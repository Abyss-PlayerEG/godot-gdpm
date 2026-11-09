"""
插件数据模型

- 描述 Godot Asset Store 插件的概要与详情信息.

----

Notes
----
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

    Attributes
    ----
    slug : str
        插件 slug, 用于商店定位.
    name : str
        插件显示名称.
    description : str
        插件描述.
    author : str
        作者名称.
    publisher_slug : str
        发布者 slug.
    license : str
        许可证类型.
    store_url : str
        商店页面 URL.
    tags : list[str]
        标签列表.
    stars : int
        收藏/星标数.
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
    插件详情.

    在 Plugin 基础上补充主页, 仓库, 兼容版本与下载地址.

    ----

    Attributes
    ----
    homepage : str
        插件主页 URL.
    repository : str
        源码仓库 URL.
    godot_versions : list[str]
        兼容的 Godot 版本列表.
    latest_version : str
        最新版本号.
    download_url : str
        下载地址.
    """

    homepage: str = ""
    repository: str = ""
    godot_versions: list[str] = field(default_factory=list)
    latest_version: str = ""
    download_url: str = ""
