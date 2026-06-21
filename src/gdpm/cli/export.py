"""gdpm export command."""

from __future__ import annotations

import json

import click
from rich.console import Console

from gdpm.cli.common import require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile

console = Console()


@click.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "toml", "text"]),
    default="text",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file")
def export(fmt: str, output: str | None) -> None:
    """Export dependency list."""
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    lock_path = find_lockfile(root)
    lock_entries = read_lockfile(lock_path)
    lock_map = {e.name: e for e in lock_entries}

    all_deps = {**config.dependencies, **config.dev_dependencies}

    lines: list[str] = []

    if fmt == "json":
        data = []
        for name, dep in all_deps.items():
            entry = lock_map.get(name)
            data.append(
                {
                    "name": name,
                    "version": entry.version if entry else str(dep.constraint),
                    "source": entry.source if entry else "",
                    "is_dev": dep.is_dev,
                }
            )
        content = json.dumps(data, indent=2, ensure_ascii=False)

    elif fmt == "toml":
        lines.append(f"# gdpm export - {config.name}")
        lines.append("")
        for name, dep in all_deps.items():
            entry = lock_map.get(name)
            ver = entry.version if entry else str(dep.constraint)
            if dep.is_dev:
                lines.append(f"[dev-dependencies.{name}]")
            else:
                lines.append(f"[dependencies.{name}]")
            lines.append(f'version = "{ver}"')
            if entry:
                lines.append(f'source = "{entry.source}"')
            lines.append("")
        content = "\n".join(lines)

    else:
        lines.append(f"# {config.name} dependencies")
        lines.append("")
        for name, dep in all_deps.items():
            entry = lock_map.get(name)
            ver = entry.version if entry else str(dep.constraint)
            dev = " (dev)" if dep.is_dev else ""
            lines.append(f"{name}=={ver}{dev}")
        content = "\n".join(lines)

    if output:
        from pathlib import Path

        Path(output).write_text(content, encoding="utf-8")
        console.print(f"[green]✓[/green] Exported to [cyan]{output}[/cyan]")
    else:
        click.echo(content)
