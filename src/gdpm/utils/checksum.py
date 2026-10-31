"""
校验和工具, 提供文件 SHA256 校验和计算.

Checksum utilities. Provide SHA256 checksum computation for files.

----

Note:
    - sha256_file: 计算文件校验和 / Compute a file checksum.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def sha256_file(path: Path) -> str:
    """
    计算文件的 SHA256 校验和.

    Compute the SHA256 checksum of a file.

    ----

    Args:
        path: 文件路径 / Path to the file.

    Returns:
        形如 "sha256:<hex>" 的校验和字符串 /
            Checksum string in the form "sha256:<hex>".
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        # 分块读取, 避免大文件占用过多内存 /
        # Read in chunks to limit memory usage on large files
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"
