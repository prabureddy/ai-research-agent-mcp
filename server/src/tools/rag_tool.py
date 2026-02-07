"""Vector RAG tool for querying personal knowledge base."""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from docx import Document

from ..config import config


class RAGTool:
    """Tool for vector-based retrieval over personal knowledge base."""

    def __init__(self) -> None:
        """Initialize the RAG tool."""
        self.embedding_model = config.rag.embedding_model
        self.vector_db_path = config.rag.vector_db_path
        self.chunk_size = config.rag.chunk_size
        self.chunk_overlap = config.rag.chunk_overlap
        self.use_local_embeddings = config.rag.use_local_embeddings
        
        # Lazy initialization flags
        self._initialized = False
        self.sentence_model = None
        self.chroma_client = None
        self.collection = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of embedding model and database."""
        if self._initialized:
            return
            
        # Initialize embedding model (local sentence-transformers)
        if self.use_local_embeddings:
            self.sentence_model = SentenceTransformer(self.embedding_model)
        else:
            # TODO: Add Anthropic embeddings support
            raise NotImplementedError(
                "Anthropic embeddings not yet implemented. "
                "Please set USE_LOCAL_EMBEDDINGS=true to use local embeddings."
            )

        # Initialize ChromaDB
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Personal knowledge base for research"},
        )
        
        self._initialized = True

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using sentence-transformers."""
        if not self.sentence_model:
            raise ValueError("Embedding model not initialized")

        # Generate embedding using sentence-transformers
        embedding = self.sentence_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    chunk = chunk[: break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        reader = PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        doc = Document(str(file_path))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from various file formats."""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._extract_text_from_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            return self._extract_text_from_docx(file_path)
        elif suffix in [".txt", ".md"]:
            return file_path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def index_file(self, file_path: Path, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Index a file into the knowledge base.

        Args:
            file_path: Path to the file to index
            metadata: Optional metadata to attach to the document

        Returns:
            Dictionary with indexing results
        """
        self._ensure_initialized()
        try:
            # Extract text
            text = self._extract_text_from_file(file_path)

            # Chunk text
            chunks = self._chunk_text(text)

            # Generate IDs for chunks
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
            chunk_ids = [f"{file_hash}_{i}" for i in range(len(chunks))]

            # Prepare metadata
            base_metadata = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": file_path.suffix,
                **(metadata or {}),
            }

            chunk_metadata = [
                {**base_metadata, "chunk_index": i} for i in range(len(chunks))
            ]

            # Get embeddings
            embeddings = [self._get_embedding(chunk) for chunk in chunks]

            # Add to collection
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=chunk_metadata,
            )

            return {
                "success": True,
                "file_path": str(file_path),
                "chunks_indexed": len(chunks),
                "total_characters": len(text),
            }

        except Exception as e:
            return {
                "success": False,
                "file_path": str(file_path),
                "error": str(e),
            }

    def index_directory(
        self, directory: Path, recursive: bool = True, file_patterns: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Index all files in a directory.

        Args:
            directory: Directory to index
            recursive: Whether to index recursively
            file_patterns: List of file patterns to match (e.g., ['*.md', '*.pdf'])

        Returns:
            Dictionary with indexing results
        """
        if file_patterns is None:
            file_patterns = ["*.md", "*.txt", "*.pdf", "*.docx"]

        files_to_index = []
        for pattern in file_patterns:
            if recursive:
                files_to_index.extend(directory.rglob(pattern))
            else:
                files_to_index.extend(directory.glob(pattern))

        results = []
        for file_path in files_to_index:
            result = self.index_file(file_path)
            results.append(result)

        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful

        return {
            "directory": str(directory),
            "total_files": len(results),
            "successful": successful,
            "failed": failed,
            "results": results,
        }

    def query(
        self, query: str, n_results: int = 5, filter_metadata: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Query the knowledge base.

        Args:
            query: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            Dictionary with query results
        """
        self._ensure_initialized()
        if not self.sentence_model:
            raise ValueError("Embedding model not initialized")

        # Get query embedding
        query_embedding = self._get_embedding(query)

        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
        )

        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results.get("distances") else None,
                    }
                )

        return {
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
        }

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the knowledge base."""
        self._ensure_initialized()
        count = self.collection.count()

        return {
            "total_chunks": count,
            "collection_name": self.collection.name,
            "embedding_model": self.embedding_model,
        }


# Tool instance
rag_tool = RAGTool()
