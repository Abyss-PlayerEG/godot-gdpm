"""
校验和工具

- 提供文件 SHA256 校验和计算.

----

Notes
----
- sha256_file: 计算文件校验和.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def sha256_file(path: Path) -> str:
    """
    计算文件的 SHA256 校验和.

    ----

    Parameters
    ----
    path : Path
        文件路径.

    Returns
    ----
    str
        形如 "sha256:<hex>" 的校验和字符串.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        # 分块读取, 避免大文件占用过多内存
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"
