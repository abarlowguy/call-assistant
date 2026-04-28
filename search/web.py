from tavily import TavilyClient
from config import TAVILY_API_KEY

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    return _client


def search(query: str, max_results: int = 3) -> str:
    """Returns a formatted string of top search results."""
    try:
        response = _get_client().search(query=query, max_results=max_results)
        results = response.get("results", [])
        if not results:
            return f"No results found for: {query}"
        lines = [f"**{r['title']}**\n{r['content'][:300]}" for r in results]
        return f"Web search: *{query}*\n\n" + "\n\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"
