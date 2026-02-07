"""Code execution sandbox for safe Python code execution."""

import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from typing import Any, Optional
import signal
import resource

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr

from ..config import config


class TimeoutException(Exception):
    """Exception raised when code execution times out."""

    pass


def timeout_handler(signum: int, frame: Any) -> None:
    """Handle timeout signal."""
    raise TimeoutException("Code execution timed out")


class CodeSandbox:
    """Safe Python code execution sandbox."""

    def __init__(self) -> None:
        """Initialize the code sandbox."""
        self.timeout = config.sandbox.timeout
        self.max_memory_mb = config.sandbox.max_memory_mb
        self.allowed_packages = config.sandbox.allowed_packages

    def _setup_safe_globals(self) -> dict[str, Any]:
        """Set up safe global namespace for code execution."""
        # Start with RestrictedPython safe globals
        safe_env = safe_globals.copy()

        # Define print handler for RestrictedPython
        def _print(output_stream):
            """Print handler for RestrictedPython."""
            return print
        
        # Add safe built-ins
        safe_env.update(
            {
                "_getiter_": iter,
                "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
                "_print_": _print,
                "__builtins__": {
                    "True": True,
                    "False": False,
                    "None": None,
                    "abs": abs,
                    "all": all,
                    "any": any,
                    "bool": bool,
                    "dict": dict,
                    "enumerate": enumerate,
                    "float": float,
                    "int": int,
                    "len": len,
                    "list": list,
                    "max": max,
                    "min": min,
                    "range": range,
                    "round": round,
                    "set": set,
                    "sorted": sorted,
                    "str": str,
                    "sum": sum,
                    "tuple": tuple,
                    "zip": zip,
                    "print": print,
                },
                "_getattr_": safer_getattr,
            }
        )

        # Import allowed packages
        for package in self.allowed_packages:
            try:
                if package == "numpy":
                    import numpy as np

                    safe_env["np"] = np
                    safe_env["numpy"] = np
                elif package == "pandas":
                    import pandas as pd

                    safe_env["pd"] = pd
                    safe_env["pandas"] = pd
                elif package == "matplotlib":
                    import matplotlib.pyplot as plt

                    safe_env["plt"] = plt
                    safe_env["matplotlib"] = __import__("matplotlib")
                elif package == "seaborn":
                    import seaborn as sns

                    safe_env["sns"] = sns
                    safe_env["seaborn"] = sns
                elif package == "scipy":
                    import scipy

                    safe_env["scipy"] = scipy
                elif package == "scikit-learn":
                    import sklearn

                    safe_env["sklearn"] = sklearn
            except ImportError:
                pass

        return safe_env

    def _set_resource_limits(self) -> None:
        """Set resource limits for code execution."""
        try:
            # Set memory limit (in bytes)
            max_memory_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
        except (ValueError, OSError):
            # Resource limits may not be available on all platforms
            pass

    def execute(
        self, code: str, timeout: Optional[int] = None, capture_plots: bool = True
    ) -> dict[str, Any]:
        """
        Execute Python code in a safe sandbox.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (defaults to config value)
            capture_plots: Whether to capture matplotlib plots

        Returns:
            Dictionary with execution results
        """
        if timeout is None:
            timeout = self.timeout

        # Compile code with RestrictedPython
        try:
            byte_code = compile_restricted(code, "<string>", "exec")
            if byte_code is None:
                return {
                    "success": False,
                    "error": "Code compilation failed",
                    "error_type": "CompilationError",
                }
        except SyntaxError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "SyntaxError",
                "line": e.lineno,
            }

        # Set up execution environment
        safe_env = self._setup_safe_globals()
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Configure matplotlib for non-interactive backend if capturing plots
        plots = []
        if capture_plots:
            try:
                import matplotlib

                matplotlib.use("Agg")
                import matplotlib.pyplot as plt

                safe_env["plt"] = plt
            except ImportError:
                pass

        # Set timeout alarm (Unix-like systems only)
        old_handler = None
        try:
            if hasattr(signal, "SIGALRM"):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
        except (ValueError, OSError):
            pass

        # Execute code
        start_time = datetime.utcnow()
        try:
            # Set resource limits
            self._set_resource_limits()

            # Execute with captured output
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(byte_code, safe_env)

            # Capture plots if matplotlib was used
            if capture_plots and "plt" in safe_env:
                try:
                    import matplotlib.pyplot as plt

                    # Get all figure numbers
                    for fig_num in plt.get_fignums():
                        fig = plt.figure(fig_num)
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", bbox_inches="tight")
                        buf.seek(0)
                        plots.append(
                            {
                                "figure_num": fig_num,
                                "format": "png",
                                "data": buf.getvalue().hex(),
                            }
                        )
                    plt.close("all")
                except Exception:
                    pass

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "plots": plots,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat(),
            }

        except TimeoutException:
            return {
                "success": False,
                "error": f"Code execution timed out after {timeout} seconds",
                "error_type": "TimeoutError",
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
            }

        except MemoryError:
            return {
                "success": False,
                "error": f"Code execution exceeded memory limit of {self.max_memory_mb}MB",
                "error_type": "MemoryError",
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
            }

        finally:
            # Cancel alarm
            if old_handler is not None:
                try:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                except (ValueError, OSError):
                    pass

    def validate_code(self, code: str) -> dict[str, Any]:
        """
        Validate Python code without executing it.

        Args:
            code: Python code to validate

        Returns:
            Dictionary with validation results
        """
        try:
            byte_code = compile_restricted(code, "<string>", "exec")
            if byte_code is None:
                return {
                    "valid": False,
                    "error": "Code compilation failed",
                }
            return {
                "valid": True,
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "error_type": "SyntaxError",
                "line": e.lineno,
            }


# Tool instance
code_sandbox = CodeSandbox()
