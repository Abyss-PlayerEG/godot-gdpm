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
from gdpm.cli.common import find_project_root
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
@click.option(
    "-id", "show_id", is_flag=True,
    help="Show ID column instead of Name and Version",
)
def godot_list(
    remote: bool, version_filter: str, show_all: bool, show_id: bool
) -> None:
    """List Godot engine versions."""
    if remote:
        _list_remote(version_filter, show_all)
    else:
        _list_local(show_id)


def _list_local(show_id: bool = False) -> None:
    """List installed Godot versions."""
    from gdpm.config.local_engines import load_local_engines

    engines_dir = _get_engines_dir()
    local_engines = load_local_engines()

    rows: list[dict[str, str]] = []

    # Downloaded engines
    if engines_dir.exists():
        for d in sorted(engines_dir.iterdir()):
            if d.is_dir():
                source = str(d).replace(str(Path.home()), "~")
                if len(source) > 35:
                    source = source[:32] + "..."
                rows.append({
                    "name": "gdpm-godot",
                    "version": d.name,
                    "source": source,
                })

    # Local engines
    for name, engine in sorted(local_engines.items()):
        source = engine.path.replace(str(Path.home()), "~")
        if len(source) > 35:
            source = source[:32] + "..."
        rows.append({
            "name": name,
            "version": engine.version or "-",
            "source": source,
        })

    if not rows:
        console.print("[dim]No Godot versions installed.[/dim]")
        console.print(
            "  Use [bold]gdpm godot install <version>[/bold] to install.\n"
            "  Use [bold]gdpm godot add <path>[/bold] to add a local engine."
        )
        return

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )

    if show_id:
        table.add_column("ID", style="yellow", min_width=25)
        table.add_column("Source", style="dim")
        for row in rows:
            engine_id = f"{row['name']}@{row['version']}"
            table.add_row(engine_id, row["source"])
    else:
        table.add_column("Name", style="cyan", min_width=15)
        table.add_column("Version", style="green", min_width=15)
        table.add_column("Source", style="dim")
        for row in rows:
            table.add_row(row["name"], row["version"], row["source"])

    console.print(
        Panel(
            table,
            title=f"[bold cyan]Installed Godot ({len(rows)})[/bold cyan]",
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
    '4.7-stable-csharp' -> '4.7-stable'
    """
    # Strip -csharp suffix if present
    version = version.replace("-csharp", "").replace("-mono", "")

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

    # Auto-detect csharp from version string
    if "-csharp" in version or "-mono" in version:
        csharp = True

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
        shutil.rmtree(ver_dir, onerror=lambda *args: None)

    url = _build_download_url(tag, csharp)
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

        # macOS: fix .app bundle
        import platform
        import subprocess

        for app in ver_dir.glob("*.app"):
            # Remove quarantine attribute (Gatekeeper)
            if platform.system() == "Darwin":
                subprocess.run(
                    ["xattr", "-cr", str(app)],
                    check=False,
                    capture_output=True,
                )
            # Make all binaries executable
            macos_dir = app / "Contents" / "MacOS"
            if macos_dir.exists():
                for binary in macos_dir.iterdir():
                    binary.chmod(0o755)

        zip_path.unlink()
        console.print(f"[green]✓[/green] Installed Godot [bold]{tag}{suffix}[/bold]")
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


@godot.command(
    name="add",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot add /Applications/Godot.app", "Add macOS Godot"),
        ("gdpm godot add /usr/local/bin/godot", "Add Linux Godot"),
        ("gdpm godot add /path/to/Godot --name 4.7-custom", "Add with alias"),
    ],
)
@click.argument("path")
@click.option("--name", "-n", default="", help="Alias for the engine")
def godot_add(path: str, name: str) -> None:
    """Add a local Godot engine."""
    from gdpm.config.local_engines import add_local_engine, load_local_engines
    from gdpm.utils.godot import detect_godot_binary, get_godot_version

    engine_path = Path(path).expanduser().resolve()

    if not engine_path.exists():
        console.print(f"[red]Error:[/red] Path [cyan]{path}[/cyan] does not exist.")
        return

    # Detect binary
    binary = detect_godot_binary(engine_path)
    if not binary:
        console.print(
            "[red]Error:[/red] Not a valid Godot application.\n"
            "  macOS: provide path to .app bundle\n"
            "  Linux: provide path to executable"
        )
        return

    console.print(f"  [dim]✓ Path exists: {engine_path}[/dim]")
    console.print(f"  [dim]✓ Binary found: {binary.name}[/dim]")

    # Get version
    version = get_godot_version(binary)
    if version:
        console.print(f"  [dim]✓ Version: {version}[/dim]")
    else:
        console.print("  [dim]⚠ Could not detect version[/dim]")

    # Check if path already exists
    engines = load_local_engines()
    for existing_name, engine in engines.items():
        if engine.path == str(engine_path):
            console.print(
                f"[yellow]This path is already added as '{existing_name}'.[/yellow]"
            )
            return

    # Get alias
    if not name:
        default_name = version or engine_path.stem
        name = click.prompt("  Alias", default=default_name, type=str)

    # Check if name already exists
    if name in engines and not click.confirm(
        f"  [yellow]'{name}' already exists. Overwrite?[/yellow]"
    ):
        return

    add_local_engine(name, str(engine_path), version)
    console.print(f"[green]✓[/green] Added Godot [bold]{name}[/bold]")


def _find_engine(name: str, version: str) -> str | None:
    """Find Godot binary path by name and version.

    Returns:
        Path string to Godot binary, or None if not found.
    """
    from gdpm.config.local_engines import load_local_engines

    engines_dir = _get_engines_dir()

    # Check local engines first
    local_engines = load_local_engines()
    if name in local_engines:
        engine = local_engines[name]
        if not version or engine.version == version:
            return engine.path

    # Check downloaded engines
    if name == "gdpm-godot":
        tag = _normalize_version(version) if version else ""
        if tag:
            ver_dir = engines_dir / tag
            if ver_dir.exists():
                # Find binary
                for app in ver_dir.glob("*.app"):
                    binary = app / "Contents" / "MacOS" / "Godot"
                    if binary.exists():
                        return str(binary)
                for f in ver_dir.iterdir():
                    if f.is_file() and not f.suffix:
                        return str(f)

    return None


@godot.command(
    name="use",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot use gdpm-godot@4.7-stable", "Use downloaded engine"),
        ("gdpm godot use steam@4.7-stable", "Use local engine"),
        ("gdpm godot list -id", "List available engine IDs"),
    ],
)
@click.argument("id")
def godot_use(id: str) -> None:
    """Set the Godot engine for the current project."""
    import json

    # Parse spec: Name@Version
    if "@" not in id:
        console.print(
            "[red]Error:[/red] Invalid format. Use [cyan]Name@Version[/cyan]\n"
            "  Example: gdpm godot use gdpm-godot@4.7-stable"
        )
        return

    name, version = id.split("@", 1)

    # Find engine
    engine_path = _find_engine(name, version)
    if not engine_path:
        console.print(
            f"[red]Error:[/red] Engine [cyan]{id}[/cyan] not found.\n"
            "  Use [bold]gdpm godot list -id[/bold] to see available engines."
        )
        return

    # Write .engines-conf.json
    root = find_project_root()
    conf_path = root / ".engines-conf.json"

    conf = {}
    if conf_path.exists():
        try:
            conf = json.loads(conf_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError):
            conf = {}

    conf["godot"] = {"name": name, "version": version, "path": engine_path}

    conf_path.write_text(
        json.dumps(conf, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    console.print(
        f"[green]✓[/green] Set Godot engine to [bold]{name}@{version}[/bold]"
    )


@godot.command(
    name="info",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot info", "Show current Godot engine info"),
    ],
)
def godot_info() -> None:
    """Show current Godot engine configuration."""
    import json

    from gdpm.cli.common import require_project

    root = require_project()
    conf_path = root / ".engines-conf.json"

    if not conf_path.exists():
        console.print(
            "[red]Error:[/red] No Godot engine configured for this project.\n"
            "  Use [bold]gdpm godot use <id>[/bold] to set an engine."
        )
        return

    try:
        conf = json.loads(conf_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, TypeError):
        console.print("[red]Error:[/red] Invalid .engines-conf.json")
        return

    godot = conf.get("godot", {})
    if not godot:
        console.print(
            "[red]Error:[/red] No Godot engine configured.\n"
            "  Use [bold]gdpm godot use <id>[/bold] to set an engine."
        )
        return

    name = godot.get("name", "?")
    version = godot.get("version", "?")
    path = godot.get("path", "?")

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Key", style="dim", min_width=12)
    table.add_column("Value", style="cyan")

    table.add_row("Name", name)
    table.add_row("Version", version)
    table.add_row("Path", path)
    table.add_row("ID", f"{name}@{version}")

    console.print(
        Panel(
            table,
            title="[bold cyan]Godot Engine[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )
