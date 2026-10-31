"""
Store 辅助工具, 提供插件名称解析能力, 统一 "slug" 与 "publisher/slug" 两种输入.

Store utility functions. Provide plugin name resolution for both "slug" and
"publisher/slug" inputs.

----

Note:
    - ResolvedPlugin: 名称解析结果 / Name resolution result.
    - resolve_publisher: 由插件名解析发布者 / Resolve publisher from a name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gdpm.store.client import StoreClient


@dataclass
class ResolvedPlugin:
    """
    插件名称解析结果.

    Result of plugin name resolution.

    ----

    Attributes:
        publisher: 发布者 slug, 未解析时为空 / Publisher slug, empty when unresolved.
        slug: 插件 slug / Plugin slug.
        found: 是否解析成功 / Whether resolution succeeded.
        error: 错误信息, 成功时为空 / Error message, empty on success.
    """

    publisher: str
    slug: str
    found: bool = True
    error: str = ""


async def resolve_publisher(
    store: StoreClient,
    name: str,
) -> ResolvedPlugin:
    """
    根据插件名解析发布者 slug, 支持两种输入形式.

    Resolve the publisher slug from a plugin name. Accepts two input forms.

    ----

    Note:
        - "slug": 搜索商店并返回发布者 / Search the store and return the publisher.
        - "publisher/slug": 直接返回 / Return directly.

    ----

    Args:
        store: 商店客户端 / Store client.
        name: 插件名或 "publisher/slug" / Plugin name or "publisher/slug".

    Returns:
        含发布者 slug 的解析结果 / ResolvedPlugin with publisher slug.
    """
    parts = name.split("/")
    if len(parts) == 2:
        # 含斜杠时视为 "publisher/slug", 无需查询商店 /
        # Slash form is "publisher/slug"; no store lookup needed.
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

        # 优先精确匹配 slug, 避免误用搜索结果 /
        # Prefer an exact slug match to avoid picking a wrong result.
        exact = next((r for r in results if r.slug == slug), None)
        if exact:
            return ResolvedPlugin(
                publisher=exact.publisher_slug,
                slug=slug,
            )

        # 无精确匹配时给出搜索建议 /
        # Suggest the closest result when there is no exact match.
        return ResolvedPlugin(
            publisher="",
            slug=slug,
            found=False,
            error=f"Plugin '{slug}' not found. Did you mean: {results[0].slug}?",
        )
    except Exception as e:
        # 搜索失败也转为解析结果, 由调用方统一处理 /
        # Convert search failures into a result for uniform handling.
        return ResolvedPlugin(
            publisher="",
            slug=slug,
            found=False,
            error=f"Failed to search for '{slug}': {e}",
        )
