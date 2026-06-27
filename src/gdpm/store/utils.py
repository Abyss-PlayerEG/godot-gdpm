"""Store utility functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gdpm.store.client import StoreClient


@dataclass
class ResolvedPlugin:
    publisher: str
    slug: str
    found: bool = True
    error: str = ""


async def resolve_publisher(
    store: StoreClient,
    name: str,
) -> ResolvedPlugin:
    """Resolve publisher from plugin name.

    Accepts:
    - "slug" → search store, return publisher
    - "publisher/slug" → return directly

    Returns ResolvedPlugin with publisher slug.
    """
    parts = name.split("/")
    if len(parts) == 2:
        return ResolvedPlugin(publisher=parts[0], slug=parts[1])

    slug = name
    try:
        results = await store.search(slug, limit=20)
        if not results:
            return ResolvedPlugin(
                publisher="",
                slug=slug,
                found=False,
                error=f"Plugin '{slug}' not found in Godot Store",
            )

        exact = next((r for r in results if r.slug == slug), None)
        if exact:
            return ResolvedPlugin(
                publisher=exact.publisher_slug,
                slug=slug,
            )

        return ResolvedPlugin(
            publisher="",
            slug=slug,
            found=False,
            error=f"Plugin '{slug}' not found. Did you mean: {results[0].slug}?",
        )
    except Exception as e:
        return ResolvedPlugin(
            publisher="",
            slug=slug,
            found=False,
            error=f"Failed to search for '{slug}': {e}",
        )
