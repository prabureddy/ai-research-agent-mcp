"""Configuration management for the MCP Research Engineer."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class SearchConfig(BaseModel):
    """Configuration for web search."""

    provider: str = Field(default="duckduckgo", description="Search provider to use")
    brave_api_key: Optional[str] = Field(default=None, description="Brave Search API key")
    max_results: int = Field(default=10, description="Maximum search results to return")


class RAGConfig(BaseModel):
    """Configuration for RAG system."""

    embedding_model: str = Field(
        default="voyage-2", description="Embedding model (sentence-transformers or voyage)"
    )
    vector_db_path: Path = Field(
        default=Path("./data/vector_db"), description="Path to vector database"
    )
    chunk_size: int = Field(default=1000, description="Text chunk size for indexing")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    use_local_embeddings: bool = Field(
        default=True, description="Use local sentence-transformers instead of API"
    )


class SandboxConfig(BaseModel):
    """Configuration for code execution sandbox."""

    timeout: int = Field(default=30, description="Execution timeout in seconds")
    max_memory_mb: int = Field(default=512, description="Maximum memory in MB")
    allowed_packages: list[str] = Field(
        default_factory=lambda: [
            "numpy",
            "pandas",
            "matplotlib",
            "seaborn",
            "scipy",
            "scikit-learn",
        ],
        description="Allowed Python packages",
    )


class WorkspaceConfig(BaseModel):
    """Configuration for workspace management."""

    research_runs_dir: Path = Field(
        default=Path("./research_runs"), description="Directory for research outputs"
    )
    knowledge_base_dir: Path = Field(
        default=Path("./knowledge_base"), description="Directory for knowledge base"
    )


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field(default="INFO", description="Log level")
    log_file: Path = Field(
        default=Path("./logs/research_engineer.log"), description="Log file path"
    )


class Config(BaseModel):
    """Main configuration class."""

    search: SearchConfig = Field(default_factory=SearchConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        search_config = SearchConfig(
            provider=os.getenv("SEARCH_PROVIDER", "duckduckgo"),
            brave_api_key=os.getenv("BRAVE_API_KEY"),
            max_results=int(os.getenv("MAX_SEARCH_RESULTS", "10")),
        )

        rag_config = RAGConfig(
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            vector_db_path=Path(os.getenv("VECTOR_DB_PATH", "./data/vector_db")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            use_local_embeddings=os.getenv("USE_LOCAL_EMBEDDINGS", "true").lower() == "true",
        )

        sandbox_config = SandboxConfig(
            timeout=int(os.getenv("SANDBOX_TIMEOUT", "30")),
            max_memory_mb=int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512")),
            allowed_packages=os.getenv(
                "ALLOWED_PACKAGES", "numpy,pandas,matplotlib,seaborn,scipy,scikit-learn"
            ).split(","),
        )

        workspace_config = WorkspaceConfig(
            research_runs_dir=Path(os.getenv("RESEARCH_RUNS_DIR", "./research_runs")),
            knowledge_base_dir=Path(os.getenv("KNOWLEDGE_BASE_DIR", "./knowledge_base")),
        )

        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=Path(os.getenv("LOG_FILE", "./logs/research_engineer.log")),
        )

        return cls(
            search=search_config,
            rag=rag_config,
            sandbox=sandbox_config,
            workspace=workspace_config,
            logging=logging_config,
        )


# Global configuration instance
config = Config.from_env()
