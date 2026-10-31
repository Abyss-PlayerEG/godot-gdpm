"""
路径工具, 提供路径显示缩短等辅助函数.

----

Note:
    - shorten_path: 缩短路径显示.
"""

from __future__ import annotations

from pathlib import Path


def shorten_path(path: str, max_len: int = 35) -> str:
    """
    缩短路径显示: 家目录替换为 ~, 超长时截断.

    ----

    Args:
        path: 完整路径字符串.
        max_len: 截断前的最大长度.

    Returns:
        缩短后的路径字符串.
    """
    short = path.replace(str(Path.home()), "~")
    if len(short) > max_len:
        short = short[: max_len - 3] + "..."
    return short
