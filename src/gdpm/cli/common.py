"""
CLI 共享工具. 提供命令实现共用的控制台实例, 文件名常量和项目根目录定位工具.

Shared CLI utilities. Provides the shared console instance, filename
constants and project-root discovery helpers used by command
implementations.

----

Note:
    - GdpmConsole / console: 自动补空行的控制台及其实例 /
        Console that pads output with blank lines, plus its instance.
    - CONFIG_FILENAME / LOCK_FILENAME / TEMPLATE_TAGS: 通用常量 /
        Common constants.
    - is_template / find_project_root / require_project: 标签与项目工具 /
        Tag and project helpers.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console


class GdpmConsole(Console):
    """
    在首次输出前和每次输出后补空行的控制台. 首次输出前打印一个空行,
    每次带内容的输出后再打印一个空行, 使命令输出与相邻内容保持视觉间隔.

    Console with padded output. Prints a blank line before the first output
    and after every non-empty output, keeping visual spacing around command
    output.
    """

    _first_print: bool = True

    def print(self, *args: object, **kwargs: object) -> None:
        """
        打印内容并按需补空行.

        Print content with automatic blank lines.

        ----

        Args:
            *args: 透传给 rich.Console.print / Passed to rich.Console.print.
            **kwargs: 透传给 rich.Console.print / Passed to rich.Console.print.
        """
        if not args:
            # 空行调用直接透传, 不做额外包装 /
            # Blank-line calls pass through without extra padding.
            super().print()
            return
        if self._first_print:
            # 仅在第一次实质输出前补一个空行 /
            # Pad a blank line only before the first real output.
            super().print()
            self._first_print = False
        super().print(*args, **kwargs)  # type: ignore[arg-type]
        super().print()


console = GdpmConsole()

# 项目配置文件名 / Project config filename.
CONFIG_FILENAME = "gdproject.toml"
# 锁文件名 / Lock filename.
LOCK_FILENAME = "gdpm.lock"

# 识别模板类插件的标签集合 (小写且去除空格) /
# Tag set identifying template plugins (lowercased, spaces removed).
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

    Whether tags mark a project template.

    ----

    Args:
        tags: 插件标签列表 / List of plugin tags.

    Returns:
        任一标签命中 TEMPLATE_TAGS 则为 True /
            True if any tag matches TEMPLATE_TAGS.
    """
    # 归一化: 转小写并去除空格后比对 / Normalize: lowercase and strip spaces.
    normalized = {t.lower().replace(" ", "") for t in tags}
    return bool(normalized & TEMPLATE_TAGS)


def find_project_root() -> Path:
    """
    从当前目录向上查找项目根目录.

    Find the project root walking up from the current directory.

    Returns:
        含 gdproject.toml 的最近父目录; 找不到则返回当前目录 /
            Nearest parent containing gdproject.toml, else the current
            directory.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / CONFIG_FILENAME).exists():
            return parent
    return current


def require_project() -> Path:
    """
    要求当前位于 gdpm 项目内并返回根目录.

    Require a gdpm project root.

    Returns:
        项目根目录路径 / Path to the project root.

    Raises:
        SystemExit: 向上未找到 gdproject.toml 时以退出码 1 终止 /
            Exits with code 1 when no gdproject.toml is found above.
    """
    root = find_project_root()
    if not (root / CONFIG_FILENAME).exists():
        console.print(
            "[red]Error:[/red] Not a gdpm project. Run [bold]gdpm init[/bold] first."
        )
        raise SystemExit(1)
    return root
