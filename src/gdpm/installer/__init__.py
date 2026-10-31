"""
插件安装器, 负责插件的下载, 解压, 标记与卸载.

Plugin installer. Handle plugin downloading, extracting, tagging and
removal.

----

Note:
    - PluginManager: 插件安装管理器 / Plugin installation manager.
    - InstallerProtocol: 安装器接口协议 / Installer interface protocol.
"""

from gdpm.installer.manager import PluginManager
from gdpm.installer.protocol import InstallerProtocol

__all__ = ["InstallerProtocol", "PluginManager"]
