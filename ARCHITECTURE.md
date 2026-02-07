# Architecture Documentation

Technical architecture and design decisions for the MCP-Powered AI Research Engineer.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Desktop / Cursor                   │
│                     (MCP Client/Host)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol (stdio)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    MCP Server (Python)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Tool Registry & Router                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Web Research │  │   RAG Tool   │  │Code Sandbox  │     │
│  │              │  │              │  │              │     │
│  │ • Search     │  │ • Embeddings │  │ • Restricted │     │
│  │ • Scrape     │  │ • ChromaDB   │  │   Python     │     │
│  │ • Extract    │  │ • Query      │  │ • Safe Exec  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  Workspace   │  │  Evaluator   │                        │
│  │              │  │              │                        │
│  │ • File I/O   │  │ • Metrics    │                        │
│  │ • Organize   │  │ • Critique   │                        │
│  │ • Manage     │  │ • Quality    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      External Services              │
        │                                     │
        │  • DuckDuckGo / Brave Search       │
        │  • OpenAI Embeddings API           │
        │  • Web Scraping (HTTP)             │
        └────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      Local Storage                  │
        │                                     │
        │  • research_runs/                  │
        │  • knowledge_base/                 │
        │  • data/vector_db/                 │
        │  • logs/                           │
        └────────────────────────────────────┘
```

## Core Components

### 1. MCP Server ([`server/src/server.py`](server/src/server.py))

**Responsibilities:**
- Expose tools via MCP protocol
- Route tool calls to appropriate handlers
- Handle errors and logging
- Manage server lifecycle

**Key Functions:**
- `list_tools()`: Returns available tools with schemas
- `call_tool()`: Routes tool invocations to handlers
- `main()`: Server entry point with stdio transport

**Technology:**
- Python 3.10+
- MCP SDK (`mcp` package)
- Async/await for I/O operations

### 2. Web Research Tool ([`server/src/tools/web_research.py`](server/src/tools/web_research.py))

**Responsibilities:**
- Search the web for information
- Scrape and extract clean content
- Handle rate limiting and retries

**Components:**
- **Search Providers:**
  - DuckDuckGo (default, no API key)
  - Brave Search (optional, requires API key)
- **Content Extraction:**
  - Trafilatura for main content
  - BeautifulSoup for metadata
  - httpx for async HTTP

**Design Decisions:**
- Async operations for parallel scraping
- Retry logic with exponential backoff
- Clean text extraction (no ads/navigation)
- Metadata preservation (title, description, URL)

### 3. RAG Tool ([`server/src/tools/rag_tool.py`](server/src/tools/rag_tool.py))

**Responsibilities:**
- Index documents into vector database
- Semantic search over knowledge base
- Support multiple file formats

**Components:**
- **Vector Database:** ChromaDB (persistent, local)
- **Embeddings:** OpenAI `text-embedding-3-small`
- **File Parsers:**
  - Markdown/Text: Direct read
  - PDF: pypdf
  - DOCX: python-docx

**Design Decisions:**
- Chunking strategy: 1000 chars with 200 char overlap
- Sentence-boundary aware splitting
- Metadata tracking (file path, type, chunk index)
- Persistent storage for reuse across sessions

**Indexing Flow:**
```
File → Extract Text → Chunk → Generate Embeddings → Store in ChromaDB
```

**Query Flow:**
```
Query → Generate Embedding → Vector Search → Return Top-K Results
```

### 4. Code Sandbox ([`server/src/tools/code_sandbox.py`](server/src/tools/code_sandbox.py))

**Responsibilities:**
- Execute Python code safely
- Capture output and plots
- Enforce resource limits

**Security Layers:**
1. **RestrictedPython:** AST-level code restrictions
2. **Resource Limits:** Memory and CPU constraints
3. **Timeout:** Execution time limits
4. **Allowed Packages:** Whitelist of safe libraries

**Allowed Libraries:**
- numpy, pandas (data manipulation)
- matplotlib, seaborn (visualization)
- scipy, scikit-learn (scientific computing)

**Design Decisions:**
- Non-interactive matplotlib backend (Agg)
- Plot capture as PNG bytes (hex-encoded)
- Separate stdout/stderr capture
- Graceful error handling with traceback

**Execution Flow:**
```
Code → Compile (RestrictedPython) → Set Limits → Execute → Capture Output
```

### 5. Workspace Tool ([`server/src/tools/workspace.py`](server/src/tools/workspace.py))

**Responsibilities:**
- Organize research outputs
- Manage file I/O
- Track research runs

**Directory Structure:**
```
research_runs/
└── YYYY-MM-DD_HHMMSS_task-name/
    ├── metadata.json
    ├── report.md
    ├── evaluation.json
    ├── sources.json
    ├── code/
    │   └── *.py
    ├── charts/
    │   └── *.png
    └── data/
        └── *.json
```

**Design Decisions:**
- Timestamped directories for uniqueness
- Structured subdirectories (code, charts, data)
- Metadata tracking (creation time, task name)
- JSON for structured data

### 6. Evaluator Tool ([`server/src/tools/evaluator.py`](server/src/tools/evaluator.py))

**Responsibilities:**
- Quality assessment
- Self-critique generation
- Metrics tracking

**Quality Metrics (0-10 scale):**
- **Clarity:** How clear and well-structured
- **Data Grounding:** How well backed by data
- **Completeness:** How thorough the analysis
- **Code Quality:** Quality of generated code
- **Actionability:** How actionable the insights
- **Confidence:** Confidence in results

**Design Decisions:**
- Pydantic models for validation
- Overall score as average of metrics
- Structured feedback (strengths, weaknesses, improvements)
- Tool usage tracking

## Configuration Management

### Environment Variables ([`.env`](.env.example))

```
BRAVE_API_KEY=...           # Optional: Better search
OPENAI_API_KEY=...          # Required: RAG embeddings
SEARCH_PROVIDER=duckduckgo  # duckduckgo or brave
MAX_SEARCH_RESULTS=10
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DB_PATH=./data/vector_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SANDBOX_TIMEOUT=30
SANDBOX_MAX_MEMORY_MB=512
RESEARCH_RUNS_DIR=./research_runs
KNOWLEDGE_BASE_DIR=./knowledge_base
LOG_LEVEL=INFO
```

### Config Module ([`server/src/config.py`](server/src/config.py))

- Pydantic models for type safety
- Environment variable loading
- Default values
- Validation

## Data Flow

### Typical Research Task Flow

```
1. User Input (Claude Desktop)
   ↓
2. MCP Server receives task
   ↓
3. Agent Planning (LLM decides tool sequence)
   ↓
4. Tool Execution:
   a. web_research → Search + Scrape
   b. query_knowledge_base → RAG query
   c. execute_code → Build model
   d. create_research_run → Setup workspace
   e. write_file → Save outputs
   f. create_evaluation → Self-assess
   ↓
5. Results returned to user
```

### Example: Real Estate Analysis

```
Task: "Analyze multifamily real estate in 2026"

1. web_research("multifamily real estate 2026 cap rates")
   → Returns: 10 search results + scraped content

2. query_knowledge_base("real estate investment metrics")
   → Returns: Relevant chunks from personal notes

3. execute_code("""
   # Build cash-flow model
   import numpy as np
   import pandas as pd
   ...
   """)
   → Returns: Execution results + plots

4. create_research_run("multifamily-analysis-2026")
   → Returns: run_id

5. write_file(run_id, "report.md", report_content)
   → Saves report

6. write_file(run_id, "model.py", code, "code")
   → Saves code

7. create_evaluation(...)
   → Returns: Quality metrics
```

## Security Considerations

### Code Execution Sandbox

**Threats Mitigated:**
- Arbitrary file system access
- Network access
- Infinite loops
- Memory exhaustion
- Malicious imports

**Mechanisms:**
- RestrictedPython compilation
- Resource limits (memory, CPU)
- Timeout enforcement
- Whitelist of allowed packages
- No file I/O in sandbox

**Limitations:**
- Not suitable for untrusted code
- Platform-dependent resource limits
- Some packages may have vulnerabilities

### API Key Management

- Environment variables (not hardcoded)
- `.env` file (gitignored)
- No keys in logs
- Optional keys for degraded functionality

### File System Access

- Restricted to configured directories
- No path traversal
- Sanitized filenames
- Metadata validation

## Performance Considerations

### Async Operations

- Web scraping: Parallel requests
- Multiple search results scraped concurrently
- Non-blocking I/O

### Caching

- Vector database persists across sessions
- No need to re-index unchanged documents
- ChromaDB handles internal caching

### Resource Limits

- Code execution timeout: 30s default
- Memory limit: 512MB default
- Search results: 10 default (configurable)

## Error Handling

### Retry Logic

- Web requests: 3 attempts with exponential backoff
- Transient failures handled gracefully
- Permanent failures reported clearly

### Graceful Degradation

- Missing API keys → Use fallback providers
- Failed scraping → Return search results only
- Code execution errors → Return error details

### Logging

- Structured logging with levels
- Tool invocation tracking
- Error details with context
- Performance metrics

## Extension Points

### Adding New Tools

1. Create tool module in `server/src/tools/`
2. Implement tool class with methods
3. Add tool to `server/src/server.py`:
   - Add to `list_tools()`
   - Add handler in `call_tool()`
4. Update documentation

### Adding Search Providers

1. Implement search method in `WebResearchTool`
2. Add provider configuration
3. Update environment variables
4. Add to provider selection logic

### Adding File Formats

1. Implement parser in `RAGTool`
2. Add to `_extract_text_from_file()`
3. Update file pattern matching
4. Test with sample files

## Testing Strategy

### Unit Tests

- Individual tool methods
- Configuration loading
- Error handling
- Edge cases

### Integration Tests

- Tool interactions
- MCP protocol compliance
- End-to-end workflows
- External API mocking

### Manual Testing

- Real research tasks
- Claude Desktop integration
- Performance under load
- Error recovery

## Deployment

### Local Development

```bash
python server/src/server.py
```

### Production Considerations

- Virtual environment isolation
- Dependency pinning
- Log rotation
- Resource monitoring
- API rate limiting
- Backup of vector database

## Future Enhancements

### Potential Improvements

1. **Multi-modal Support:**
   - Image analysis
   - PDF table extraction
   - Chart understanding

2. **Advanced RAG:**
   - Hybrid search (keyword + semantic)
   - Re-ranking
   - Query expansion
   - Citation tracking

3. **Code Execution:**
   - Support for other languages (R, Julia)
   - GPU access for ML
   - Package installation
   - Persistent environments

4. **Collaboration:**
   - Shared knowledge bases
   - Research run templates
   - Team workspaces

5. **Monitoring:**
   - Usage analytics
   - Cost tracking
   - Performance metrics
   - Quality trends

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [RestrictedPython Documentation](https://restrictedpython.readthedocs.io/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
