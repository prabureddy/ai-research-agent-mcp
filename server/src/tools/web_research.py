"""Web research tool for searching and scraping content."""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

import httpx
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from trafilatura import extract
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import config


class WebResearchTool:
    """Tool for web research including search and content extraction."""

    def __init__(self) -> None:
        """Initialize the web research tool."""
        self.search_provider = config.search.provider
        self.max_results = config.search.max_results
        self.brave_api_key = config.search.brave_api_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_duckduckgo(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Search using DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = []
                for result in ddgs.text(query, max_results=max_results):
                    results.append(
                        {
                            "title": result.get("title", ""),
                            "url": result.get("href", ""),
                            "snippet": result.get("body", ""),
                            "source": "duckduckgo",
                        }
                    )
                return results
        except Exception as e:
            raise Exception(f"DuckDuckGo search failed: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_brave(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Search using Brave Search API."""
        if not self.brave_api_key:
            raise ValueError("Brave API key not configured")

        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": self.brave_api_key}
        params = {"q": query, "count": max_results}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", ""),
                        "source": "brave",
                    }
                )
            return results

    async def search(
        self, query: str, max_results: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """
        Search the web for information.

        Args:
            query: Search query string
            max_results: Maximum number of results (defaults to config value)

        Returns:
            List of search results with title, url, snippet, and source
        """
        if max_results is None:
            max_results = self.max_results

        if self.search_provider == "brave":
            return await self.search_brave(query, max_results)
        else:
            return await self.search_duckduckgo(query, max_results)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def scrape_url(self, url: str) -> dict[str, Any]:
        """
        Scrape and extract clean content from a URL.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with extracted content and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

            # Extract main content using trafilatura
            extracted_text = extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )

            # Also parse with BeautifulSoup for metadata
            soup = BeautifulSoup(html, "html.parser")

            # Extract metadata
            title = ""
            if soup.title:
                title = soup.title.string or ""
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)

            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"]

            return {
                "url": url,
                "title": title,
                "description": description,
                "content": extracted_text or "",
                "content_length": len(extracted_text or ""),
                "scraped_at": datetime.utcnow().isoformat(),
                "success": True,
            }

        except Exception as e:
            return {
                "url": url,
                "title": "",
                "description": "",
                "content": "",
                "content_length": 0,
                "scraped_at": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e),
            }

    async def research(
        self, query: str, max_results: Optional[int] = None, scrape_content: bool = True
    ) -> dict[str, Any]:
        """
        Perform comprehensive web research on a query.

        Args:
            query: Research query
            max_results: Maximum search results
            scrape_content: Whether to scrape full content from URLs

        Returns:
            Dictionary with search results and scraped content
        """
        # Search for results
        search_results = await self.search(query, max_results)

        # Optionally scrape content from URLs
        scraped_content = []
        if scrape_content:
            scrape_tasks = [self.scrape_url(result["url"]) for result in search_results]
            scraped_content = await asyncio.gather(*scrape_tasks, return_exceptions=True)

            # Filter out exceptions
            scraped_content = [
                content
                for content in scraped_content
                if isinstance(content, dict) and content.get("success")
            ]

        return {
            "query": query,
            "search_results": search_results,
            "scraped_content": scraped_content,
            "total_results": len(search_results),
            "total_scraped": len(scraped_content),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Tool instance
web_research_tool = WebResearchTool()
