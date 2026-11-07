"""
自定义 click 命令基类

- GdpmCommand / GdpmGroup: Rich 帮助渲染的命令与命令组类.
- 位于入口 (app) 与命令 (commands) 之间的独立层: 命令依赖本模块,
  入口组合命令, 两侧不再互相 import, 循环依赖随之消失.

----

Notes
----
- GdpmCommand: 叶子命令类, 支持 examples 示例对与 category 分组键.
- GdpmGroup: 命令组类, 按上下文分发主帮助 / 组帮助渲染.
"""

from __future__ import annotations

from typing import Any

import click

from gdpm.cli.help import render_group_help, render_leaf_help, render_main_help


class GdpmCommand(click.Command):
    """使用 Rich 渲染帮助的自定义命令类 (category 分组 + examples 示例)."""

    def __init__(
        self,
        *args: Any,
        examples: list[tuple[str, str]] | None = None,
        category: str | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化命令并保存帮助数据 (examples 示例对 / category 分组键)."""
        super().__init__(*args, **kwargs)
        self.examples: list[tuple[str, str]] = examples or []
        self.category: str | None = category

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """渲染 Rich 帮助 (标题 / Usage / 选项表 / 示例面板)."""
        render_leaf_help(ctx, self.params, self.examples)


class GdpmGroup(click.Group):
    """使用 Rich 渲染帮助的自定义命令组类 (按上下文分发主帮助/组帮助)."""

    def __init__(
        self,
        *args: Any,
        examples: list[tuple[str, str]] | None = None,
        category: str | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化命令组并保存帮助数据 (参数含义与 GdpmCommand 一致)."""
        super().__init__(*args, **kwargs)
        self.examples: list[tuple[str, str]] = examples or []
        self.category: str | None = category

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """根上下文渲染主帮助, 其余命令组渲染组帮助."""
        if ctx.parent is None:
            render_main_help(self.commands)
        else:
            render_group_help(ctx, self.commands, self.examples)
