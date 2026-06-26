"""Download utilities."""

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
) -> Path:
    """Download a file with optional progress callback.

    Args:
        url: Download URL
        dest: Destination directory
        filename: Filename (auto-detected from URL if empty)
        on_progress: Callback(downloaded, total, speed)

    Returns:
        Path to downloaded file
    """
    dest.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = url.split("/")[-1].split("?")[0]

    file_path = dest / filename

    with httpx.stream("GET", url, follow_redirects=True, verify=False) as resp:
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


async def async_download_file(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    *,
    filename: str = "",
    on_progress: Callable[[int, int, float], None] | None = None,
) -> Path:
    """Async download a file with optional progress callback.

    Args:
        client: Async HTTP client
        url: Download URL
        dest: Destination directory
        filename: Filename (auto-detected from URL if empty)
        on_progress: Callback(downloaded, total, speed)

    Returns:
        Path to downloaded file
    """
    dest.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = url.split("/")[-1].split("?")[0]

    file_path = dest / filename

    start_time = time.monotonic()
    downloaded = 0

    async with client.stream("GET", url) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        async for chunk in resp.aiter_bytes(8192):
            with open(file_path, "ab") as f:
                f.write(chunk)
            downloaded += len(chunk)
            if on_progress:
                elapsed = time.monotonic() - start_time
                speed = downloaded / elapsed if elapsed > 0 else 0
                on_progress(downloaded, total, speed)

    return file_path


def create_progress() -> Progress:
    """Create a Rich Progress instance for downloads."""
    return Progress(
        TextColumn("[bold blue]{task.fields[name]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )
