"""
install 下载进度任务的渲染契约测试.

复现用户实测崩溃 (KeyError 'name'): TextColumn 按 {task.fields[name]} 渲染,
分片任务显形后若缺 name 字段, rich 刷新线程会直接抛 KeyError 导致下载中断.
"""

from __future__ import annotations

import io
import time

from rich.console import Console
from rich.progress import Progress, TextColumn

from gdpm.cli.godot.install import (
    CHUNK_COUNT,
    _create_download_tasks,
    _make_slice_handler,
)


def _render_with_slice_updates() -> str:
    """用 install 同款结构渲染进度, 返回输出文本 (终端模式触发 Live 刷新)."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    with Progress(
        TextColumn("[bold blue]{task.fields[name]}"), console=console
    ) as progress:
        slice_ids, task_id = _create_download_tasks(progress, "Godot 4.7-stable")
        handler = _make_slice_handler(progress, slice_ids)

        # 模拟首次分片回调 (定长显形) 与总进度推进
        handler(0, 250_000, 1_000_000)
        handler(1, 100_000, 1_000_000)
        progress.update(task_id, total=4_000_000, completed=350_000)

        # 给 rich 的 Live 刷新线程渲染窗口 (用户崩溃发生在该线程)
        time.sleep(0.3)
    return buf.getvalue()


def test_slice_tasks_render_without_keyerror() -> None:
    """分片条显形后渲染不抛 KeyError 且行可见 (name 字段契约)."""
    out = _render_with_slice_updates()
    assert f"Slice 1/{CHUNK_COUNT}" in out
    assert "Godot 4.7-stable" in out


def test_slice_count_follows_constant(monkeypatch) -> None:
    """CHUNK_COUNT 改为 8: 分片任务数量与标签自动跟随."""
    monkeypatch.setattr("gdpm.cli.godot.install.CHUNK_COUNT", 8)
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False, width=80)
    with Progress(
        TextColumn("[bold blue]{task.fields[name]}"), console=console
    ) as progress:
        slice_ids, _ = _create_download_tasks(progress, "Godot 4.7-stable")
        labels = [progress.tasks[int(tid)].description for tid in slice_ids]

    assert len(slice_ids) == 8
    assert labels == [f"Slice {i}/8" for i in range(1, 9)]


def test_workers_param_controls_task_count() -> None:
    """workers 参数 (parallel_downloads 配置值) 决定进度条分片行数."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False, width=80)
    with Progress(
        TextColumn("[bold blue]{task.fields[name]}"), console=console
    ) as progress:
        slice_ids, _ = _create_download_tasks(progress, "Godot 4.7-stable", workers=6)
        labels = [progress.tasks[int(tid)].description for tid in slice_ids]

    assert len(slice_ids) == 6
    assert labels == [f"Slice {i}/6" for i in range(1, 7)]


def test_fallback_hides_slice_tasks() -> None:
    """回退信号 (index=None) 收起分片条, 输出不再含 Slice 行."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    with Progress(
        TextColumn("[bold blue]{task.fields[name]}"), console=console
    ) as progress:
        slice_ids, task_id = _create_download_tasks(progress, "Godot 4.7-stable")
        handler = _make_slice_handler(progress, slice_ids)

        handler(0, 250_000, 1_000_000)  # 先显形
        handler(None, 0, 0)  # 回退信号收起
        progress.update(task_id, total=1_000_000, completed=250_000)
        time.sleep(0.3)

    out = buf.getvalue()
    assert "Godot 4.7-stable" in out
    assert "Slice" not in out
