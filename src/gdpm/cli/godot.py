"""gdpm godot command - Godot engine management."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from gdpm.cli.app import GdpmCommand, GdpmGroup
from gdpm.cli.common import console as gdpm_console
from gdpm.constants import GODOT_DOWNLOAD_URL, GODOT_RELEASES_URL
from gdpm.utils.install import get_godot_ext, get_godot_platform

console = gdpm_console


def _get_engines_dir() -> Path:
    """Get the global engines directory."""
    engines_dir = Path.home() / ".gdpm" / "engines"
    engines_dir.mkdir(parents=True, exist_ok=True)
    return engines_dir


@click.group(cls=GdpmGroup, examples=[
    ("gdpm godot list", "List installed Godot versions"),
    ("gdpm godot list --remote", "List available versions"),
    ("gdpm godot install 4.7", "Install Godot 4.7"),
])
def godot() -> None:
    """Manage Godot engine versions."""


@godot.command(
    name="list",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot list", "List installed versions"),
        ("gdpm godot list --remote", "List available versions"),
    ],
)
@click.option(
    "--remote", "-r", is_flag=True,
    help="List available versions from GitHub",
)
@click.option(
    "-V", "--version", "version_filter", default="", metavar="VERSION",
    help="Filter by version (e.g. '4.7', '3.6')",
)
@click.option(
    "-a", "--all", "show_all", is_flag=True,
    help="Show all versions including 1.x/2.x",
)
def godot_list(remote: bool, version_filter: str, show_all: bool) -> None:
    """List Godot engine versions."""
    if remote:
        _list_remote(version_filter, show_all)
    else:
        _list_local()


def _list_local() -> None:
    """List installed Godot versions."""
    engines_dir = _get_engines_dir()

    versions = []
    for d in sorted(engines_dir.iterdir()):
        if d.is_dir():
            has_binary = any(d.iterdir())
            versions.append((d.name, has_binary))

    if not versions:
        console.print("[dim]No Godot versions installed.[/dim]")
        console.print("  Use [bold]gdpm godot install <version>[/bold] to install.")
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Version", style="cyan", min_width=15)
    table.add_column("Status", min_width=10)

    for ver, has_binary in versions:
        status = (
            "[green]✓ Installed[/green]"
            if has_binary else "[red]✗ Incomplete[/red]"
        )
        table.add_row(ver, status)

    console.print(
        Panel(
            table,
            title=f"[bold cyan]Installed Godot ({len(versions)})[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )


def _list_remote(version_filter: str, show_all: bool) -> None:
    """List available Godot versions from GitHub."""
    try:
        resp = httpx.get(
            GODOT_RELEASES_URL,
            timeout=10,
            verify=False,
        )
        resp.raise_for_status()
        releases = resp.json()
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch releases: {e}")
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Version", style="cyan", min_width=20)
    table.add_column("Type", min_width=10)
    table.add_column("Date", min_width=12)

    for r in releases:
        tag = r.get("tag_name", "")
        pre = r.get("prerelease", False)
        date = r.get("published_at", "")[:10]

        if version_filter:
            if not tag.startswith(version_filter):
                continue
        elif not show_all and not tag.startswith(("3.", "4.", "5.")):
            continue

        ver_type = "[yellow]Pre-release[/yellow]" if pre else "[green]Stable[/green]"
        table.add_row(tag, ver_type, date)

    console.print(
        Panel(
            table,
            title="[bold cyan]Available Godot Versions[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )


def _normalize_version(version: str) -> str:
    """Normalize version string to tag format.

    '4.7' -> '4.7-stable'
    '4.7-stable' -> '4.7-stable'
    '3.6.2' -> '3.6.2-stable'
    """
    if "-stable" in version or "-rc" in version or "-beta" in version:
        return version
    return f"{version}-stable"


def _build_download_url(version: str, csharp: bool = False) -> str:
    """Build Godot download URL."""
    tag = _normalize_version(version)
    plat = get_godot_platform()
    ext = get_godot_ext()
    mono = "_mono" if csharp else ""
    return f"{GODOT_DOWNLOAD_URL}/{tag}/Godot_v{tag}{mono}_{plat}.{ext}"


def _get_asset_hash(tag: str, filename: str) -> str:
    """Get SHA256 hash for a release asset from GitHub API."""
    try:
        resp = httpx.get(
            f"{GODOT_RELEASES_URL}/tags/{tag}",
            timeout=10,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()

        for asset in data.get("assets", []):
            if asset.get("name") == filename:
                digest = asset.get("digest", "")
                if digest.startswith("sha256:"):
                    return digest[7:]
        return ""
    except Exception:
        return ""


@godot.command(
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
    """Install a Godot engine version."""
    import hashlib

    import httpx

    engines_dir = _get_engines_dir()
    tag = _normalize_version(version)
    suffix = "-csharp" if csharp else ""
    ver_dir = engines_dir / f"{tag}{suffix}"

    if ver_dir.exists():
        if not click.confirm(
            f"  Godot [cyan]{tag}{suffix}[/cyan] is already installed. "
            "Reinstall?"
        ):
            return
        shutil.rmtree(ver_dir)

    url = _build_download_url(version, csharp)
    plat = get_godot_platform()
    ext = get_godot_ext()
    filename = f"Godot_v{tag}{suffix}_{plat}.{ext}"
    zip_path = engines_dir / filename

    # Get expected hash from GitHub API
    expected_hash = _get_asset_hash(tag, filename)

    progress = Progress(
        TextColumn("[bold blue]{task.fields[name]}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    try:
        with progress:
            task_id = progress.add_task("download", name=f"Godot {tag}", total=None)

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

        # Verify hash
        if expected_hash:
            actual_hash = sha256.hexdigest()
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
        ver_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(ver_dir)

        # macOS: move .app bundle to version dir
        for app in ver_dir.glob("*.app"):
            # Make executable
            binary = app / "Contents" / "MacOS" / app.stem
            if binary.exists():
                binary.chmod(0o755)

        zip_path.unlink()
        console.print(f"[green]✓[/green] Installed Godot [bold]{tag}[/bold]")
    except Exception as e:
        console.print(f"[red]Error:[/red] Extraction failed: {e}")
        if ver_dir.exists():
            shutil.rmtree(ver_dir)
        if zip_path.exists():
            zip_path.unlink()


@godot.command(
    name="uninstall",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot uninstall 4.7", "Uninstall Godot 4.7"),
    ],
)
@click.argument("version")
def godot_uninstall(version: str) -> None:
    """Uninstall a Godot engine version."""
    engines_dir = _get_engines_dir()
    tag = _normalize_version(version)
    ver_dir = engines_dir / tag

    if not ver_dir.exists():
        console.print(f"[red]Error:[/red] Godot [cyan]{tag}[/cyan] is not installed.")
        return

    shutil.rmtree(ver_dir)
    console.print(f"[green]✓[/green] Uninstalled Godot [bold]{tag}[/bold]")
