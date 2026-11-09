"""
CLI 共享工具

- 提供命令实现共用的控制台实例, 文件名常量和项目根目录定位工具.

----

Notes
----
- GdpmConsole / console: 自动补空行的控制台及其实例.
- CONFIG_FILENAME / LOCK_FILENAME / TEMPLATE_TAGS: 通用常量.
- is_template / find_project_root / require_project: 标签与项目工具.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console


class GdpmConsole(Console):
    """
    在首次输出前和每次输出后补空行的控制台

    首次输出前打印一个空行, 每次带内容的输出后再打印一个空行,
    使命令输出与相邻内容保持视觉间隔.
    """

    _first_print: bool = True

    def print(self, *args: object, **kwargs: object) -> None:
        """
        打印内容并按需补空行.

        ----

        Parameters
        ----
        *args : object
            透传给 rich.Console.print.
        **kwargs : object
            透传给 rich.Console.print.
        """
        if not args:
            # 空行调用直接透传, 不做额外包装
            super().print()
            return
        if self._first_print:
            # 仅在第一次实质输出前补一个空行
            super().print()
            self._first_print = False
        super().print(*args, **kwargs)  # type: ignore[arg-type]
        super().print()


console = GdpmConsole()

# 项目配置文件名
CONFIG_FILENAME = "gdproject.toml"
# 锁文件名
LOCK_FILENAME = "gdpm.lock"

# 识别模板类插件的标签集合 (小写且去除空格)
TEMPLATE_TAGS = {
    "template",
    "starter kit",
    "starterkit",
    "demo",
    "project",
    "boilerplate",
    "sample",
}


def is_template(tags: list[str]) -> bool:
    """
    判断标签是否属于项目模板类插件.

    ----

    Parameters
    ----
    tags : list[str]
        插件标签列表.

    Returns
    ----
    bool
        任一标签命中 TEMPLATE_TAGS 则为 True.
    """
    # 归一化: 转小写并去除空格后比对
    normalized = {t.lower().replace(" ", "") for t in tags}
    return bool(normalized & TEMPLATE_TAGS)


def find_project_root() -> Path:
    """
    从当前目录向上查找项目根目录.

    ----

    Returns
    ----
    Path
        含 gdproject.toml 的最近父目录; 找不到则返回当前目录.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / CONFIG_FILENAME).exists():
            return parent
    return current


def require_project() -> Path:
    """
    要求当前位于 gdpm 项目内并返回根目录.

    ----

    Returns
    ----
    Path
        项目根目录路径.

    Raises
    ----
    SystemExit
        向上未找到 gdproject.toml 时以退出码 1 终止.
    """
    root = find_project_root()
    if not (root / CONFIG_FILENAME).exists():
        console.print(
            "[red]Error:[/red] Not a gdpm project. Run [bold]gdpm init[/bold] first."
        )
        raise SystemExit(1)
    return root
