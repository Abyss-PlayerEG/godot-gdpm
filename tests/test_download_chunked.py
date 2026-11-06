"""
download_file_chunked 分片下载测试.

用本地 HTTP 服务器验证: 4 片并行内容正确, 进度回调到满,
不支持 Range 时回退单流, 原 download_file 行为不变.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING

from gdpm.utils.download import download_file, download_file_chunked

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
