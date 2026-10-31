"""
gdpm godot install/uninstall 命令, 安装与卸载 Godot 引擎.

gdpm godot install/uninstall commands for installing and uninstalling
Godot engines.

----

Note:
    - godot_install: 下载, 校验并解压 Godot 引擎 /
        Download, verify and extract a Godot engine.
    - godot_uninstall: 删除已安装的 Godot 引擎 / Remove an installed Godot engine.
"""

from __future__ import annotations

import hashlib
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
    get_asset_hash,
    get_engines_dir,
    normalize_version,
)
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
    """安装一个 Godot 引擎版本 / Install a Godot engine version."""
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
        # 确认后删除旧安装目录以便重装 / Remove old install dir before reinstalling
        shutil.rmtree(ver_dir, onexc=lambda *args: None)

    url = build_download_url(tag, csharp)
    if not url:
        console.print(
            f"[red]Error:[/red] Failed to fetch download URL for "
            f"[cyan]{tag}{suffix}[/cyan].\n"
            "  GitHub API may be rate-limited. Try again later."
        )
        return

    plat = get_godot_platform()
    ext = get_godot_ext()
    filename = f"Godot_v{tag}{suffix}_{plat}.{ext}"
    zip_path = engines_dir / filename

    expected_hash = get_asset_hash(tag, filename)

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

            with httpx.stream("GET", url, follow_redirects=True, verify=False) as resp:
                if resp.status_code == 404:
                    console.print(
                        f"[red]Error:[/red] Version [cyan]{tag}[/cyan] not found.\n"
                        "  Use [bold]gdpm godot list -r[/bold] "
                        "to see available versions."
                    )
                    return
                resp.raise_for_status()

                total = int(resp.headers.get("content-length", 0))
                progress.update(task_id, total=total)

                sha256 = hashlib.sha256()
                with open(zip_path, "wb") as f:
                    for chunk in resp.iter_bytes(8192):
                        f.write(chunk)
                        sha256.update(chunk)
                        progress.update(task_id, advance=len(chunk))

        if expected_hash:
            actual_hash = sha256.hexdigest()
            # 校验失败时删除下载文件 / Remove the download when verification fails
            if actual_hash != expected_hash:
                zip_path.unlink()
                console.print(
                    "[red]Error:[/red] Hash verification failed.\n"
                    f"  Expected: [dim]{expected_hash}[/dim]\n"
                    f"  Actual:   [dim]{actual_hash}[/dim]"
                )
                return
            console.print("[dim]  Hash verified ✓[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] Download failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return

    console.print("Extracting...")

    try:
        from gdpm.cli.godot.common import prepare_engine_dir

        # 解压到版本目录并修复执行权限 / Extract into version dir, fix exec perms
        ver_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(ver_dir)

        prepare_engine_dir(ver_dir)

        zip_path.unlink()
        console.print(f"[green]✓[/green] Installed Godot [bold]{tag}{suffix}[/bold]")
    except Exception as e:
        console.print(f"[red]Error:[/red] Extraction failed: {e}")
        # 解压失败时清理残留目录和压缩包 / Clean partial dir and archive on failure
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
    """卸载一个 Godot 引擎版本 / Uninstall a Godot engine version."""
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
