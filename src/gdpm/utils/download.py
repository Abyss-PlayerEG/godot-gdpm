"""
下载工具模块

- 提供带进度回调的流式文件下载与 Rich 进度条创建
- 支持大文件分块下载与实时速度显示.

----

Examples
----
path = download_file("https://example.com/a.zip", Path("/tmp"))\n
progress = create_progress()

Notes
----
- 使用场景: 插件压缩包下载 (gdpm add / gdpm sync), Godot 引擎安装包
  下载 (gdpm godot install), 以及任何需要进度显示的 HTTP 文件下载.
- 仅支持 http/https 直链下载.
- 超时默认 300 秒, 可通过 timeout 参数调整.
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

    以流式分块方式将 URL 内容写入目标目录, 写入过程中按需回调下载进度 (字节数与速度).

    ----

    Parameters
    ----
    url : str
        下载地址 (http/https 直链).
    dest : Path
        目标目录, 不存在时自动创建.
    filename : str, optional
        保存文件名, 为空时从 URL 路径推断.
    on_progress : Callable[[int, int, float], None], optional
        进度回调, 依次传入 (已下载字节数, 总字节数, 速度 B/s).
    timeout : float, optional
        请求超时秒数, 默认 300.

    Returns
    ----
    pathlib.Path
        下载完成的文件路径.

    Raises
    ----
    httpx.HTTPStatusError
        响应状态码非 2xx (如 404, 403).

    Examples
    ----
    >>> download_file("https://example.com/a.zip", Path("/tmp"))
        PosixPath('/tmp/a.zip')
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

    预配置文件名, 已下载字节数, 传输速度与剩余时间四列,
    适合与 download_file 的 on_progress 回调配合使用.

    ----

    Returns
    ----
    rich.progress.Progress
        配置好下载列的进度条实例.
    """
    return Progress(
        TextColumn("[bold blue]{task.fields[name]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )
