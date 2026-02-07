"""Evaluation and self-critique tool for research quality assessment."""

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class QualityMetrics(BaseModel):
    """Quality metrics for research output."""

    clarity: float = Field(ge=0.0, le=10.0, description="Clarity of explanation (0-10)")
    data_grounding: float = Field(
        ge=0.0, le=10.0, description="How well grounded in data (0-10)"
    )
    completeness: float = Field(ge=0.0, le=10.0, description="Completeness of analysis (0-10)")
    code_quality: float = Field(ge=0.0, le=10.0, description="Quality of code (0-10)")
    actionability: float = Field(
        ge=0.0, le=10.0, description="How actionable the insights are (0-10)"
    )
    confidence: float = Field(ge=0.0, le=10.0, description="Confidence in results (0-10)")

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score."""
        return (
            self.clarity
            + self.data_grounding
            + self.completeness
            + self.code_quality
            + self.actionability
            + self.confidence
        ) / 6.0


class ResearchEvaluation(BaseModel):
    """Complete evaluation of a research task."""

    task_description: str
    metrics: QualityMetrics
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_time_improvements: list[str] = Field(default_factory=list)
    data_sources_used: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    execution_time_seconds: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EvaluatorTool:
    """Tool for evaluating and critiquing research outputs."""

    def __init__(self) -> None:
        """Initialize the evaluator tool."""
        pass

    def create_evaluation(
        self,
        task_description: str,
        metrics: dict[str, float],
        strengths: list[str],
        weaknesses: list[str],
        next_time_improvements: list[str],
        data_sources_used: list[str],
        tools_used: list[str],
        execution_time_seconds: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Create a comprehensive evaluation of a research task.

        Args:
            task_description: Description of the research task
            metrics: Dictionary of quality metrics (clarity, data_grounding, etc.)
            strengths: List of strengths in the research
            weaknesses: List of weaknesses or limitations
            next_time_improvements: List of improvements for next time
            data_sources_used: List of data sources used
            tools_used: List of tools used
            execution_time_seconds: Total execution time

        Returns:
            Dictionary with evaluation results
        """
        try:
            quality_metrics = QualityMetrics(**metrics)

            evaluation = ResearchEvaluation(
                task_description=task_description,
                metrics=quality_metrics,
                strengths=strengths,
                weaknesses=weaknesses,
                next_time_improvements=next_time_improvements,
                data_sources_used=data_sources_used,
                tools_used=tools_used,
                execution_time_seconds=execution_time_seconds,
            )

            return {
                "success": True,
                "evaluation": evaluation.model_dump(),
                "overall_score": quality_metrics.overall_score,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def evaluate_code_quality(self, code: str, execution_result: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate the quality of generated code.

        Args:
            code: The code to evaluate
            execution_result: Result from code execution

        Returns:
            Dictionary with code quality assessment
        """
        issues = []
        score = 10.0

        # Check if code executed successfully
        if not execution_result.get("success"):
            issues.append("Code failed to execute")
            score -= 5.0

        # Check for output
        if not execution_result.get("stdout") and not execution_result.get("plots"):
            issues.append("Code produced no output or visualizations")
            score -= 2.0

        # Check code length (very short might be incomplete)
        if len(code.strip()) < 50:
            issues.append("Code is very short, might be incomplete")
            score -= 1.0

        # Check for common patterns
        if "import" not in code:
            issues.append("No imports found, might be missing dependencies")
            score -= 1.0

        # Check for documentation
        if "#" not in code and '"""' not in code:
            issues.append("No comments or documentation")
            score -= 1.0

        score = max(0.0, score)

        return {
            "score": score,
            "issues": issues,
            "has_output": bool(execution_result.get("stdout") or execution_result.get("plots")),
            "executed_successfully": execution_result.get("success", False),
        }

    def evaluate_research_completeness(
        self, task: str, search_results: int, scraped_pages: int, rag_queries: int, code_runs: int
    ) -> dict[str, Any]:
        """
        Evaluate the completeness of research process.

        Args:
            task: The research task
            search_results: Number of search results obtained
            scraped_pages: Number of pages scraped
            rag_queries: Number of RAG queries made
            code_runs: Number of code executions

        Returns:
            Dictionary with completeness assessment
        """
        score = 0.0
        feedback = []

        # Check search coverage
        if search_results >= 5:
            score += 2.5
            feedback.append("Good search coverage")
        elif search_results > 0:
            score += 1.0
            feedback.append("Limited search coverage")
        else:
            feedback.append("No web search performed")

        # Check content extraction
        if scraped_pages >= 3:
            score += 2.5
            feedback.append("Good content extraction")
        elif scraped_pages > 0:
            score += 1.0
            feedback.append("Limited content extraction")
        else:
            feedback.append("No content scraped")

        # Check knowledge base usage
        if rag_queries >= 2:
            score += 2.5
            feedback.append("Good use of knowledge base")
        elif rag_queries > 0:
            score += 1.0
            feedback.append("Limited knowledge base usage")
        else:
            feedback.append("Knowledge base not consulted")

        # Check code execution
        if code_runs >= 1:
            score += 2.5
            feedback.append("Code execution performed")
        else:
            feedback.append("No code execution")

        return {
            "score": score,
            "max_score": 10.0,
            "feedback": feedback,
            "search_results": search_results,
            "scraped_pages": scraped_pages,
            "rag_queries": rag_queries,
            "code_runs": code_runs,
        }

    def generate_self_critique_prompt(self, task: str, output: str) -> str:
        """
        Generate a prompt for LLM self-critique.

        Args:
            task: The research task
            output: The generated output

        Returns:
            Prompt string for self-critique
        """
        return f"""You have completed the following research task:

TASK: {task}

YOUR OUTPUT:
{output}

Please provide a self-critique of your work by evaluating:

1. CLARITY (0-10): How clear and well-structured is the output?
2. DATA GROUNDING (0-10): How well is the analysis grounded in actual data?
3. COMPLETENESS (0-10): How complete is the analysis?
4. CODE QUALITY (0-10): If code was written, how good is it?
5. ACTIONABILITY (0-10): How actionable are the insights?
6. CONFIDENCE (0-10): How confident are you in the results?

Also provide:
- STRENGTHS: List 2-3 key strengths of your work
- WEAKNESSES: List 2-3 limitations or weaknesses
- NEXT TIME: List 2-3 things you would do differently next time

Format your response as JSON with the following structure:
{{
  "metrics": {{
    "clarity": <score>,
    "data_grounding": <score>,
    "completeness": <score>,
    "code_quality": <score>,
    "actionability": <score>,
    "confidence": <score>
  }},
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "next_time_improvements": ["improvement1", "improvement2", "improvement3"]
}}
"""

    def save_evaluation(self, evaluation: dict[str, Any], file_path: str) -> dict[str, Any]:
        """
        Save evaluation to a JSON file.

        Args:
            evaluation: Evaluation dictionary
            file_path: Path to save the evaluation

        Returns:
            Dictionary with save result
        """
        try:
            with open(file_path, "w") as f:
                json.dump(evaluation, f, indent=2)

            return {
                "success": True,
                "file_path": file_path,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Tool instance
evaluator_tool = EvaluatorTool()
