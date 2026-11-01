"""
gdpm 数据模型

- 零外部依赖的纯数据结构集合, 描述插件, 依赖, 锁文件条目与版本.

----

Notes
----
- Dependency: 依赖项模型, 含版本约束与来源信息.
- LockEntry: 锁文件条目模型.
- Plugin / PluginDetail: 商店插件概要与详情模型.
- Version / VersionConstraint: 版本与版本约束模型.
"""

from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.models.plugin import Plugin, PluginDetail
from gdpm.models.version import Version, VersionConstraint

__all__ = [
    "Dependency",
    "LockEntry",
    "Plugin",
    "PluginDetail",
    "Version",
    "VersionConstraint",
]
