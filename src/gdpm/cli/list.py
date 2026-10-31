"""
gdpm list 命令. 列出项目中已安装的插件及其版本与来源, 支持表格和 JSON
两种输出.

----

Note:
    - list_cmd: 命令入口, 扫描 addons 并渲染表格或 JSON.
"""

from __future__ import annotations

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.utils.tag import scan_addons


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm list", "List all installed plugins"),
        ("gdpm list --json", "Output as JSON"),
    ],
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_cmd(as_json: bool) -> None:
    """列出已安装的插件."""
    root = require_project()
    config = read_project_config(root / "gdproject.toml")
    addons_dir = root / config.addons_dir
    # 锁条目按插件名索引, 用于查询已锁定版本
    lock_entries = {e.name: e for e in read_lockfile(find_lockfile(root))}

    installed: list[dict[str, str]] = []

    # 扫描 addons 目录, 汇总每个插件的名称, slug, 版本和来源
    for addon_path, tag in scan_addons(addons_dir):
        locked = lock_entries.get(tag.slug)
        # 本地插件显示 "local"; 其余取锁文件版本, 缺失时显示 "?"
        version = "local" if tag.is_local else (locked.version if locked else "?")

        installed.append(
            {
                "name": addon_path.name,
                "slug": tag.slug,
                "version": version,
                "source": tag.source,
            }
        )

    if as_json:
        import json

        console.print(json.dumps(installed, indent=2))
        return

    if not installed:
        console.print(
            "[dim]No plugins installed.[/dim]\n"
            "  Use [bold]gdpm add <plugin>[/bold] to install plugins."
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
    table.add_column("Plugin", style="cyan", min_width=20)
    table.add_column("Version", style="green", min_width=10)
    table.add_column("Source", min_width=10)

    # 为表格渲染准备带高亮的显示字段
    for p in installed:
        version = p["version"]
        if version == "local":
            version = f"[yellow]{version}[/yellow]"
        p["version_display"] = version

        source = p["source"]
        if source.startswith("store+"):
            source = "[blue]store[/blue]+" + source[6:]
        elif source.startswith("local+"):
            source = "[yellow]local[/yellow]+" + source[6:]

        p["source_display"] = source

    # 按来源排序, 使 store/local 插件分组展示
    installed.sort(key=lambda p: p["source"])

    for p in installed:
        table.add_row(p["name"], p["version_display"], p["source_display"])

    console.print(
        Panel(
            table,
            title=f"[bold cyan]Installed Plugins ({len(installed)})[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )
