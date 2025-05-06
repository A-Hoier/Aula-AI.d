from __future__ import annotations as _annotations

from dataclasses import dataclass
from typing import Any

import aiohttp
from bs4 import BeautifulSoup
from pydantic_ai import RunContext

from config import app_settings

# region research_agent


@dataclass
class SearchDataclass:
    max_results: int
    todays_date: str


@dataclass
class ResearchDependencies:
    todays_date: str


async def google_search(query, **kwargs):
    """
    Perform a Google search using the Custom Search API.
    Args:
        query (str): The search query.
        **kwargs: Additional parameters for the API request.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://customsearch.googleapis.com/customsearch/v1",
            params={
                "q": query,
                "key": app_settings().GOOGLE_SEARCH_API_KEY.get_secret_value(),
                "cx": app_settings().GOOGLE_SEARCH_cx.get_secret_value(),
                "num": 5,
                "cr": "countryDK",
                **kwargs,
            },
        ) as response:
            print("Status:", response.status)
            print("Content-type:", response.headers["content-type"])
            r = await response.json(encoding="utf-8")
            return [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in r.get("items", [])
            ]


async def get_search(
    search_data: RunContext[SearchDataclass], query: str, query_number: int
) -> dict[str, Any]:
    """Perform a google search for a given query.

    Args:
        query: keywords to search.
    """
    print(f"Search query {query_number}: {query}")
    max_results = search_data.deps.max_results
    results = await google_search(query=query, max_results=max_results)

    return results


async def fetch_url(ctx: RunContext, url: str) -> str:
    """
    Fetch the content of a URL.
    Args:
        url (str): The URL to fetch.
    """
    print(f"Fetching URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            res = await response.text()
            html_text = BeautifulSoup(res, "html.parser")
            return html_text.get_text()


# endregion
