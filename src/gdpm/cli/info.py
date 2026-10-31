"""
gdpm info 命令. 查询并展示 Godot Asset Store 插件的详细信息, 包括描述,
元数据和版本历史.

----

Note:
    - info: 命令入口, 解析 publisher/slug 并输出详情面板.
"""

from __future__ import annotations

import asyncio

import click
from rich.panel import Panel

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, is_template
from gdpm.store.client import StoreClient


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm info limbo-ai", "Show plugin details"),
        ("gdpm info rsubtil/controller-icons", "Show with publisher/slug"),
    ],
)
@click.argument("plugin_slug")
def info(plugin_slug: str) -> None:
    """显示插件的详细信息."""
    # 支持 "publisher/slug" 与仅 "slug" 两种输入形式
    parts = plugin_slug.split("/")
    if len(parts) == 2:
        publisher, slug = parts
    else:
        publisher = ""
        slug = plugin_slug

    # 商店 API 调用是异步的, 在独立协程中执行
    async def _info() -> None:
        """
        查询插件详情与版本列表并渲染信息面板.

        未提供 publisher 时先经搜索定位发布者, 查询失败输出错误并退出.
        """
        client = StoreClient()

        try:
            # 未提供 publisher 时先搜索定位发布者, 优先精确匹配 slug
            if not publisher:
                results = await client.search(slug, limit=20)
                if not results:
                    console.print(f"[red]Error:[/red] Plugin '{slug}' not found.")
                    raise SystemExit(1)

                exact = next((r for r in results if r.slug == slug), None)
                if exact:
                    author = exact.publisher_slug
                else:
                    console.print(
                        f"[red]Error:[/red] Plugin '{slug}' not found. "
                        f"Did you mean: {results[0].slug}?"
                    )
                    raise SystemExit(1)
            else:
                author = publisher

            detail = await client.get_plugin(author, slug)
            versions = await client.get_versions(author, slug)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1) from e
        finally:
            await client.close()

        add_route = f"{author}/{slug}"

        # 组装详情面板内容
        info_lines = []
        info_lines.append(
            f"[bold cyan]{detail.name}[/bold cyan]"
            + (f"  [dim]{detail.latest_version}[/dim]" if detail.latest_version else "")
        )
        info_lines.append("")
        info_lines.append(detail.description)
        info_lines.append("")

        if detail.author:
            info_lines.append(f"  Author:     {detail.author}")
        if detail.license:
            info_lines.append(f"  License:    {detail.license}")
        if detail.homepage:
            info_lines.append(f"  Store:      {detail.homepage}")
        if detail.tags:
            info_lines.append(f"  Tags:       {', '.join(detail.tags)}")
        info_lines.append("")

        # 模板类插件不可作为 addon 安装, 显示提示而非安装命令
        if is_template(detail.tags):
            info_lines.append(
                "  [yellow]Project template - not installable as addon[/yellow]"
            )
        else:
            info_lines.append(f"  Install:    [green]gdpm add {add_route}[/green]")

        # 如有版本数据则追加版本表, 最多展示 10 条
        if versions:
            info_lines.append("")
            info_lines.append("  [bold]Versions:[/bold]")
            for v in versions[:10]:
                ver = v.get("version", "")
                stable = "stable" if v.get("stable") == "True" else "pre"
                date = v.get("created", "")
                info_lines.append(f"    {ver}  {date}  [{stable}]")

        console.print(
            Panel(
                "\n".join(info_lines),
                title="[bold cyan]Info[/bold cyan]",
                border_style="dim",
                padding=(1, 2),
                width=120,
            )
        )

    asyncio.run(_info())
