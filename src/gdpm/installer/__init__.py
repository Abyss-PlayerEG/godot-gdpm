"""
插件安装器, 负责插件的下载, 解压, 标记与卸载.

----

Note:
    - PluginManager: 插件安装管理器.
    - InstallerProtocol: 安装器接口协议.
"""

from gdpm.installer.manager import PluginManager
from gdpm.installer.protocol import InstallerProtocol

__all__ = ["InstallerProtocol", "PluginManager"]
