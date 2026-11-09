"""
download_file_chunked 分片下载测试.

用本地 HTTP 服务器验证: 4 片并行内容正确, 进度回调到满,
不支持 Range 时回退单流, 原 download_file 行为不变.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor as _RealExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING

import pytest

from gdpm.utils.download import CHUNK_COUNT, download_file, download_file_chunked

if TYPE_CHECKING:
    from pathlib import Path

PAYLOAD = bytes(range(256)) * 4096  # 1 MiB, 可被 4 整除


class _RangeHandler(BaseHTTPRequestHandler):
    """支持 Range 的最小 HTTP 处理器, support_range 由子类控制."""

    payload = PAYLOAD
    support_range = True

    def log_message(self, *args: object) -> None:
        pass

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        if self.support_range:
            self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

    def do_GET(self) -> None:
        rng = self.headers.get("Range")
        if rng and self.support_range:
            spec = rng.split("=", 1)[1]
            start_s, end_s = spec.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            part = self.payload[start : end + 1]
            self.send_response(206)
            self.send_header(
                "Content-Range", f"bytes {start}-{end}/{len(self.payload)}"
            )
            self.send_header("Content-Length", str(len(part)))
            self.end_headers()
            self.wfile.write(part)
        else:
            self.send_response(200)
            self.send_header("Content-Length", str(len(self.payload)))
            self.end_headers()
            self.wfile.write(self.payload)


def _serve(support_range: bool) -> tuple[ThreadingHTTPServer, str]:
    handler = type("Handler", (_RangeHandler,), {"support_range": support_range})
    # 8 片并发连接突发需要更大 backlog (默认 5 会偶发拒绝连接)
    ThreadingHTTPServer.request_queue_size = 32
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/file.bin"
    return server, url


def test_chunked_download_content(tmp_path: Path) -> None:
    """4 片并行下载后文件内容与源完全一致."""
    server, url = _serve(support_range=True)
    try:
        path = download_file_chunked(url, tmp_path)
    finally:
        server.shutdown()
    assert path.read_bytes() == PAYLOAD


def test_progress_reaches_total(tmp_path: Path) -> None:
    """进度回调最终达到总字节数."""
    server, url = _serve(support_range=True)
    calls: list[tuple[int, int]] = []
    try:
        download_file_chunked(
            url, tmp_path, on_progress=lambda d, t, s: calls.append((d, t))
        )
    finally:
        server.shutdown()
    assert calls
    assert calls[-1] == (len(PAYLOAD), len(PAYLOAD))


def test_fallback_without_range(tmp_path: Path) -> None:
    """服务器不支持 Range 时回退单流下载, 内容仍正确."""
    server, url = _serve(support_range=False)
    try:
        path = download_file_chunked(url, tmp_path)
    finally:
        server.shutdown()
    assert path.read_bytes() == PAYLOAD


def test_plain_download_unchanged(tmp_path: Path) -> None:
    """保留的单流 download_file 行为不回归."""
    server, url = _serve(support_range=True)
    try:
        path = download_file(url, tmp_path)
    finally:
        server.shutdown()
    assert path.read_bytes() == PAYLOAD


def test_on_slice_reports_every_slice(tmp_path: Path) -> None:
    """分片回调: 4 个序号齐全, 每片终值等于片长, 片长之和等于总量."""
    server, url = _serve(support_range=True)
    events: list[tuple[int, int, int]] = []
    try:
        path = download_file_chunked(
            url, tmp_path, on_slice=lambda i, d, t: events.append((i, d, t))
        )
    finally:
        server.shutdown()

    assert path.read_bytes() == PAYLOAD
    indices = {i for i, _, _ in events}
    assert indices == set(range(CHUNK_COUNT))

    # 每片最后一次回调: 已下载 == 片长; 各片长之和 == 总量; 进度单调不减
    final: dict[int, tuple[int, int]] = {}
    last_seen: dict[int, int] = {}
    for i, done, total in events:
        final[i] = (done, total)
        assert i not in last_seen or done >= last_seen[i]
        last_seen[i] = done
    for done, total in final.values():
        assert done == total
    assert sum(t for _, t in final.values()) == len(PAYLOAD)


def test_on_slice_sentinel_on_fallback(tmp_path: Path) -> None:
    """服务器不支持 Range: 只收到 index=None 回退信号, 无分片事件."""
    server, url = _serve(support_range=False)
    events: list[int | None] = []
    try:
        path = download_file_chunked(
            url, tmp_path, on_slice=lambda i, d, t: events.append(i)
        )
    finally:
        server.shutdown()

    assert path.read_bytes() == PAYLOAD
    assert events == [None]


def test_chunk_count_constant_drives_slicing(tmp_path: Path, monkeypatch) -> None:
    """CHUNK_COUNT 改为 8: 分片数、片长切分与回调序号自动跟随."""
    monkeypatch.setattr("gdpm.utils.download.CHUNK_COUNT", 8)
    server, url = _serve(support_range=True)
    events: list[tuple[int, int, int]] = []
    try:
        path = download_file_chunked(
            url, tmp_path, on_slice=lambda i, d, t: events.append((i, d, t))
        )
    finally:
        server.shutdown()

    assert path.read_bytes() == PAYLOAD
    indices = {i for i, _, _ in events}
    assert indices == set(range(8))
    final = {i: (d, t) for i, d, t in events}
    assert sum(t for _, t in final.values()) == len(PAYLOAD)


def test_workers_param_overrides_default(tmp_path: Path) -> None:
    """workers 参数 (parallel_downloads 配置值) 直接决定分片数."""
    server, url = _serve(support_range=True)
    events: list[int] = []
    try:
        path = download_file_chunked(
            url, tmp_path, workers=8, on_slice=lambda i, d, t: events.append(i)
        )
    finally:
        server.shutdown()

    assert path.read_bytes() == PAYLOAD
    assert {i for i in events if i is not None} == set(range(8))


def test_keyboard_interrupt_cleans_partial(tmp_path: Path, monkeypatch) -> None:
    """Ctrl+C: 主线程取消时半成品即删, KeyboardInterrupt 原样上抛."""

    class _KIResult:
        def __init__(self, fut: object) -> None:
            self._fut = fut

        def result(self, timeout: object = None) -> object:
            raise KeyboardInterrupt

    class _InterruptingExecutor:
        """真线程池 + 主线程首次 result() 即抛 KI (模拟 Ctrl+C 落在等待点)."""

        def __init__(self, max_workers: int | None = None) -> None:
            self._pool = _RealExecutor(max_workers=max_workers)

        def __enter__(self) -> _InterruptingExecutor:
            return self

        def __exit__(self, *exc: object) -> None:
            self.shutdown(wait=True)

        def submit(self, fn: object, *args: object, **kwargs: object) -> _KIResult:
            return _KIResult(self._pool.submit(fn, *args, **kwargs))

        def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
            self._pool.shutdown(wait=wait, cancel_futures=cancel_futures)

    monkeypatch.setattr("gdpm.utils.download.ThreadPoolExecutor", _InterruptingExecutor)
    server, url = _serve(support_range=True)
    try:
        with pytest.raises(KeyboardInterrupt):
            download_file_chunked(url, tmp_path)
    finally:
        server.shutdown()

    assert not (tmp_path / "file.bin").exists()


def test_clamp_workers_bounds() -> None:
    """生效并行度: 空值回退默认, 负数收敛 1, 超上限按 32 计."""
    from gdpm.utils.download import MAX_SLICES, clamp_workers

    assert clamp_workers(None) == CHUNK_COUNT
    assert clamp_workers(0) == CHUNK_COUNT  # 0 为 falsy, 走默认回退
    assert clamp_workers(-5) == 1
    assert clamp_workers(12) == 12
    assert clamp_workers(32) == 32
    assert clamp_workers(64) == MAX_SLICES == 32


def test_workers_clamped_to_max_slices(tmp_path: Path) -> None:
    """workers=64: 真实下载也只切 32 片 (配置超过上限按 32 计)."""
    server, url = _serve(support_range=True)
    events: list[int] = []
    try:
        path = download_file_chunked(
            url, tmp_path, workers=64, on_slice=lambda i, d, t: events.append(i)
        )
    finally:
        server.shutdown()

    assert path.read_bytes() == PAYLOAD
    assert {i for i in events if i is not None} == set(range(32))
