"""
Godot Asset Store API 客户端包

- 封装 Asset Store 的搜索, 详情, 版本查询与下载接口.

----

Notes
----
- Plugin, PluginDetail: 插件数据模型.
- StoreClient: 基于 httpx 的异步 API 客户端.
- StoreProtocol: 依赖注入用的客户端接口.
"""

from gdpm.models.plugin import Plugin, PluginDetail
from gdpm.store.client import StoreClient
from gdpm.store.protocol import StoreProtocol

__all__ = ["Plugin", "PluginDetail", "StoreClient", "StoreProtocol"]
