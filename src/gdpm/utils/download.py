"""
下载工具, 提供带进度回调的文件下载与 Rich 进度条创建.

----

Note:
    - download_file: 流式下载文件.
    - create_progress: 创建下载进度条.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def download_file(
    url: str,
    dest: Path,
    *,
    filename: str = "",
    on_progress: Callable[[int, int, float], None] | None = None,
    timeout: float = 300,
) -> Path:
    """
    下载文件, 支持进度回调.

    ----

    Args:
        url: 下载地址.
        dest: 目标目录.
        filename: 文件名, 为空时从 URL 推断.
        on_progress: 进度回调 (已下载, 总大小, 速度).
        timeout: 请求超时秒数.

    Returns:
        下载文件的路径.
    """
    dest.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = url.split("/")[-1].split("?")[0]

    file_path = dest / filename

    with httpx.stream(
        "GET", url, follow_redirects=True, verify=False, timeout=timeout
    ) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        start_time = time.monotonic()

        with open(file_path, "wb") as f:
            for chunk in resp.iter_bytes(8192):
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress:
                    elapsed = time.monotonic() - start_time
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    on_progress(downloaded, total, speed)

    return file_path


def create_progress() -> Progress:
    """
    创建下载用的 Rich 进度条.

    Returns:
        配置好下载列的进度条实例.
    """
    return Progress(
        TextColumn("[bold blue]{task.fields[name]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )
