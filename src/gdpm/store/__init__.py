"""
Godot Asset Store API 客户端包, 封装 Asset Store 的搜索, 详情, 版本查询与下载接口.

Godot Asset Store API client package. Wrap the Asset Store search, detail,
version and download APIs.

----

Note:
    - Plugin, PluginDetail: 插件数据模型 / Plugin data models.
    - StoreClient: 基于 httpx 的异步 API 客户端 / Async httpx-based API client.
    - StoreProtocol: 依赖注入用的客户端接口 / Client interface for injection.
"""

from gdpm.models.plugin import Plugin, PluginDetail
from gdpm.store.client import StoreClient
from gdpm.store.protocol import StoreProtocol

__all__ = ["Plugin", "PluginDetail", "StoreClient", "StoreProtocol"]
