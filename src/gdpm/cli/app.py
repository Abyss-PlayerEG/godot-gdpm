"""
CLI 应用入口

- 组合根: 定义 main 与全局选项回调, 并挂载 gdpm.cli.commands 下的
  全部子命令. 命令基类在 gdpm.cli.base, 帮助渲染在 gdpm.cli.help.

Notes
----
- print_info / print_version / print_completion: 全局选项的回调.
- main: 根命令组, 模块尾部挂载全部子命令.
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from gdpm import __tag__, __version__
from gdpm.cli.base import GdpmGroup
from gdpm.cli.commands.add import add as add_cmd
from gdpm.cli.commands.cache import cache as cache_cmd
from gdpm.cli.commands.config import config as config_cmd
from gdpm.cli.commands.create import create as create_cmd
from gdpm.cli.commands.export import export as export_cmd
from gdpm.cli.commands.godot import godot as godot_cmd
from gdpm.cli.commands.import_cmd import import_cmd as import_cmd_
from gdpm.cli.commands.info import info as info_cmd
from gdpm.cli.commands.init import init as init_cmd
from gdpm.cli.commands.list import list_cmd
from gdpm.cli.commands.lock import lock as lock_cmd
from gdpm.cli.commands.remove import remove as remove_cmd
from gdpm.cli.commands.search import search as search_cmd
from gdpm.cli.commands.status import status as status_cmd
from gdpm.cli.commands.sync import sync as sync_cmd
from gdpm.cli.commands.update import update as update_cmd
from gdpm.cli.help import BANNER
from gdpm.constants import GITHUB_API_URL, REPO_URL

console = Console()


def _version_text() -> Text:
    """构建版本文本: 基础版本 (剥预发布后缀) + 发布标签 + 安装方式与平台."""
    import re

    from gdpm.utils.install import get_install_type, get_platform

    # 去掉 dev/a/b/rc 等预发布后缀得到展示用基础版本
    base_version = re.sub(r"(\.dev\d+|[a-z]\d+|rc\d+)$", "", __version__)
    tag_display = f" [{__tag__}]" if __tag__ else ""
    install_type = get_install_type()
    platform_info = get_platform()

    return (
        Text("gdpm", style="bold white")
        + Text(f" v{base_version}", style="yellow")
        + Text(tag_display, style="dim")
        + Text(f" ({install_type} | {platform_info})", style="dim")
    )


def print_completion(ctx: click.Context, _param: click.Parameter, value: str) -> None:
    """生成 shell 补全脚本: 设置 _GDPM_COMPLETE 后重调自身 (click 补全协议)."""
    if not value or ctx.resilient_parsing:
        return

    import os
    import subprocess

    env = os.environ.copy()
    env["_GDPM_COMPLETE"] = f"{value}_source"

    result = subprocess.run(
        ["gdpm"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    click.echo(result.stdout)
    ctx.exit()


def print_info(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    """打印信息横幅与版本并退出 (-i/--info); 贡献者拉取失败时静默跳过."""
    if not value:
        return

    import httpx
    from rich.console import Group

    info_lines = [
        Text(BANNER, style="bold cyan"),
        Text(""),
        Text("  ") + _version_text(),
        Text("  Godot Dependency Package Manager", style="dim"),
        Text(""),
        Text("  GitHub: ", style="dim") + Text(REPO_URL, style="blue underline"),
    ]

    terminal_width = console.width
    console.print()
    console.print(
        Panel(
            Group(*info_lines),
            title="[bold cyan]GDPM-Info[/bold cyan]",
            border_style="dim",
            padding=(1, 2),
            width=min(terminal_width, 90),
        )
    )

    # 从 GitHub API 拉取贡献者列表; 网络失败时静默跳过
    try:
        resp = httpx.get(f"{GITHUB_API_URL}contributors", timeout=5, verify=False)
        if resp.status_code == 200:
            contributors = sorted([c["login"] for c in resp.json()], key=str.lower)
            contrib_text = Text()
            for i, name in enumerate(contributors):
                if i > 0:
                    contrib_text.append("  ")
                contrib_text.append(f"@{name}", style="cyan")
            console.print()
            console.print(
                Panel(
                    contrib_text,
                    title="[bold cyan]Contributors[/bold cyan]",
                    border_style="dim",
                    padding=(1, 2),
                    width=min(terminal_width, 90),
                )
            )
    except Exception:
        pass

    console.print()
    ctx.exit()


def print_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    """打印版本信息并退出 (-V/--version 回调)."""
    if not value:
        return

    console.print(_version_text())
    ctx.exit()


@click.group(cls=GdpmGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "-i",
    "--info",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_info,
    help="Show project info and version.",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_version,
    help="Show version and exit.",
)
@click.option(
    "--completion",
    type=click.Choice(["zsh", "bash", "fish"], case_sensitive=False),
    is_eager=True,
    expose_value=False,
    callback=print_completion,
    help="Generate shell completion script.",
)
def main() -> None:
    """Godot 依赖包管理器."""


# 将全部子命令挂载到根命令组
main.add_command(add_cmd, "add")
main.add_command(cache_cmd, "cache")
main.add_command(config_cmd, "config")
main.add_command(create_cmd, "create")
main.add_command(export_cmd, "export")
main.add_command(godot_cmd, "godot")
main.add_command(import_cmd_, "import")
main.add_command(info_cmd, "info")
main.add_command(init_cmd, "init")
main.add_command(list_cmd, "list")
main.add_command(lock_cmd, "lock")
main.add_command(remove_cmd, "remove")
main.add_command(search_cmd, "search")
main.add_command(status_cmd, "status")
main.add_command(sync_cmd, "sync")
main.add_command(update_cmd, "update")
