"""
gdpm godot install/uninstall 命令

- 安装与卸载 Godot 引擎.

----

Notes
----
- godot_install: 分片下载并解压 Godot 引擎.
- godot_uninstall: 删除已安装的 Godot 引擎.
"""

from __future__ import annotations

import shutil
import zipfile
from typing import TYPE_CHECKING

import click
import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from gdpm.cli.base import GdpmCommand
from gdpm.cli.commands.godot.common import (
    build_download_url,
    get_engines_dir,
    normalize_version,
)
from gdpm.cli.common import console
from gdpm.config.global_config import read_global_config
from gdpm.utils.download import CHUNK_COUNT, download_file_chunked
from gdpm.utils.install import get_godot_ext, get_godot_platform

if TYPE_CHECKING:
    from collections.abc import Callable


def _create_download_tasks(
    progress: Progress, total_name: str, workers: int | None = None
) -> tuple[list[TaskID], TaskID]:
    """
    创建下载进度任务: n 条分片条 (惰性显形) + 总进度条.

    分片条初始不可见, 由分片回调首次触发时定长显形;
    每个任务必须携带 name 字段 — TextColumn 按 {task.fields[name]} 渲染,
    缺失会在显形渲染时抛 KeyError.

    ----

    Parameters
    ----
    progress : Progress
        rich 进度条实例.
    total_name : str
        总进度条显示名, 如 'Godot 4.7-stable'.
    workers : int | None, optional
        分片数, None 时回退 CHUNK_COUNT (与 download_file_chunked 一致).

    Returns
    ----
    tuple[list[TaskID], TaskID]
        (分片任务 ID 列表, 总任务 ID).
    """
    n = max(1, workers or CHUNK_COUNT)
    slice_ids = [
        progress.add_task(
            f"Slice {i + 1}/{n}",
            name=f"Slice {i + 1}/{n}",
            total=None,
            visible=False,
        )
        for i in range(n)
    ]
    task_id = progress.add_task("download", name=total_name, total=None)
    return slice_ids, task_id


def _make_slice_handler(
    progress: Progress, slice_ids: list[TaskID]
) -> Callable[[int | None, int, int], None]:
    """
    构造分片进度回调, 供 download_file_chunked 的 on_slice 使用.

    首次收到某片回调时为该条定长并显形; index 为 None (回退单流)
    时收起全部分片条.

    ----

    Parameters
    ----
    progress : Progress
        rich 进度条实例.
    slice_ids : list[TaskID]
        _create_download_tasks 创建的分片任务 ID 列表.

    Returns
    ----
    Callable[[int | None, int, int], None]
        形如 on_slice 的回调函数.
    """

    def handler(index: int | None, done: int, slice_total: int) -> None:
        if index is None:
            for tid in slice_ids:
                progress.update(tid, visible=False)
            return
        tid = slice_ids[index]
        if progress.tasks[int(tid)].total is None:
            progress.update(tid, total=slice_total, visible=True)
        progress.update(tid, completed=done)

    return handler


@click.command(
    name="install",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot install 4.7", "Install latest 4.7 stable"),
        ("gdpm godot install 4.7 --csharp", "Install C# version"),
        ("gdpm godot install 3.6.2-stable", "Install specific version"),
    ],
)
@click.argument("version")
@click.option("--csharp", "-cs", is_flag=True, help="Install C# (mono) version")
def godot_install(version: str, csharp: bool) -> None:
    """安装一个 Godot 引擎版本."""
    if "-csharp" in version or "-mono" in version:
        csharp = True

    engines_dir = get_engines_dir()
    tag = normalize_version(version)
    suffix = "-csharp" if csharp else ""
    ver_dir = engines_dir / f"{tag}{suffix}"

    if ver_dir.exists():
        if not click.confirm(
            f"  Godot [cyan]{tag}{suffix}[/cyan] is already installed. Reinstall?"
        ):
            return
        # 确认后删除旧安装目录以便重装
        shutil.rmtree(ver_dir, onexc=lambda *args: None)

    # 官方接口按平台与代际拼接, 无网络请求且恒非空
    url = build_download_url(tag, csharp)

    plat = get_godot_platform()
    ext = get_godot_ext()
    filename = f"Godot_v{tag}{suffix}_{plat}.{ext}"
    zip_path = engines_dir / filename

    # 统一并行度: 分片数与进度条均取全局配置 parallel_downloads
    workers = read_global_config().parallel_downloads

    progress = Progress(
        TextColumn("[bold blue]{task.fields[name]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    try:
        with progress:
            # 分片条在上 (首次回调才定长显形), 总进度垫底
            slice_ids, task_id = _create_download_tasks(
                progress, f"Godot {tag}{suffix}", workers
            )

            last_downloaded = 0

            def on_progress(done: int, total_bytes: int, _speed: float) -> None:
                nonlocal last_downloaded
                # 首次回调设置总量, 之后按增量推进进度条
                if total_bytes and progress.tasks[int(task_id)].total is None:
                    progress.update(task_id, total=total_bytes)
                progress.update(task_id, advance=done - last_downloaded)
                last_downloaded = done

            on_slice = _make_slice_handler(progress, slice_ids)

            # 多片并行下载, 服务器不支持 Range 时自动回退单流
            download_file_chunked(
                url,
                engines_dir,
                filename=filename,
                on_progress=on_progress,
                on_slice=on_slice,
                workers=workers,
            )

    except httpx.HTTPStatusError as e:
        # 保留 404 的友好提示 (版本不存在)
        if e.response.status_code == 404:
            console.print(
                f"[red]Error:[/red] Version [cyan]{tag}[/cyan] not found.\n"
                "  Use [bold]gdpm godot list -r[/bold] "
                "to see available versions."
            )
        else:
            console.print(f"[red]Error:[/red] Download failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return
    except Exception as e:
        console.print(f"[red]Error:[/red] Download failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return

    console.print("Extracting...")

    try:
        from gdpm.cli.commands.godot.common import prepare_engine_dir

        # 解压到版本目录并修复执行权限
        ver_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(ver_dir)

        prepare_engine_dir(ver_dir)

        zip_path.unlink()
        console.print(f"[green]✓[/green] Installed Godot [bold]{tag}{suffix}[/bold]")
    except Exception as e:
        console.print(f"[red]Error:[/red] Extraction failed: {e}")
        # 解压失败时清理残留目录和压缩包
        if ver_dir.exists():
            shutil.rmtree(ver_dir)
        if zip_path.exists():
            zip_path.unlink()


@click.command(
    name="uninstall",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot uninstall 4.7", "Uninstall Godot 4.7"),
        ("gdpm godot uninstall 4.7 -cs", "Uninstall Godot 4.7 C#"),
    ],
)
@click.argument("version")
@click.option("--csharp", "-cs", is_flag=True, help="Uninstall C# (mono) version")
def godot_uninstall(version: str, csharp: bool) -> None:
    """卸载一个 Godot 引擎版本."""
    engines_dir = get_engines_dir()
    suffix = ""
    if "-csharp" in version or "-mono" in version or csharp:
        suffix = "-csharp"
        version = version.replace("-csharp", "").replace("-mono", "")
    tag = normalize_version(version)
    ver_dir = engines_dir / f"{tag}{suffix}"

    if not ver_dir.exists():
        console.print(
            f"[red]Error:[/red] Godot [cyan]{tag}{suffix}[/cyan] is not installed."
        )
        return

    shutil.rmtree(ver_dir)
    console.print(f"[green]✓[/green] Uninstalled Godot [bold]{tag}{suffix}[/bold]")
