"""
插件数据模型. 描述 Godot Asset Store 插件的概要与详情信息.

----

Note:
    - Plugin: 商店插件概要.
    - PluginDetail: 插件详情, 继承 Plugin 并补充下载与兼容信息.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Plugin:
    """
    商店插件概要.

    ----

    Note:
        - slug: 插件 slug, 用于商店定位.
        - name: 插件显示名称.
        - description: 插件描述.
        - author: 作者名称.
        - publisher_slug: 发布者 slug.
        - license: 许可证类型.
        - store_url: 商店页面 URL.
        - tags: 标签列表.
        - stars: 收藏/星标数.
    """

    slug: str
    name: str
    description: str
    author: str
    publisher_slug: str
    license: str
    store_url: str = ""
    tags: list[str] = field(default_factory=list)
    stars: int = 0


@dataclass(frozen=True)
class PluginDetail(Plugin):
    """
    插件详情. 在 Plugin 基础上补充主页, 仓库, 兼容版本与下载地址.

    ----

    Note:
        - homepage: 插件主页 URL.
        - repository: 源码仓库 URL.
        - godot_versions: 兼容的 Godot 版本列表.
        - latest_version: 最新版本号.
        - download_url: 下载地址.
    """

    homepage: str = ""
    repository: str = ""
    godot_versions: list[str] = field(default_factory=list)
    latest_version: str = ""
    download_url: str = ""
