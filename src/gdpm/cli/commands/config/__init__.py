"""
gdpm config 命令组

- 管理 gdpm 全局配置 (config.toml): 设置配置项, 打开配置目录.

----

Notes
----
- set: 设置一个配置项 (空值恢复该项默认).
- open: 打开配置文件所在目录.
"""

from __future__ import annotations

import click

from gdpm.cli.base import GdpmGroup
from gdpm.cli.commands.config.open import config_open
from gdpm.cli.commands.config.set import config_set


@click.group(
    cls=GdpmGroup,
    category="config",
    examples=[
        (
            "gdpm config set default_engine steam-godot@4.7-stable",
            "Set default engine",
        ),
        ("gdpm config set language zh", "Switch help language (en/zh)"),
        ("gdpm config open", "Open config directory"),
    ],
)
def config() -> None:
    """管理全局配置."""


config.add_command(config_set, "set")
config.add_command(config_open, "open")
