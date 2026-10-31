"""
安装器协议, 定义插件安装器的抽象接口, 便于依赖注入与测试替换.

Installer protocol. Define the abstract installer interface for
dependency injection and test doubles.

----

Note:
    - InstallerProtocol: 安装器接口协议 / Installer interface protocol.
"""

from __future__ import annotations

from typing import Protocol


class InstallerProtocol(Protocol):
    """
    安装器接口协议, 实现类需提供插件安装, 卸载与状态查询能力.

    Installer interface protocol. Implementations provide plugin
    install, remove and status query capabilities.
    """

    def install(self, name: str, version: str) -> None:
        """
        安装指定版本的插件.

        Install a plugin at the given version.

        ----

        Args:
            name: 插件名称 / Plugin name.
            version: 插件版本号 / Plugin version.
        """
        ...

    def remove(self, name: str) -> None:
        """
        卸载插件.

        Remove a plugin.

        ----

        Args:
            name: 插件名称 / Plugin name.
        """
        ...

    def is_installed(self, name: str) -> bool:
        """
        判断插件是否已安装.

        Check whether a plugin is installed.

        ----

        Args:
            name: 插件名称 / Plugin name.

        Returns:
            已安装返回 True / True if the plugin is installed.
        """
        ...

    def installed_version(self, name: str) -> str | None:
        """
        获取已安装插件的版本号.

        Get the installed version of a plugin.

        ----

        Args:
            name: 插件名称 / Plugin name.

        Returns:
            版本号, 未安装时返回 None /
                Version string, or None if not installed.
        """
        ...
