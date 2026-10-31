"""
CLI 命令接口. 本模块是 gdpm.cli 包的入口, 对外暴露命令行主函数 main.

----

Note:
    - main: click 根命令组, gdpm 全部子命令的挂载点.
"""

from gdpm.cli.app import main

__all__ = ["main"]
