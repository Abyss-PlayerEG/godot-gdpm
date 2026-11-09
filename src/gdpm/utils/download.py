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
- download_file: 单流顺序下载, 行为保持不变.
- download_file_chunked: 固定 4 片并行下载, 服务器不支持 Range 时回退单流.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
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

CHUNK_COUNT = 4  # 默认分片数 (parallel_downloads 配置的回退值)
MAX_SLICES = 32  # 切片数硬上限 (配置超过时按 32 计)


def clamp_workers(workers: int | None) -> int:
    """
    将并行度收敛到有效范围: 空值回退 CHUNK_COUNT, 下限 1, 上限 MAX_SLICES.

    下载切片、进度条标签与 sync 并发共用本函数, 保证三处生效值永远一致.

    ----

    Parameters
    ----
    workers : int | None
        调用方传入的并行度 (通常来自全局配置 parallel_downloads).

    Returns
    ----
    int
        [1, MAX_SLICES] 区间内的生效并行度.
    """
    return min(MAX_SLICES, max(1, workers or CHUNK_COUNT))


def download_file(
    url: str,
    dest: Path,
    *,
    filename: str = "",
    on_progress: Callable[[int, int, float], None] | None = None,
    timeout: float = 300,
    verify: bool = True,
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
    verify : bool, optional
        TLS 证书校验; False 时接受本地拦截证书 (特殊网络环境),
        默认 True (自建镜像通道严格校验).

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
        "GET", url, follow_redirects=True, verify=verify, timeout=timeout
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


def download_file_chunked(
    url: str,
    dest: Path,
    *,
    filename: str = "",
    on_progress: Callable[[int, int, float], None] | None = None,
    on_slice: Callable[[int | None, int, int], None] | None = None,
    workers: int | None = None,
    timeout: float = 300,
    verify: bool = True,
) -> Path:
    """
    分片并行下载文件 (片数由 clamp_workers 决定, 上限 32).

    先用 HEAD 探测文件大小与 Range 支持, 将字节范围均分给 workers 个
    工作线程同时下载, 各线程独立句柄按偏移直接写入目标文件, 无需合并.
    服务器不支持 Range 或探测失败时回退为 download_file 单流下载.

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
    on_slice : Callable[[int | None, int, int], None], optional
        分片进度回调, 依次传入 (分片序号, 本片已下载字节数, 本片总字节数).
        分片序号为 None 表示回退单流 (UI 应隐藏分片进度); 单流路径不触发.
    workers : int | None, optional
        分片数, None 时回退到模块常量 CHUNK_COUNT (默认 4).
        调用方通常传入全局配置 parallel_downloads 以统一并行度.
    timeout : float, optional
        请求超时秒数, 默认 300.
    verify : bool, optional
        TLS 证书校验; False 时接受本地拦截证书 (特殊网络环境),
        默认 True (自建镜像通道严格校验).

    Returns
    ----
    pathlib.Path
        下载完成的文件路径.

    Raises
    ----
    OSError
        下载结果与预期大小不一致, 且单流回退也失败.

    Notes
    ----
    - 分片数由 workers 参数控制 (缺省回退 CHUNK_COUNT=4), 经 clamp_workers
      收敛到 [1, MAX_SLICES=32] —— 配置超过 32 时按 32 计.
    - 文件过小 (不足分片数) 或不支持 Range 时直接回退单流.
    - 任一切片失败时清理半成品并回退单流下载.
    - Ctrl+C 优雅取消: cancel 事件让切片在下个分块退出, 半成品即删,
      KeyboardInterrupt 原样上抛 (调用方负责提示与退出码).
    - on_slice 与 on_progress 同锁串行, 回调内可安全更新 UI.

    Examples
    ----
    >>> download_file_chunked("https://example.com/a.zip", Path("/tmp"))
        PosixPath('/tmp/a.zip')
    """
    dest.mkdir(parents=True, exist_ok=True)
    n = clamp_workers(workers)

    if not filename:
        filename = url.split("/")[-1].split("?")[0]

    file_path = dest / filename

    # HEAD 探测: 大小与 Range 支持, 不满足则回退单流
    total = 0
    supports_range = False
    try:
        with httpx.stream(
            "HEAD", url, follow_redirects=True, verify=verify, timeout=timeout
        ) as resp:
            if resp.status_code < 400:
                total = int(resp.headers.get("content-length", 0))
                supports_range = (
                    resp.headers.get("accept-ranges", "").lower() == "bytes"
                )
    except Exception:
        pass

    if total < n or not supports_range:
        # 回退信号: 不分片, UI 据此隐藏分片进度
        if on_slice:
            on_slice(None, 0, 0)
        return download_file(
            url,
            dest,
            filename=filename,
            on_progress=on_progress,
            timeout=timeout,
            verify=verify,
        )

    # 均分为 n 段闭区间 [start, end]
    bounds = [(i * total // n, ((i + 1) * total // n) - 1) for i in range(n)]

    # 预分配目标文件, 各切片线程用独立句柄按偏移写入
    with open(file_path, "wb") as f:
        f.truncate(total)

    lock = threading.Lock()
    cancel = threading.Event()
    downloaded = 0
    start_time = time.monotonic()

    def fetch(index: int, start: int, end: int) -> None:
        nonlocal downloaded
        slice_done = 0
        slice_total = end - start + 1
        headers = {"Range": f"bytes={start}-{end}"}
        with httpx.stream(
            "GET",
            url,
            headers=headers,
            follow_redirects=True,
            verify=verify,
            timeout=timeout,
        ) as resp:
            # 必须是 206, 收到 200 说明服务器忽略了 Range
            if resp.status_code != 206:
                raise OSError(f"range request failed: HTTP {resp.status_code}")
            with open(file_path, "r+b") as f:
                f.seek(start)
                for chunk in resp.iter_bytes(8192):
                    if cancel.is_set():
                        # 取消信号: 本切片立即退出, 不再写入
                        return
                    f.write(chunk)
                    with lock:
                        downloaded += len(chunk)
                        slice_done += len(chunk)
                        if on_progress:
                            elapsed = time.monotonic() - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            on_progress(downloaded, total, speed)
                        if on_slice:
                            on_slice(index, slice_done, slice_total)

    try:
        with ThreadPoolExecutor(max_workers=n) as pool:
            try:
                futures = [
                    pool.submit(fetch, i, s, e) for i, (s, e) in enumerate(bounds)
                ]
                for future in futures:
                    future.result()
            except BaseException:
                # 任意异常 (含 Ctrl+C): 先通知切片线程退出, 再由 with 收尾
                cancel.set()
                raise
    except KeyboardInterrupt:
        # 优雅取消: 半成品即删, KI 原样上抛给调用方清理
        file_path.unlink(missing_ok=True)
        raise
    except Exception:
        # 任一切片失败: 清理半成品, 回退单流下载 (先发回退信号收起分片进度)
        file_path.unlink(missing_ok=True)
        if on_slice:
            on_slice(None, 0, 0)
        return download_file(
            url,
            dest,
            filename=filename,
            on_progress=on_progress,
            timeout=timeout,
            verify=verify,
        )

    actual = file_path.stat().st_size
    if actual != total:
        file_path.unlink(missing_ok=True)
        raise OSError(f"incomplete download: {actual}/{total} bytes")

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
