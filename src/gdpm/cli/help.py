"""
Rich 帮助渲染器

- 纯函数构建器 (build_*) 全部可单测, 不触碰 Rich; 渲染函数 (render_*)
  只负责把构建结果交给 Rich 绘制, 三套布局: 主帮助 / 组帮助 / 叶子帮助.
- 文案一律经 i18n 词典取词条 (docstring 仅作 IDE 悬浮文档, 不参与渲染).

----

Notes
----
- BANNER: ASCII 横幅, 由 gdpm --about 展示.
- command_key: 由 click 上下文推导词典键 (根命令裸名 / godot.list 路径).
- build_usage: 叶子命令 Usage 行 (真实选项拼写 / Choice 展开 / <>[] 区分).
- build_option_rows: 选项表格行 (含默认值后缀).
- build_example_rows: 示例面板行 (英文标签查词典换语言).
- build_command_groups: 按 category 自动分组的命令清单 (删除 COMMANDS 后的
  唯一事实源).
- render_main_help / render_group_help / render_leaf_help: 三个渲染入口.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from gdpm.cli.i18n import category_keys, category_name, t

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

console = Console()

# ASCII 艺术字横幅, 由 gdpm --about 展示
BANNER = r""" ██████╗ ██████╗ ██████╗ ███╗   ███╗
██╔════╝ ██╔══██╗██╔══██╗████╗ ████║
██║  ███╗██║  ██║██████╔╝██╔████╔██║
██║   ██║██║  ██║██╔═══╝ ██║╚██╔╝██║
╚██████╔╝██████╔╝██║     ██║ ╚═╝ ██║
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝     ╚═╝"""

# 叶子帮助面板固定宽度 (沿用历史行为: min(80, 90))
_LEAF_PANEL_WIDTH = 80


def command_key(ctx: click.Context) -> str:
    """
    由 click 上下文推导词典键.

    根命令用裸名 (list), 组用自身名 (godot), 组内子命令用点号路径
    (godot.list) —— 裸名会与 godot/config 的同名子命令撞键.

    ----

    Parameters
    ----
    ctx : click.Context
        当前帮助对应的上下文.

    Returns
    ----
    str
        词典键, 如 'list' / 'godot' / 'godot.list'.
    """
    parts: list[str] = []
    node: click.Context | None = ctx
    while node is not None:
        if node.parent is not None:
            # 根上下文 (gdpm) 不进键
            parts.append(str(node.info_name))
        node = node.parent
    return ".".join(reversed(parts))


def build_usage(ctx: click.Context) -> str:
    """
    拼装叶子命令的 Usage 行.

    固化语义: 选项用真实 CLI 拼写 (--all, 而非 Python 变量名 show_all),
    Choice 选项展开全部合法取值, 参数按必选用 <name> / 可选 [name],
    metavar 优先于参数名.

    ----

    Parameters
    ----
    ctx : click.Context
        叶子命令上下文, 提供 command_path 与参数表.

    Returns
    ----
    str
        Usage 行正文 (不含 'Usage:' 前缀).
    """
    parts = [ctx.command_path]
    for param in ctx.command.params:
        if param.name == "help":
            continue
        if isinstance(param, click.Argument):
            display = param.metavar or param.name
            parts.append(f"<{display}>" if param.required else f"[{display}]")
        elif isinstance(param, click.Option):
            long_opts = [o for o in param.opts if o.startswith("--")]
            spelling = long_opts[0] if long_opts else param.opts[0]
            if param.is_flag:
                parts.append(f"[{spelling}]")
            elif isinstance(param.type, click.Choice):
                values = "|".join(str(c) for c in param.type.choices)
                parts.append(f"[{spelling} {values}]")
            else:
                parts.append(f"[{spelling} {param.metavar or 'VALUE'}]")
    return " ".join(parts)


def build_option_rows(
    params: Iterable[click.Parameter], lang: str | None = None
) -> list[tuple[str, str]]:
    """
    构建选项表格行: (选项拼写, 说明+默认值后缀).

    ----

    Parameters
    ----
    params : Iterable[click.Parameter]
        命令参数表 (自动跳过 help 与位置参数).
    lang : str | None, optional
        目标语言, None 时按全局语言配置.

    Returns
    ----
    list[tuple[str, str]]
        表格行列表, 行内容含 Rich 标记.
    """
    rows: list[tuple[str, str]] = []
    for param in params:
        if param.name == "help" or not isinstance(param, click.Option):
            continue
        opts = ", ".join(param.opts)
        desc = param.help or ""
        default = ""
        if param.default is not None and not param.is_flag:
            suffix = t("ui.default", lang).format(v=param.default)
            default = f" [dim]{suffix}[/dim]"
        elif param.is_flag and param.default:
            default = f" [dim]{t('ui.default_on', lang)}[/dim]"
        rows.append((f"  {opts}", f"{desc}{default}"))
    return rows


def build_example_rows(
    examples: Iterable[tuple[str, str]], lang: str | None = None
) -> list[str]:
    """
    构建示例面板行: 一行注释说明 + 一行命令.

    英文标签经 i18n 词典换为目标语言, 命令原文不动.

    ----

    Parameters
    ----
    examples : Iterable[tuple[str, str]]
        (命令, 英文说明) 示例对.
    lang : str | None, optional
        目标语言, None 时按全局语言配置.

    Returns
    ----
    list[str]
        面板行列表 (含 Rich 标记).
    """
    rows: list[str] = []
    for example_cmd, example_desc in examples:
        rows.append(f"  [dim]# {t(example_desc, lang)}[/dim]")
        rows.append(f"  $ {example_cmd}")
    return rows


def build_command_groups(
    commands: Mapping[str, click.Command], lang: str | None = None
) -> list[tuple[str, list[tuple[str, str]]]]:
    """
    按命令的 category 属性自动分组, 替代原 COMMANDS 双份事实源.

    分组顺序取 i18n 词典定义序 (other 兜底恒最后), 分类名与命令描述
    均从词典取词条 —— docstring/硬编码简介不再参与.

    ----

    Parameters
    ----
    commands : Mapping[str, click.Command]
        命令名到命令对象的映射 (根命令组的全部子命令).
    lang : str | None, optional
        目标语言, None 时按全局语言配置.

    Returns
    ----
    list[tuple[str, list[tuple[str, str]]]]
        [(分类展示名, [(命令名, 描述), ...]), ...], 空分类不返回.
    """
    buckets: dict[str, list[tuple[str, str]]] = {key: [] for key in category_keys()}
    for name, cmd in commands.items():
        category = str(getattr(cmd, "category", "") or "other")
        if category not in buckets:
            category = "other"
        buckets[category].append((name, t(name, lang)))
    return [
        (category_name(category, lang), rows)
        for category, rows in buckets.items()
        if rows
    ]


def _panel_width() -> int:
    """
    组/主帮助的面板宽度: 留出边距并限制在 80 列内.

    ----

    Returns
    ----
    int
        面板宽度 (字符).
    """
    return min(console.width - 6, 80)


def render_main_help(commands: Mapping[str, click.Command]) -> None:
    """
    渲染主帮助 (gdpm): 命令总览, 用法提示与公共选项.

    ----

    Parameters
    ----
    commands : Mapping[str, click.Command]
        根命令组的全部子命令.

    Returns
    ----
    None
        无.
    """
    panel_width = _panel_width()
    console.print()

    table = Table(
        box=None,
        show_header=False,
        padding=(0, 1),
        width=panel_width - 4,
    )
    table.add_column("Content", justify="left")

    for category_display, rows in build_command_groups(commands):
        table.add_row(Text(f"  {category_display}", style="bold magenta"))
        for name, desc in rows:
            table.add_row(
                Text(f"    {name:<16}", style="green") + Text(desc, style="dim")
            )
        table.add_row(Text(""))

    console.print(
        Panel(
            table,
            title=f"[bold cyan]{t('ui.commands')}[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=panel_width,
        )
    )

    console.print()
    console.print(
        Text(f"  {t('ui.usage')} ", style="dim")
        + Text("gdpm", style="bold green")
        + Text(" <command>", style="white")
        + Text(" [options]", style="dim")
    )
    console.print(
        Text(f"  {t('ui.help')}  ", style="dim")
        + Text("gdpm", style="bold green")
        + Text(" <command>", style="white")
        + Text(" --help", style="dim")
    )
    console.print()
    common_lines = "\n".join(
        f"  {opt:<16}{t(label)}"
        for opt, label in (
            ("-h, --help", "ui.opt_help"),
            ("-a, --about", "ui.opt_about"),
            ("-V, --version", "ui.opt_version"),
            ("-y, --yes", "ui.opt_yes"),
        )
    )
    console.print(
        Panel(
            Text(common_lines, style="dim"),
            title=f"[bold cyan]{t('ui.common_options')}[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=panel_width,
        )
    )


def render_group_help(
    ctx: click.Context,
    commands: Mapping[str, click.Command],
    examples: list[tuple[str, str]],
) -> None:
    """
    渲染子命令组帮助 (如 gdpm godot / gdpm cache).

    标题与子命令描述均从词典取词条 (跟随语言配置).

    ----

    Parameters
    ----
    ctx : click.Context
        命令组上下文.
    commands : Mapping[str, click.Command]
        组内全部子命令.
    examples : list[tuple[str, str]]
        组级示例列表.

    Returns
    ----
    None
        无.
    """
    panel_width = _panel_width()
    group_key = command_key(ctx)

    console.print()
    console.print(
        Text(f"  gdpm {ctx.info_name}", style="bold green")
        + Text(f"  {t(group_key)}", style="dim")
    )
    console.print()
    console.print(
        Text(f"  {t('ui.usage')} ", style="dim")
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
    table.add_column(t("ui.command"), style="green", width=16, justify="left")
    table.add_column(t("ui.description"), justify="left")

    for name in commands:
        table.add_row(f"  {name}", t(f"{group_key}.{name}"))

    console.print(
        Panel(
            table,
            title=f"[bold cyan]{t('ui.commands')}[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=panel_width,
        )
    )

    if examples:
        console.print(
            Panel(
                "\n".join(build_example_rows(examples)),
                title=f"[bold cyan]{t('ui.examples')}[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=panel_width,
            )
        )


def render_leaf_help(
    ctx: click.Context,
    params: list[click.Parameter],
    examples: list[tuple[str, str]],
) -> None:
    """
    渲染叶子命令帮助: 标题行, Usage, 选项表格与示例面板.

    标题描述取自词典 (command_key), docstring 不参与渲染.

    ----

    Parameters
    ----
    ctx : click.Context
        叶子命令上下文.
    params : list[click.Parameter]
        命令参数表.
    examples : list[tuple[str, str]]
        示例列表.

    Returns
    ----
    None
        无.
    """
    console.print()
    console.print(
        Text(f"  {ctx.command_path}", style="bold green")
        + Text(f"  {t(command_key(ctx))}", style="dim")
    )
    console.print()
    console.print(
        Text(f"  {t('ui.usage')} ", style="dim") + Text(build_usage(ctx), style="white")
    )
    console.print()

    option_rows = build_option_rows(params)
    if option_rows:
        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold",
            padding=(0, 2),
            width=_LEAF_PANEL_WIDTH,
        )
        table.add_column(t("ui.option"), style="green", min_width=20, justify="left")
        table.add_column(t("ui.description"), justify="left")

        for opts, desc in option_rows:
            table.add_row(opts, desc)

        console.print(
            Panel(
                table,
                title=f"[bold cyan]{t('ui.options')}[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=_LEAF_PANEL_WIDTH,
            )
        )

    if examples:
        console.print(
            Panel(
                "\n".join(build_example_rows(examples)),
                title=f"[bold cyan]{t('ui.examples')}[/bold cyan]",
                border_style="dim",
                padding=(0, 1),
                width=_LEAF_PANEL_WIDTH,
            )
        )
