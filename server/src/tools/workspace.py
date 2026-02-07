"""Workspace management tool for organizing research outputs."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..config import config


class WorkspaceTool:
    """Tool for managing research workspace and files."""

    def __init__(self) -> None:
        """Initialize the workspace tool."""
        self.research_runs_dir = config.workspace.research_runs_dir
        self.research_runs_dir.mkdir(parents=True, exist_ok=True)

    def create_research_run(self, name: str, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Create a new research run directory.

        Args:
            name: Name of the research run
            metadata: Optional metadata about the research run

        Returns:
            Dictionary with research run information
        """
        # Create timestamped directory name
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
        dir_name = f"{timestamp}_{safe_name}"
        run_dir = self.research_runs_dir / dir_name

        # Create directory structure
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "charts").mkdir(exist_ok=True)
        (run_dir / "data").mkdir(exist_ok=True)
        (run_dir / "code").mkdir(exist_ok=True)

        # Save metadata
        metadata_dict = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "directory": str(run_dir),
            **(metadata or {}),
        }

        with open(run_dir / "metadata.json", "w") as f:
            json.dump(metadata_dict, f, indent=2)

        return {
            "success": True,
            "run_id": dir_name,
            "directory": str(run_dir),
            "metadata": metadata_dict,
        }

    def write_file(
        self, run_id: str, filename: str, content: str, subdirectory: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Write a file to a research run directory.

        Args:
            run_id: Research run ID
            filename: Name of the file
            content: File content
            subdirectory: Optional subdirectory (e.g., 'charts', 'data', 'code')

        Returns:
            Dictionary with file information
        """
        run_dir = self.research_runs_dir / run_id

        if not run_dir.exists():
            return {
                "success": False,
                "error": f"Research run '{run_id}' not found",
            }

        # Determine file path
        if subdirectory:
            file_dir = run_dir / subdirectory
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
        else:
            file_path = run_dir / filename

        # Write file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "file_path": str(file_path),
                "size_bytes": len(content.encode("utf-8")),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def write_binary_file(
        self, run_id: str, filename: str, data: bytes, subdirectory: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Write a binary file to a research run directory.

        Args:
            run_id: Research run ID
            filename: Name of the file
            data: Binary data
            subdirectory: Optional subdirectory

        Returns:
            Dictionary with file information
        """
        run_dir = self.research_runs_dir / run_id

        if not run_dir.exists():
            return {
                "success": False,
                "error": f"Research run '{run_id}' not found",
            }

        # Determine file path
        if subdirectory:
            file_dir = run_dir / subdirectory
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / filename
        else:
            file_path = run_dir / filename

        # Write file
        try:
            with open(file_path, "wb") as f:
                f.write(data)

            return {
                "success": True,
                "file_path": str(file_path),
                "size_bytes": len(data),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def read_file(self, run_id: str, filename: str, subdirectory: Optional[str] = None) -> dict[str, Any]:
        """
        Read a file from a research run directory.

        Args:
            run_id: Research run ID
            filename: Name of the file
            subdirectory: Optional subdirectory

        Returns:
            Dictionary with file content
        """
        run_dir = self.research_runs_dir / run_id

        if not run_dir.exists():
            return {
                "success": False,
                "error": f"Research run '{run_id}' not found",
            }

        # Determine file path
        if subdirectory:
            file_path = run_dir / subdirectory / filename
        else:
            file_path = run_dir / filename

        if not file_path.exists():
            return {
                "success": False,
                "error": f"File '{filename}' not found",
            }

        # Read file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "success": True,
                "content": content,
                "file_path": str(file_path),
                "size_bytes": len(content.encode("utf-8")),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def list_files(self, run_id: str, subdirectory: Optional[str] = None) -> dict[str, Any]:
        """
        List files in a research run directory.

        Args:
            run_id: Research run ID
            subdirectory: Optional subdirectory

        Returns:
            Dictionary with file list
        """
        run_dir = self.research_runs_dir / run_id

        if not run_dir.exists():
            return {
                "success": False,
                "error": f"Research run '{run_id}' not found",
            }

        # Determine directory to list
        if subdirectory:
            list_dir = run_dir / subdirectory
        else:
            list_dir = run_dir

        if not list_dir.exists():
            return {
                "success": False,
                "error": f"Directory not found",
            }

        # List files
        try:
            files = []
            for item in list_dir.iterdir():
                if item.is_file():
                    files.append(
                        {
                            "name": item.name,
                            "size_bytes": item.stat().st_size,
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        }
                    )

            return {
                "success": True,
                "files": files,
                "total_files": len(files),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def list_research_runs(self) -> dict[str, Any]:
        """
        List all research runs.

        Returns:
            Dictionary with research run list
        """
        try:
            runs = []
            for run_dir in self.research_runs_dir.iterdir():
                if run_dir.is_dir():
                    metadata_file = run_dir / "metadata.json"
                    metadata = {}

                    if metadata_file.exists():
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)

                    runs.append(
                        {
                            "run_id": run_dir.name,
                            "directory": str(run_dir),
                            "created_at": metadata.get("created_at", ""),
                            "name": metadata.get("name", ""),
                        }
                    )

            # Sort by creation time (newest first)
            runs.sort(key=lambda x: x["created_at"], reverse=True)

            return {
                "success": True,
                "runs": runs,
                "total_runs": len(runs),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def delete_research_run(self, run_id: str) -> dict[str, Any]:
        """
        Delete a research run directory.

        Args:
            run_id: Research run ID

        Returns:
            Dictionary with deletion result
        """
        run_dir = self.research_runs_dir / run_id

        if not run_dir.exists():
            return {
                "success": False,
                "error": f"Research run '{run_id}' not found",
            }

        try:
            shutil.rmtree(run_dir)
            return {
                "success": True,
                "run_id": run_id,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_run_summary(self, run_id: str) -> dict[str, Any]:
        """
        Get a summary of a research run.

        Args:
            run_id: Research run ID

        Returns:
            Dictionary with run summary
        """
        run_dir = self.research_runs_dir / run_id

        if not run_dir.exists():
            return {
                "success": False,
                "error": f"Research run '{run_id}' not found",
            }

        try:
            # Load metadata
            metadata_file = run_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

            # Count files in subdirectories
            file_counts = {}
            for subdir in ["charts", "data", "code"]:
                subdir_path = run_dir / subdir
                if subdir_path.exists():
                    file_counts[subdir] = len(list(subdir_path.glob("*")))
                else:
                    file_counts[subdir] = 0

            # Check for key files
            has_report = (run_dir / "report.md").exists()
            has_evaluation = (run_dir / "evaluation.json").exists()

            return {
                "success": True,
                "run_id": run_id,
                "metadata": metadata,
                "file_counts": file_counts,
                "has_report": has_report,
                "has_evaluation": has_evaluation,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Tool instance
workspace_tool = WorkspaceTool()
