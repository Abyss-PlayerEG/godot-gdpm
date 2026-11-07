"""
gdpm status 命令

- 展示插件状态与可用更新: 扫描 addons/, 查询版本, 对比输出.

----

Notes
----
- 扫描 addons/: 收集已安装插件.
- 查询最新版本: 从 Store 获取.
- 对比版本: 归一化后比较并标注可更新项.
- 输出结果: 表格或 JSON.
- status: 命令入口, 内部定义异步 _status.
"""

from __future__ import annotations

import asyncio

import click
from rich.table import Table

from gdpm.cli.base import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context
from gdpm.store.client import StoreClient
from gdpm.utils.tag import scan_addons
from gdpm.utils.version import normalize_version


@click.command(
    cls=GdpmCommand,
    category="project",
    examples=[
        ("gdpm status", "Show status of all plugins"),
        ("gdpm status limbo-ai", "Show status of specific plugin"),
        ("gdpm status --json", "Output as JSON"),
    ],
)
@click.argument("plugin_slug", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(plugin_slug: str | None, as_json: bool) -> None:
    """显示插件状态与可用更新."""

    async def _status() -> None:
        """收集插件状态并输出结果."""
        ctx = get_project_context()

        installed: list[dict[str, str]] = []

        for _, tag in scan_addons(ctx.addons_dir):
            if plugin_slug and tag.slug != plugin_slug:
                continue

            locked = ctx.lock_map.get(tag.slug)
            version = "local" if tag.is_local else (locked.version if locked else "?")

            installed.append(
                {
                    "slug": tag.slug,
                    "version": version,
                    "source": tag.source,
                    "is_local": str(tag.is_local),
                }
            )

        if not installed:
            if plugin_slug:
                console.print(f"[red]Plugin '{plugin_slug}' not installed.[/red]")
            else:
                console.print("[dim]No plugins installed.[/dim]")
            return

        store = StoreClient()
        results: list[dict[str, str]] = []

        try:
            for plugin in installed:
                slug = plugin["slug"]
                current_ver = plugin["version"]
                is_local = plugin.get("is_local", "False") == "True"

                if is_local:
                    results.append(
                        {
                            "slug": slug,
                            "version": "local",
                            "latest": "local",
                            "status": "✓ Local",
                        }
                    )
                    continue

                # 从 source (store+publisher/slug) 解析发布者
                source = plugin["source"]
                publisher = ""
                if "/" in source:
                    clean = source.replace("store+", "")
                    parts = clean.split("/")
                    if len(parts) >= 2:
                        publisher = parts[0]

                latest_ver = current_ver
                if publisher:
                    try:
                        versions = await store.get_versions(publisher, slug)
                        if versions:
                            latest_ver = versions[0].get("version", current_ver)
                    except Exception as e:
                        console.print(
                            f"  [dim]Failed to fetch versions for {slug}: {e}[/dim]"
                        )

                current_norm = normalize_version(current_ver.lstrip("vV"))
                latest_norm = normalize_version(latest_ver.lstrip("vV"))

                # 归一化后比较版本
                if current_norm == latest_norm:
                    update_status = "✓ Up to date"
                else:
                    update_status = f"⬆ {latest_ver}"

                results.append(
                    {
                        "slug": slug,
                        "version": current_ver,
                        "latest": latest_ver,
                        "status": update_status,
                    }
                )
        finally:
            await store.close()

        if as_json:
            import json

            console.print(json.dumps(results, indent=2))
            return

        header = f"[bold]Plugin status ({len(results)}):[/bold]"

        table = Table(show_header=True, header_style="bold", box=None)
        table.add_column("Plugin", style="cyan", min_width=20)
        table.add_column("Version", min_width=10)
        table.add_column("Latest", min_width=10)
        table.add_column("Status", min_width=15)

        for r in results:
            style = "green" if "Up to date" in r["status"] else "yellow"
            table.add_row(
                r["slug"],
                r["version"],
                r["latest"],
                f"[{style}]{r['status']}[/{style}]",
            )

        updates = [r for r in results if "⬆" in r["status"]]

        update_msg = ""
        if updates:
            update_msg = (
                f"\n[yellow]{len(updates)} update(s) available. "
                f"Run 'gdpm update' to update.[/yellow]"
            )

        console.print(f"{header}\n{table}{update_msg}")

    asyncio.run(_status())
