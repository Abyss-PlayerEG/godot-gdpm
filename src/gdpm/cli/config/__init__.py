"""
gdpm config 命令组

- 管理 gdpm 全局配置 (config.toml): 设置配置项, 恢复默认, 打开配置目录.

----

Notes
----
- set: 设置一个配置项 (空值恢复该项默认).
- init: 恢复默认配置 (清除全部定制项).
- open: 打开配置文件所在目录.
"""

from __future__ import annotations

import click

from gdpm.cli.app import GdpmGroup
from gdpm.cli.config.init import config_init
from gdpm.cli.config.open import config_open
from gdpm.cli.config.set import config_set


@click.group(
    cls=GdpmGroup,
    examples=[
        (
            "gdpm config set default_engine steam-godot@4.7-stable",
            "Set default engine",
        ),
        ("gdpm config init", "Reset to defaults"),
        ("gdpm config open", "Open config directory"),
    ],
)
def config() -> None:
    """管理全局配置."""


config.add_command(config_set, "set")
config.add_command(config_init, "init")
config.add_command(config_open, "open")
