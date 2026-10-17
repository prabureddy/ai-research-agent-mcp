# Optional Parallel Search MCP companion

Add [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
alongside `research-engineer` in Claude Desktop to gather current web sources
and read pages before combining them with your notes, code, and reports.
It provides `web_search` and `web_fetch`, with no Parallel account or API key
required for free, light use. Anonymous searches use Fast mode.

This is a separate MCP server selected by Claude Desktop. The Python server's
`web_search` and `web_research` tools still use your existing `SEARCH_PROVIDER`
choice (DuckDuckGo by default); `SEARCH_PROVIDER=parallel` is not supported.

## Setup in Claude Desktop

1. Complete the [research-engineer setup](../README.md) first.
2. Install [Node.js](https://nodejs.org/en/download) 22 LTS or newer, including
   `npx`. Check `node --version` and `npx --version` in a terminal. Claude Desktop
   must also be able to find `npx`; if necessary, use its absolute path as the
   `command` below (`where npx` on Windows, `command -v npx` on macOS/Linux).
3. Open **Settings → Developer → Edit Config**. Merge the `parallel-search`
   entry below into your existing `mcpServers` object, keeping your configured
   `research-engineer` entry and any other servers. This snippet shows only the
   new entry, not a replacement for your full configuration.

```json
{
  "mcpServers": {
    "parallel-search": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@0.15.1",
        "https://search.parallel.ai/mcp",
        "--transport",
        "http-only",
        "--header",
        "User-Agent:ai-research-agent-mcp/0.1.0"
      ]
    }
  }
}
```

The pinned [`mcp-remote`](https://github.com/geelen/mcp-remote) bridge connects
Claude Desktop's local stdio transport to Parallel's remote HTTP endpoint.
The first start downloads the npm package and requires internet access. No
`Authorization` header or extra Python dependency is needed for this setup.

4. Fully quit and reopen Claude Desktop. Confirm that `parallel-search` exposes
   `web_search` and `web_fetch` in the available tools. Both servers have a tool
   named `web_search`, so check the server name when selecting or approving it.

## Try a research task

With both servers enabled, try:

```text
Research Python asyncio task cancellation using current official documentation.
Use web_search from the parallel-search server to find relevant sources, then
web_fetch from that server to read the selected pages. Cite the source URLs.
Compare the findings with any relevant notes using research-engineer's
query_knowledge_base. Use its create_research_run and write_file tools to save
a report.md containing the findings, citations, and any gaps in the evidence.
```

Parallel's `web_search` takes an `objective` and a nonempty `search_queries` list;
`web_fetch` takes a `urls` list. These differ from the local server's search
arguments. Claude Desktop discovers the schemas from each server. Fetch the
selected URLs to read beyond search excerpts before drawing conclusions.

## Troubleshooting and removal

- If `parallel-search` fails to start, check the `npx` path, Node.js version, and
  internet access, then fully restart Claude Desktop. Ensure the merged file is
  valid JSON, with a comma between adjacent server entries and no trailing comma.
- Anonymous access has rate limits. If a tool reports a limit, wait as directed
  by the response. See the [Parallel setup guide](https://docs.parallel.ai/integrations/mcp/search-mcp)
  for authenticated access and higher limits.
- Adding this companion does not route local `web_research` calls through
  Parallel. Ask explicitly for the tools from `parallel-search` when needed.
- To remove it, delete only the `parallel-search` entry from `mcpServers` and
  restart Claude Desktop. Keep the existing `research-engineer` configuration.
