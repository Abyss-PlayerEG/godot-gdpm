"""
gdpm godot list 命令

- 列出本地或远程 Godot 版本.

----

Notes
----
- _list_local: 列出已安装的 Godot 版本.
- _list_remote: 列出官方 versions.json 中可用的版本.
- godot_list: click 命令入口.
"""

from __future__ import annotations

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot.common import (
    RemoteRelease,
    _flavor_channel,
    fetch_remote_versions,
    get_engines_dir,
)

REMOTE_PAGE_SIZE = 30  # 远程列表每页条数

# 本地排序用: 同版本号时的通道新旧次序 (stable 比 rc/beta 更新)
_CHANNEL_RANK = {"stable": 0, "rc": 1, "beta": 2, "alpha": 3, "dev": 4}


def _version_nums(version: str) -> tuple[int, ...]:
    """
    提取版本号的数字段用于排序比较.

    '4.10-stable' -> (4, 10), 无法解析 (如 '-') 时返回空元组.

    ----

    Parameters
    ----
    version : str
        版本字符串.

    Returns
    ----
    tuple[int, ...]
        数值分量元组, 空元组表示无法解析.
    """
    core = version.partition("-")[0]
    try:
        return tuple(int(p) for p in core.split("."))
    except ValueError:
        return ()


def _sort_local_rows(rows: list[dict[str, str]]) -> None:
    """
    对本地引擎行按版本新旧排序 (新版本在前), 原地修改.

    数值版本降序为主序 (4.10 优先于 4.7, 非字符串序),
    同版本号按通道 stable 优先 (stable 比 rc/beta 更新),
    再按名称与版本字符串升序保证确定性, 版本无法解析的条目排在最后.

    ----

    Parameters
    ----
    rows : list[dict[str, str]]
        本地引擎行列表, 含 version 与 name 字段.

    Returns
    ----
    None
        无, 原地排序.
    """
    # 稳定排序的四段式: 先次级键, 后主键 (reverse)
    rows.sort(key=lambda r: r["version"])
    rows.sort(key=lambda r: r["name"])
    rows.sort(key=lambda r: _CHANNEL_RANK.get(_local_channel(r["version"]), 9))
    rows.sort(key=lambda r: _version_nums(r["version"]), reverse=True)


def _local_channel(version: str) -> str:
    """
    从本地引擎版本串推导发布通道.

    先剥 -csharp/-mono 变体后缀, 再去掉通道序号, 如
    '4.4-stable-csharp' -> 'stable', '4.8-rc1' -> 'rc'.

    ----

    Parameters
    ----
    version : str
        本地引擎版本串, 如 '4.4-stable'.

    Returns
    ----
    str
        发布通道名, 无法推导时为空串.
    """
    _, _, flavor = version.partition("-")
    flavor = flavor.replace("-csharp", "").replace("-mono", "")
    return _flavor_channel(flavor)


def _filter_local_rows(
    rows: list[dict[str, str]], version_filter: str, channel: str | None
) -> list[dict[str, str]]:
    """
    对本地引擎行做版本与通道筛选.

    仅显式指定时生效: -V 按版本前缀匹配, -c 按发布通道精确匹配.
    本地是库存视图, 不套用远程的默认 stable 规则.

    ----

    Parameters
    ----
    rows : list[dict[str, str]]
        引擎行列表 (含 version 字段).
    version_filter : str
        版本前缀, 空串表示不过滤.
    channel : str | None
        发布通道, None 表示不过滤.

    Returns
    ----
    list[dict[str, str]]
        筛选后的行列表.
    """
    result = rows
    if version_filter:
        result = [r for r in result if r["version"].startswith(version_filter)]
    if channel:
        result = [r for r in result if _local_channel(r["version"]) == channel]
    return result


def _list_local(
    show_id: bool = False,
    version_filter: str = "",
    channel: str | None = None,
) -> None:
    """
    列出已安装的 Godot 版本.

    按版本新旧排序 (新版本在前), 默认列与 -id 列共用该顺序.

    ----

    Parameters
    ----
    show_id : bool, optional
        以 ID 列 (Name@Version) 展示, 而非名称和版本两列.
    version_filter : str, optional
        版本前缀筛选, 如 '4.4'.
    channel : str | None, optional
        发布通道筛选, 如 'stable', 'rc'.

    Returns
    ----
    None
        无, 结果直接打印到终端.
    """
    from gdpm.config.local_engines import load_local_engines
    from gdpm.utils.path import shorten_path

    engines_dir = get_engines_dir()
    local_engines = load_local_engines()

    rows: list[dict[str, str]] = []

    if engines_dir.exists():
        for d in sorted(engines_dir.iterdir()):
            if d.is_dir():
                rows.append(
                    {
                        "name": "gdpm-godot",
                        "version": d.name,
                        "source": shorten_path(str(d)),
                    }
                )

    for name, engine in sorted(local_engines.items()):
        rows.append(
            {
                "name": name,
                "version": engine.version or "-",
                "source": shorten_path(engine.path),
            }
        )

    # 显式 -V/-c 筛选 (排序在筛选前, 两种显示模式共用)
    _sort_local_rows(rows)
    rows = _filter_local_rows(rows, version_filter, channel)

    if not rows:
        if version_filter or channel:
            console.print(
                "[dim]No engines match the filter.[/dim]\n"
                "  Use [bold]gdpm godot list[/bold] without -V/-c to list all."
            )
        else:
            console.print(
                "[dim]No Godot versions installed.[/dim]\n"
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


def _paginate_remote(
    releases: list[RemoteRelease],
    version_filter: str,
    channel: str | None,
    show_all: bool,
    page: int,
) -> tuple[list[RemoteRelease], int, int]:
    """
    对远程版本列表做过滤与分页.

    通道规则: -c 显式指定优先; -a 表示不限通道; 其余情况默认只看正式版.
    分页规则: 仅 -a 不分页, 其余模式 (含 -V/-c 筛选) 一律按页切片.

    ----

    Parameters
    ----
    releases : list[RemoteRelease]
        全量版本条目 (新版本在前).
    version_filter : str
        版本前缀过滤, 非空时与其他条件取交集.
    channel : str | None
        发布通道过滤 (stable/rc/beta/alpha/dev), None 表示走默认通道规则.
    show_all : bool
        为 True 时不限通道与版本范围, 且不分页.
    page : int
        请求的页码, 越界时收敛到有效范围.

    Returns
    ----
    tuple[list[RemoteRelease], int, int]
        (本页条目, 总页数, 生效页码), -a 时总页数为 1.
    """
    result = releases
    if version_filter:
        result = [r for r in result if r.tag.startswith(version_filter)]

    # 通道: -c 显式指定优先, -a 不限通道, 其余默认只看正式版
    if channel:
        result = [r for r in result if r.channel == channel]
    elif not show_all:
        result = [r for r in result if r.stable]

    # 仅 -a 免除分页
    if show_all:
        return result, 1, 1

    # 旧版本隐藏只作用于默认视图, -V/-c 显式筛选不受限 (如 -V 2.)
    if not version_filter and not channel:
        result = [r for r in result if r.tag.startswith(("3.", "4.", "5."))]

    total_pages = max(1, (len(result) + REMOTE_PAGE_SIZE - 1) // REMOTE_PAGE_SIZE)
    page = min(max(page, 1), total_pages)
    start = (page - 1) * REMOTE_PAGE_SIZE
    return result[start : start + REMOTE_PAGE_SIZE], total_pages, page


def _list_remote(
    version_filter: str, channel: str | None, show_all: bool, page: int = 1
) -> None:
    """
    列出官方 versions.json 中可用的 Godot 版本.

    ----

    Parameters
    ----
    version_filter : str
        版本前缀过滤, 如 '4.7'.
    channel : str | None
        发布通道过滤, 如 'stable', 'beta'; 缺省时默认只看正式版.
    show_all : bool
        不限通道与版本范围 (含 1.x/2.x) 且不分页.
    page : int, optional
        远程列表页码, 仅 -a 指定时忽略.

    Returns
    ----
    None
        无, 结果直接打印到终端.
    """
    try:
        all_releases = fetch_remote_versions()
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to fetch versions: {e}")
        return

    releases, total_pages, page = _paginate_remote(
        all_releases, version_filter, channel, show_all, page
    )

    terminal_width = console.width

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
        padding=(0, 2),
        width=min(terminal_width - 6, 90),
    )
    table.add_column("Version", style="cyan", min_width=20)
    table.add_column("Channel", min_width=10)
    table.add_column("Date", min_width=12)

    for r in releases:
        # 通道名上色: stable 绿色, 其余预发布通道黄色
        color = "green" if r.stable else "yellow"
        table.add_row(r.tag, f"[{color}]{r.channel}[/{color}]", r.date)

    if not table.row_count:
        console.print(
            "[dim]No versions found. Use [bold]-a[/bold] to show all versions.[/dim]"
        )
        return

    # 分页时展示页码, 仅 -a 不分页时展示总条数
    title_suffix = (
        f"(page {page}/{total_pages})" if total_pages > 1 else f"({len(releases)})"
    )
    console.print(
        Panel(
            table,
            title=f"[bold cyan]Available Godot Versions {title_suffix}[/bold cyan]",
            border_style="dim",
            padding=(0, 1),
            width=min(terminal_width, 90),
        )
    )


@click.command(
    name="list",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot list", "List installed versions"),
        ("gdpm godot list --remote", "List available versions"),
        ("gdpm godot list -V 4.4", "Filter installed versions"),
        ("gdpm godot list -r -c stable", "List stable releases only"),
    ],
)
@click.option(
    "--remote",
    "-r",
    is_flag=True,
    help="List available versions from official versions.json",
)
@click.option(
    "-V",
    "--version",
    "version_filter",
    default="",
    metavar="VERSION",
    help="Filter by version prefix, e.g. '4.7'",
)
@click.option(
    "-c",
    "--channel",
    type=click.Choice(["stable", "rc", "beta", "alpha", "dev"]),
    default=None,
    help="Filter by release channel (remote defaults to stable)",
)
@click.option(
    "-a",
    "--all",
    "show_all",
    is_flag=True,
    help="Show all versions, any channel, no paging (with --remote)",
)
@click.option(
    "-p", "--page", "page", default=1, type=int, help="Page number for remote list"
)
@click.option(
    "-id", "show_id", is_flag=True, help="Show ID column instead of Name and Version"
)
def godot_list(
    *,
    remote: bool,
    version_filter: str,
    channel: str | None,
    show_all: bool,
    page: int,
    show_id: bool,
) -> None:
    """列出 Godot 引擎版本."""
    if remote:
        _list_remote(version_filter, channel, show_all, page)
    else:
        _list_local(show_id, version_filter, channel)
