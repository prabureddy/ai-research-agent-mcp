"""Main MCP server for the AI Research Engineer."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to support direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Use absolute imports that work when server directory is in path
from src.config import config
from src.tools.web_research import web_research_tool
from src.tools.rag_tool import rag_tool
from src.tools.code_sandbox import code_sandbox
from src.tools.workspace import workspace_tool
from src.tools.evaluator import evaluator_tool

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("research-engineer")

# Create MCP server
app = Server("research-engineer")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="web_search",
            description="Search the web for information using DuckDuckGo or Brave Search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="web_research",
            description="Perform comprehensive web research including search and content scraping",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Research query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum search results (default: 10)",
                        "default": 10,
                    },
                    "scrape_content": {
                        "type": "boolean",
                        "description": "Whether to scrape full content from URLs (default: true)",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="scrape_url",
            description="Scrape and extract clean content from a specific URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to scrape",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="query_knowledge_base",
            description="Query your personal knowledge base (notes, papers, documents) using semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query string",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="index_knowledge_base",
            description="Index files or directories into the knowledge base for RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory to index",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to index recursively (for directories)",
                        "default": True,
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="execute_code",
            description="Execute Python code in a safe sandbox environment with data science libraries",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Execution timeout in seconds (default: 30)",
                        "default": 30,
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="validate_code",
            description="Validate Python code without executing it",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to validate",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="create_research_run",
            description="Create a new research run directory for organizing outputs",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the research run",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata about the research",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="write_file",
            description="Write a file to a research run directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "Research run ID",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content",
                    },
                    "subdirectory": {
                        "type": "string",
                        "description": "Optional subdirectory (e.g., 'charts', 'data', 'code')",
                    },
                },
                "required": ["run_id", "filename", "content"],
            },
        ),
        Tool(
            name="read_file",
            description="Read a file from a research run directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "Research run ID",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the file",
                    },
                    "subdirectory": {
                        "type": "string",
                        "description": "Optional subdirectory",
                    },
                },
                "required": ["run_id", "filename"],
            },
        ),
        Tool(
            name="list_research_runs",
            description="List all research runs",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_run_summary",
            description="Get a summary of a research run",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "Research run ID",
                    },
                },
                "required": ["run_id"],
            },
        ),
        Tool(
            name="create_evaluation",
            description="Create a comprehensive evaluation of research output with quality metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the research task",
                    },
                    "metrics": {
                        "type": "object",
                        "description": "Quality metrics (clarity, data_grounding, completeness, code_quality, actionability, confidence)",
                        "properties": {
                            "clarity": {"type": "number", "minimum": 0, "maximum": 10},
                            "data_grounding": {"type": "number", "minimum": 0, "maximum": 10},
                            "completeness": {"type": "number", "minimum": 0, "maximum": 10},
                            "code_quality": {"type": "number", "minimum": 0, "maximum": 10},
                            "actionability": {"type": "number", "minimum": 0, "maximum": 10},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 10},
                        },
                    },
                    "strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of strengths",
                    },
                    "weaknesses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of weaknesses",
                    },
                    "next_time_improvements": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Improvements for next time",
                    },
                    "data_sources_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Data sources used",
                    },
                    "tools_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tools used",
                    },
                },
                "required": [
                    "task_description",
                    "metrics",
                    "strengths",
                    "weaknesses",
                    "next_time_improvements",
                    "data_sources_used",
                    "tools_used",
                ],
            },
        ),
        Tool(
            name="evaluate_code_quality",
            description="Evaluate the quality of generated code",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to evaluate",
                    },
                    "execution_result": {
                        "type": "object",
                        "description": "Result from code execution",
                    },
                },
                "required": ["code", "execution_result"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        # Web research tools
        if name == "web_search":
            result = await web_research_tool.search(
                query=arguments["query"],
                max_results=arguments.get("max_results"),
            )
        elif name == "web_research":
            result = await web_research_tool.research(
                query=arguments["query"],
                max_results=arguments.get("max_results"),
                scrape_content=arguments.get("scrape_content", True),
            )
        elif name == "scrape_url":
            result = await web_research_tool.scrape_url(url=arguments["url"])

        # RAG tools
        elif name == "query_knowledge_base":
            result = rag_tool.query(
                query=arguments["query"],
                n_results=arguments.get("n_results", 5),
            )
        elif name == "index_knowledge_base":
            from pathlib import Path

            path = Path(arguments["path"])
            if path.is_file():
                result = rag_tool.index_file(path)
            else:
                result = rag_tool.index_directory(
                    path, recursive=arguments.get("recursive", True)
                )

        # Code execution tools
        elif name == "execute_code":
            result = code_sandbox.execute(
                code=arguments["code"],
                timeout=arguments.get("timeout"),
            )
        elif name == "validate_code":
            result = code_sandbox.validate_code(code=arguments["code"])

        # Workspace tools
        elif name == "create_research_run":
            result = workspace_tool.create_research_run(
                name=arguments["name"],
                metadata=arguments.get("metadata"),
            )
        elif name == "write_file":
            result = workspace_tool.write_file(
                run_id=arguments["run_id"],
                filename=arguments["filename"],
                content=arguments["content"],
                subdirectory=arguments.get("subdirectory"),
            )
        elif name == "read_file":
            result = workspace_tool.read_file(
                run_id=arguments["run_id"],
                filename=arguments["filename"],
                subdirectory=arguments.get("subdirectory"),
            )
        elif name == "list_research_runs":
            result = workspace_tool.list_research_runs()
        elif name == "get_run_summary":
            result = workspace_tool.get_run_summary(run_id=arguments["run_id"])

        # Evaluation tools
        elif name == "create_evaluation":
            result = evaluator_tool.create_evaluation(
                task_description=arguments["task_description"],
                metrics=arguments["metrics"],
                strengths=arguments["strengths"],
                weaknesses=arguments["weaknesses"],
                next_time_improvements=arguments["next_time_improvements"],
                data_sources_used=arguments["data_sources_used"],
                tools_used=arguments["tools_used"],
                execution_time_seconds=arguments.get("execution_time_seconds"),
            )
        elif name == "evaluate_code_quality":
            result = evaluator_tool.evaluate_code_quality(
                code=arguments["code"],
                execution_result=arguments["execution_result"],
            )

        else:
            result = {"error": f"Unknown tool: {name}"}

        logger.info(f"Tool {name} completed successfully")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
        error_result = {"error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main() -> None:
    """Run the MCP server."""
    logger.info("Starting MCP Research Engineer server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
