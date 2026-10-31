"""
gdpm godot 子命令组, 负责 Godot 引擎版本管理.

gdpm godot command group for Godot engine management.

----

Note:
    - list: 列出已安装或远程可用的版本 / List installed or remote versions.
    - install / uninstall: 安装或卸载 Godot 引擎 / Install or uninstall engines.
    - add / remove: 管理本地 Godot 引擎 / Manage local Godot engines.
    - use / default: 设置项目或全局默认引擎 / Set project or global default engine.
    - info: 显示当前引擎配置 / Show current engine configuration.
    - open: 打开 Godot 编辑器或运行项目 / Open the editor or run the project.
"""

from __future__ import annotations

import click

from gdpm.cli.app import GdpmGroup
from gdpm.cli.godot.engine import godot_add, godot_default, godot_remove, godot_use
from gdpm.cli.godot.info import godot_info
from gdpm.cli.godot.install import godot_install, godot_uninstall
from gdpm.cli.godot.list import godot_list
from gdpm.cli.godot.open import godot_open


@click.group(
    cls=GdpmGroup,
    examples=[
        ("gdpm godot list", "List installed Godot versions"),
        ("gdpm godot list --remote", "List available versions"),
        ("gdpm godot install 4.7", "Install Godot 4.7"),
    ],
)
def godot() -> None:
    """管理 Godot 引擎版本 / Manage Godot engine versions."""


godot.add_command(godot_list, "list")
godot.add_command(godot_install, "install")
godot.add_command(godot_uninstall, "uninstall")
godot.add_command(godot_add, "add")
godot.add_command(godot_remove, "remove")
godot.add_command(godot_use, "use")
godot.add_command(godot_info, "info")
godot.add_command(godot_open, "open")
godot.add_command(godot_default, "default")
