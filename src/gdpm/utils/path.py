"""Path utilities."""

from __future__ import annotations

from pathlib import Path


def shorten_path(path: str, max_len: int = 35) -> str:
    """Shorten a path by replacing home directory with ~ and truncating.

    Args:
        path: Full path string
        max_len: Maximum length before truncation

    Returns:
        Shortened path string
    """
    short = path.replace(str(Path.home()), "~")
    if len(short) > max_len:
        short = short[: max_len - 3] + "..."
    return short
