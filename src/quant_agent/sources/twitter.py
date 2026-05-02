from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import asyncio

from quant_agent import events

try:
    import snscrape.modules.twitter as sntwitter
except Exception:  # pragma: no cover - fallback for environments where snscrape is unavailable
    sntwitter = None


@dataclass
class TwitterClient:
    def search(self, query: str, limit: int = 20) -> List[Dict[str, str]]:
        if sntwitter is None:
            return [
                {
                    "id": "bootstrap-twitter-1",
                    "text": f"Twitter source unavailable; bootstrap result for {query}.",
                    "user": "bootstrap",
                    "url": "https://twitter.com",
                }
            ]

        results: list[Dict[str, str]] = []
        try:
            for item in sntwitter.TwitterSearchScraper(query).get_items():
                results.append(
                    {
                        "id": str(item.id),
                        "text": item.content,
                        "user": getattr(item.user, "username", ""),
                        "url": getattr(item, "url", ""),
                    }
                )
                if len(results) >= limit:
                    break
        except Exception:
            return [
                {
                    "id": "bootstrap-twitter-1",
                    "text": f"Twitter scraping unavailable; bootstrap result for {query}.",
                    "user": "bootstrap",
                    "url": "https://twitter.com",
                }
            ]
        return results or [
            {
                "id": "bootstrap-twitter-1",
                "text": f"Twitter returned no items; bootstrap result for {query}.",
                "user": "bootstrap",
                "url": "https://twitter.com",
            }
        ]

    async def search_async(self, query: str, limit: int = 20) -> List[Dict[str, str]]:
        """Async wrapper around the blocking `search` method.

        This runs the existing sync scraper in a thread and publishes each
        found tweet as a citation event for streaming UIs to consume.
        """
        # Run the blocking search in a thread pool
        results = await asyncio.to_thread(self.search, query, limit)

        # Publish each result as it arrives so frontends can stream citations.
        for item in results:
            # non-blocking publish (await) so backpressure is respected
            try:
                await events.publish({
                    "type": "twitter",
                    "query": query,
                    "id": item.get("id"),
                    "user": item.get("user"),
                    "url": item.get("url"),
                    "text_snippet": (item.get("text") or "")[:300],
                })
            except Exception:
                # best-effort: don't fail the search if publishing errors
                continue

        return results
