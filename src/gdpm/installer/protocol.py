"""
安装器协议, 定义插件安装器的抽象接口, 便于依赖注入与测试替换.

----

Note:
    - InstallerProtocol: 安装器接口协议.
"""

from __future__ import annotations

from typing import Protocol


class InstallerProtocol(Protocol):
    """
    安装器接口协议, 实现类需提供插件安装, 卸载与状态查询能力.
    """

    def install(self, name: str, version: str) -> None:
        """
        安装指定版本的插件.

        ----

        Args:
            name: 插件名称.
            version: 插件版本号.
        """
        ...

    def remove(self, name: str) -> None:
        """
        卸载插件.

        ----

        Args:
            name: 插件名称.
        """
        ...

    def is_installed(self, name: str) -> bool:
        """
        判断插件是否已安装.

        ----

        Args:
            name: 插件名称.

        Returns:
            已安装返回 True.
        """
        ...

    def installed_version(self, name: str) -> str | None:
        """
        获取已安装插件的版本号.

        ----

        Args:
            name: 插件名称.

        Returns:
            版本号, 未安装时返回 None.
        """
        ...
