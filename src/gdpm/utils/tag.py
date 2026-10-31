"""
标记文件工具, 读取和解析插件目录中的 tag.gdpm 标记文件.

----

Note:
    - PluginTag: 插件标记信息.
    - read_plugin_tag: 读取单个标记.
    - scan_addons: 扫描带标记的插件.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpm.constants import LOCAL_TAG_PREFIX, TAG_FILENAME

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class PluginTag:
    """
    插件标记信息.

    ----

    Attributes:
        slug: 插件 slug.
        source: 标记文件的完整来源标识.
        is_local: 是否为本地插件.
    """

    slug: str
    source: str
    is_local: bool


def read_plugin_tag(addon_dir: Path) -> PluginTag | None:
    """
    读取 addon 目录下的 tag.gdpm.

    ----

    Args:
        addon_dir: addon 目录路径.

    Returns:
        插件标记信息; 标记文件不存在或为空时返回 None.
    """
    tag_path = addon_dir / TAG_FILENAME
    if not tag_path.exists():
        return None

    content = tag_path.read_text(encoding="utf-8").strip()
    if not content:
        return None

    is_local = content.startswith(LOCAL_TAG_PREFIX)

    slug = content.split("/")[-1] if "/" in content else content.split("+")[-1]

    return PluginTag(slug=slug, source=content, is_local=is_local)


def scan_addons(addons_dir: Path) -> list[tuple[Path, PluginTag]]:
    """
    扫描 addons 目录下带标记的插件.

    ----

    Args:
        addons_dir: addons 目录路径.

    Returns:
        (目录路径, 标记) 元组的列表.
    """
    if not addons_dir.exists():
        return []

    results: list[tuple[Path, PluginTag]] = []
    for child in sorted(addons_dir.iterdir()):
        if not child.is_dir():
            continue
        tag = read_plugin_tag(child)
        if tag:
            results.append((child, tag))
    return results
