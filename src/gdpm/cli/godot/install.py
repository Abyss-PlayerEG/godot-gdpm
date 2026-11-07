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

import click
import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot.common import (
    build_download_url,
    get_engines_dir,
    normalize_version,
)
from gdpm.utils.download import download_file_chunked
from gdpm.utils.install import get_godot_ext, get_godot_platform


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

    progress = Progress(
        TextColumn("[bold blue]{task.fields[name]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    try:
        with progress:
            task_id = progress.add_task(
                "download", name=f"Godot {tag}{suffix}", total=None
            )

            last_downloaded = 0

            def on_progress(done: int, total_bytes: int, _speed: float) -> None:
                nonlocal last_downloaded
                # 首次回调设置总量, 之后按增量推进进度条
                if total_bytes and progress.tasks[int(task_id)].total is None:
                    progress.update(task_id, total=total_bytes)
                progress.update(task_id, advance=done - last_downloaded)
                last_downloaded = done

            # 4 片并行下载, 服务器不支持 Range 时自动回退单流
            download_file_chunked(
                url,
                engines_dir,
                filename=filename,
                on_progress=on_progress,
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
        from gdpm.cli.godot.common import prepare_engine_dir

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
