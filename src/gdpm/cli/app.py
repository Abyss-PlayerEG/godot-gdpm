"""
CLI 应用入口. 本模块定义 gdpm 命令行主入口和基于 Rich 的帮助渲染系统.

CLI application entry point. This module defines the gdpm CLI entry point
and the Rich-based help rendering system.

----

Note:
    - BANNER / COMMANDS: ASCII 横幅与主帮助中的命令分类清单 /
        ASCII banner and the categorized command catalog for main help.
    - GdpmCommand / GdpmGroup: 自定义 click 命令与命令组类, 渲染 Rich 帮助 /
        Custom click command/group classes that render Rich help panels.
    - print_info / print_version / print_completion: 全局选项的回调 /
        Eager callbacks for the global options.
    - main: 根命令组, 在模块尾部挂载全部子命令 /
        Root command group, with all subcommands mounted at module bottom.
"""

from __future__ import annotations

from typing import Any

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gdpm import __tag__, __version__
from gdpm.constants import GITHUB_API_URL, REPO_URL

console = Console()

# ASCII 艺术字横幅, 由 gdpm --info 展示 /
# ASCII art banner displayed by gdpm --info.
BANNER = r""" ██████╗ ██████╗ ██████╗ ███╗   ███╗
██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
██║  ███╗██║  ██║██████╔╝██╔████╔██║
██║   ██║██║  ██║██╔═══╝ ██║╚██╔╝██║
╚██████╔╝██████╔╝██║     ██║ ╚═╝ ██║
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝     ╚═╝"""

# 主帮助中的命令分类: 分类名 -> {命令名: 简介} /
# Command catalog for main help: category -> {command: summary}.
COMMANDS = {
    "Project": {
        "init": "Initialize a new gdpm project",
        "create": "Create a new Godot project",
        "sync": "Sync addons/ to lock file state",
        "lock": "Generate or update lock file",
        "list": "List installed plugins",
        "status": "Show plugin status and updates",
    },
    "Dependencies": {
        "add": "Add plugins to the project",
        "remove": "Remove plugins",
        "update": "Update plugins to newer versions",
        "search": "Search Godot Asset Store",
        "info": "Show plugin details",
        "cache": "Manage global cache (info, clean)",
        "export": "Export plugins to zip archive",
        "import": "Import plugins from zip archive",
    },
    "Engine": {
        "godot": "Manage Godot engine versions",
    },
}


class GdpmCommand(click.Command):
    """
    使用 Rich 渲染帮助的自定义命令类. 在 click 标准帮助之外渲染: 标题行,
    Usage 行, Options 表格和 Examples 面板.

    Custom click command with Rich help. Renders a title line, Usage line,
    Options table and Examples panel on top of the standard click help
    output.
    """

    def __init__(
        self,
        *args: Any,
        examples: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化命令并保存示例列表.

        Initialize the command and store examples.

        ----

        Args:
            *args: 透传给 click.Command / Passed through to click.Command.
            examples: (命令, 说明) 示例对, 展示在 Examples 面板 /
                (command, description) pairs shown in the Examples panel.
            **kwargs: 透传给 click.Command / Passed through to click.Command.
        """
        super().__init__(*args, **kwargs)
        self.examples: list[tuple[str, str]] = examples or []

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """
        渲染 Rich 风格的命令帮助. 依次输出标题, 用法行, 选项表格和示例面板.

        Render Rich-styled command help. Prints the title, usage line, options
        table and examples panel.

        ----

        Args:
            ctx: click 上下文, 提供命令名等信息 /
                click context providing the command name and more.
            formatter: click 帮助格式化器, 本实现未使用 /
                click help formatter, unused in this implementation.
        """
        console.print()
        console.print(
            Text(f"  gdpm {ctx.info_name}", style="bold green")
            + Text(f"  {self.help or ''}", style="dim")
        )
        console.print()

        # 根据参数类型拼装 Usage: 必填用 <name>, 标志用 [--name], 其余用 VALUE /
        # Build Usage from params: <name> for required, [--name] for flags,
        # [--name VALUE] otherwise.
        usage_parts = [f"gdpm {ctx.info_name}"]
        for param in self.params:
            if param.name == "help":
                continue
            if param.required:
                usage_parts.append(f"<{param.name}>")
            elif isinstance(param, click.Option) and param.is_flag:
                usage_parts.append(f"[--{param.name}]")
            else:
                usage_parts.append(f"[--{param.name} VALUE]")
        console.print(
            Text("  Usage: ", style="dim") + Text(" ".join(usage_parts), style="white")
        )
        console.print()

        # 收集全部 Option 参数 (排除 help), 渲染为选项表格 /
        # Collect all Option params (except help) for the options table.
        options = [
            p for p in self.params if p.name != "help" and isinstance(p, click.Option)
        ]
        if options:
            table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold",
                padding=(0, 2),
                width=min(80, 90),
            )
            table.add_column("Option", style="green", min_width=20, justify="left")
            table.add_column("Description", justify="left")

            for param in options:
                opts = ", ".join(param.opts)
                desc = param.help or ""
                # 非标志参数显示默认值; 默认开启的标志显示 (default: on) /
                # Show default for non-flags; flags defaulting on show (default: on).
                default = ""
                if param.default is not None and not param.is_flag:
                    default = f" [dim](default: {param.default})[/dim]"
                elif param.is_flag and param.default:
                    default = " [dim](default: on)[/dim]"
                table.add_row(f"  {opts}", f"{desc}{default}")

            console.print(
                Panel(
                    table,
                    title="[bold cyan]Options[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=min(80, 90),
                )
            )

        # 示例面板: 每条示例渲染为一行说明注释和一行命令 /
        # Examples panel: each example renders as a comment line plus a command line.
        if self.examples:
            lines = []
            for example_cmd, example_desc in self.examples:
                lines.append(f"  [dim]# {example_desc}[/dim]")
                lines.append(f"  $ {example_cmd}")
            console.print(
                Panel(
                    "\n".join(lines),
                    title="[bold cyan]Examples[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=min(80, 90),
                )
            )


class GdpmGroup(click.Group):
    """
    使用 Rich 渲染帮助的自定义命令组类. 根据上下文区分主帮助 (gdpm) 与
    子命令组帮助 (如 gdpm cache), 分别交给不同布局的渲染方法处理.

    Custom click group with Rich help. Dispatches to different layouts for
    the main help (gdpm) and subgroup help (e.g. gdpm cache).
    """

    def __init__(
        self,
        *args: Any,
        examples: list[tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        初始化命令组并保存示例列表.

        Initialize the group and store examples.

        ----

        Args:
            *args: 透传给 click.Group / Passed through to click.Group.
            examples: (命令, 说明) 示例对, 展示在 Examples 面板 /
                (command, description) pairs shown in the Examples panel.
            **kwargs: 透传给 click.Group / Passed through to click.Group.
        """
        super().__init__(*args, **kwargs)
        self.examples: list[tuple[str, str]] = examples or []

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """
        按上下文分发帮助渲染. 主命令 (gdpm) 渲染总览帮助, 其余命令组渲染
        子命令帮助.

        Dispatch help rendering by context. The root command (gdpm) renders
        the overview help; other groups render the subcommand help.

        ----

        Args:
            ctx: click 上下文 / click context.
            formatter: click 帮助格式化器, 本实现未使用 /
                click help formatter, unused in this implementation.
        """
        terminal_width = console.width
        # 面板宽度留出边距, 并限制在 80 列内 /
        # Keep some margin and cap the panel width at 80 columns.
        panel_width = min(terminal_width - 6, 80)

        if ctx.info_name == "gdpm":
            self._format_main_help(ctx, panel_width)
        else:
            self._format_group_help(ctx, panel_width)

    def _format_main_help(self, ctx: click.Context, panel_width: int) -> None:
        """
        渲染主帮助: 命令总览, 用法与公共选项. 显示按类别分组的命令清单,
        Usage/Help 提示行和公共选项面板.

        Render the main help. Shows the categorized command list, Usage/Help
        hint lines and the Common Options panel.

        ----

        Args:
            ctx: click 上下文 / click context.
            panel_width: 面板宽度 (字符) / Panel width in characters.
        """
        console.print()

        table = Table(
            box=None,
            show_header=False,
            padding=(0, 1),
            width=panel_width - 4,
        )
        table.add_column("Content", justify="left")

        # 按分类渲染命令清单, 分类名用品红色标题行 /
        # Render the command list per category with magenta category headers.
        for category, cmds in COMMANDS.items():
            table.add_row(Text(f"  {category}", style="bold magenta"))
            for cmd_name, desc in cmds.items():
                table.add_row(
                    Text(f"    {cmd_name:<16}", style="green") + Text(desc, style="dim")
                )
            table.add_row(Text(""))

        console.print(
            Panel(
                table,
                title="[bold cyan]Commands[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=panel_width,
            )
        )

        console.print()
        console.print(
            Text("  Usage: ", style="dim")
            + Text("gdpm", style="bold green")
            + Text(" <command>", style="white")
            + Text(" [options]", style="dim")
        )
        console.print(
            Text("  Help:  ", style="dim")
            + Text("gdpm", style="bold green")
            + Text(" <command>", style="white")
            + Text(" --help", style="dim")
        )
        console.print()
        console.print(
            Panel(
                Text("  -h, --help      Show help message\n", style="dim")
                + Text("  -i, --info      Show project info and version\n", style="dim")
                + Text("  -V, --version   Show version\n", style="dim")
                + Text("  -y, --yes       Skip confirmation prompts", style="dim"),
                title="[bold cyan]Common Options[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=panel_width,
            )
        )

    def _format_group_help(self, ctx: click.Context, panel_width: int) -> None:
        """
        渲染子命令组帮助. 显示组标题, 用法行, 子命令表格以及可选的示例面板.

        Render subgroup help. Shows the group title, usage line, subcommand
        table and the optional examples panel.

        ----

        Args:
            ctx: click 上下文 / click context.
            panel_width: 面板宽度 (字符) / Panel width in characters.
        """
        console.print()
        console.print(
            Text(f"  gdpm {ctx.info_name}", style="bold green")
            + Text(f"  {self.help or ''}", style="dim")
        )
        console.print()
        console.print(
            Text("  Usage: ", style="dim")
            + Text(f"gdpm {ctx.info_name}", style="bold green")
            + Text(" <command>", style="white")
        )
        console.print()

        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold magenta",
            padding=(0, 2),
            width=panel_width - 4,
        )
        table.add_column("Command", style="green", width=16, justify="left")
        table.add_column("Description", justify="left")

        for name, cmd in self.commands.items():
            table.add_row(f"  {name}", cmd.help or "")

        console.print(
            Panel(
                table,
                title="[bold cyan]Commands[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=panel_width,
            )
        )

        # 示例面板: 每条示例渲染为一行说明注释和一行命令 /
        # Examples panel: each example renders as a comment line plus a command line.
        if self.examples:
            lines = []
            for example_cmd, example_desc in self.examples:
                lines.append(f"  [dim]# {example_desc}[/dim]")
                lines.append(f"  $ {example_cmd}")
            console.print(
                Panel(
                    "\n".join(lines),
                    title="[bold cyan]Examples[/bold cyan]",
                    border_style="dim",
                    padding=(0, 1),
                    width=panel_width,
                )
            )


def _version_text() -> Text:
    """
    构建含发布标签与平台信息的版本文本.

    Build version text with tag info.

    Returns:
        富文本版本行: 基础版本, 发布标签, 安装方式与平台 /
            Rich text: base version, release tag, install type and platform.
    """
    import re

    from gdpm.utils.install import get_install_type, get_platform

    # 去掉 dev/a/b/rc 等预发布后缀得到展示用基础版本 /
    # Strip dev/a/b/rc prerelease suffixes for the displayed base version.
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
    """
    生成 shell 补全脚本.

    Generate shell completion script.

    ----

    Args:
        ctx: click 上下文 / click context.
        _param: 触发回调的参数, 未使用 / Triggering parameter, unused.
        value: 目标 shell (zsh/bash/fish) / Target shell (zsh/bash/fish).
    """
    if not value or ctx.resilient_parsing:
        return

    import os
    import subprocess

    # 复用 click 的补全协议: 设置 _GDPM_COMPLETE 后重新调用 gdpm 自身 /
    # Reuse click's completion protocol: set _GDPM_COMPLETE and re-run gdpm.
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
    """
    打印项目信息横幅与版本. 显示 ASCII 横幅, 版本, 仓库地址和贡献者列表,
    随后退出.

    Print project info banner and version. Shows the ASCII banner, version,
    repo URL and contributor list, then exits.

    ----

    Args:
        ctx: click 上下文 / click context.
        _param: 触发回调的参数, 未使用 / Triggering parameter, unused.
        value: 是否指定了 -i/--info / Whether -i/--info was given.
    """
    if not value:
        return

    import httpx
    from rich.console import Group

    # 组装信息面板内容: 横幅, 版本行和仓库地址 /
    # Assemble the info panel: banner, version line and repo URL.
    info_lines = []
    info_lines.append(Text(BANNER, style="bold cyan"))
    info_lines.append(Text(""))
    info_lines.append(Text("  ") + _version_text())
    info_lines.append(Text("  Godot Dependency Package Manager", style="dim"))
    info_lines.append(Text(""))
    info_lines.append(
        Text("  GitHub: ", style="dim") + Text(REPO_URL, style="blue underline")
    )

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

    # 从 GitHub API 拉取贡献者列表; 网络失败时静默跳过 /
    # Fetch the contributor list from the GitHub API; silently skip on failure.
    try:
        resp = httpx.get(f"{GITHUB_API_URL}contributors", timeout=5, verify=False)
        if resp.status_code == 200:
            contributors = sorted(
                [c["login"] for c in resp.json()],
                key=str.lower,
            )
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
    """
    打印版本信息并退出.

    Print version info and exit.

    ----

    Args:
        ctx: click 上下文 / click context.
        _param: 触发回调的参数, 未使用 / Triggering parameter, unused.
        value: 是否指定了 -V/--version / Whether -V/--version was given.
    """
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
    """Godot 依赖包管理器 / Godot Dependency Package Manager."""


# 子命令导入放在 main 定义之后, 避免模块间循环导入 /
# Import subcommands after main is defined to avoid circular imports.
from gdpm.cli.add import add as add_cmd  # noqa: E402
from gdpm.cli.cache_cmd import cache as cache_cmd  # noqa: E402
from gdpm.cli.create import create as create_cmd  # noqa: E402
from gdpm.cli.export import export as export_cmd  # noqa: E402
from gdpm.cli.godot import godot as godot_cmd  # noqa: E402
from gdpm.cli.import_cmd import import_cmd as import_cmd_  # noqa: E402
from gdpm.cli.info import info as info_cmd  # noqa: E402
from gdpm.cli.init import init as init_cmd  # noqa: E402
from gdpm.cli.list import list_cmd  # noqa: E402
from gdpm.cli.lock import lock as lock_cmd  # noqa: E402
from gdpm.cli.remove import remove as remove_cmd  # noqa: E402
from gdpm.cli.search import search as search_cmd  # noqa: E402
from gdpm.cli.status import status as status_cmd  # noqa: E402
from gdpm.cli.sync import sync as sync_cmd  # noqa: E402
from gdpm.cli.update import update as update_cmd  # noqa: E402

# 将全部子命令挂载到根命令组 /
# Mount all subcommands on the root command group.
main.add_command(add_cmd, "add")  # type: ignore[has-type]
main.add_command(cache_cmd, "cache")
main.add_command(create_cmd, "create")
main.add_command(export_cmd, "export")
main.add_command(godot_cmd, "godot")  # type: ignore[has-type]
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
