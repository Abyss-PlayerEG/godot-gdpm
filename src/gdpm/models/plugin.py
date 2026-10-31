"""
插件数据模型. 描述 Godot Asset Store 插件的概要与详情信息.

Describe summary and detail info of Godot Asset Store plugins.

----

Note:
    - Plugin: 商店插件概要 / Store plugin summary.
    - PluginDetail: 插件详情, 继承 Plugin 并补充下载与兼容信息 /
        Plugin detail, extends Plugin with download and compatibility info.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Plugin:
    """
    商店插件概要.

    Store plugin summary.

    ----

    Note:
        - slug: 插件 slug, 用于商店定位 / Plugin slug used for store lookup.
        - name: 插件显示名称 / Plugin display name.
        - description: 插件描述 / Plugin description.
        - author: 作者名称 / Author name.
        - publisher_slug: 发布者 slug / Publisher slug.
        - license: 许可证类型 / License type.
        - store_url: 商店页面 URL / Store page URL.
        - tags: 标签列表 / List of tags.
        - stars: 收藏/星标数 / Number of stars.
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

    Plugin detail. Extends Plugin with homepage, repository,
    compatible versions, and download URL.

    ----

    Note:
        - homepage: 插件主页 URL / Plugin homepage URL.
        - repository: 源码仓库 URL / Source repository URL.
        - godot_versions: 兼容的 Godot 版本列表 /
            List of compatible Godot versions.
        - latest_version: 最新版本号 / Latest version string.
        - download_url: 下载地址 / Download URL.
    """

    homepage: str = ""
    repository: str = ""
    godot_versions: list[str] = field(default_factory=list)
    latest_version: str = ""
    download_url: str = ""
