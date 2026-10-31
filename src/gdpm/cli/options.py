"""
CLI 共享选项与装饰器. 收集多个命令复用的 click 选项装饰器, 保持各命令选项一致.

----

Note:
    - yes_option: 为命令添加 -y/--yes 跳过确认选项.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Callable


def yes_option(func: Callable[..., object]) -> Callable[..., object]:
    """
    为命令添加 -y/--yes 选项的装饰器.

    ----

    example:
        @click.command()
        @yes_option
        def my_command(yes: bool) -> None:
            if yes:
                # 跳过确认提示
                ...

    ----

    Args:
        func: 待装饰的 click 命令函数.

    Returns:
        附带 -y/--yes 选项的命令函数.
    """
    return click.option(
        "-y",
        "--yes",
        is_flag=True,
        default=False,
        help="Skip all confirmation prompts.",
    )(func)
