"""
gdpm 全局常量

- 定义项目内共享的文件名, 目录名与外部 URL 等常量.

----

Notes
----
- 项目文件名常量: 配置文件, 锁文件, 插件标签文件.
- 本地插件常量: 本地目录名与哈希清单.
- 仓库与 API URL 常量.
- Godot 下载镜像常量 (客户端唯一通道).
"""

from __future__ import annotations

CONFIG_FILENAME = "gdproject.toml"
LOCK_FILENAME = "gdpm.lock"
TAG_FILENAME = "tag.gdpm"
LOCAL_TAG_PREFIX = "local+"
LOCAL_DIR_NAME = "gdpm-local"
HASHES_FILE = ".hashes"

DEVELOPER = "playereg"
REPO_URL = "https://github.com/Abyss-PlayerEG/godot-gdpm"
WEBSITE_REPO_URL = "https://github.com/Abyss-PlayerEG/gdpm-website"
OFFICIAL_SITE_URL = "https://gdpm.playereg.top"
ISSUES_URL = "https://github.com/Abyss-PlayerEG/godot-gdpm/issues"
GITHUB_API_URL = "https://api.github.com/repos/Abyss-PlayerEG/godot-gdpm/"
# Godot 下载镜像 (gdpm 唯一通道, 写死无配置项):
# 引擎下载与 versions.json 均走此地址, 官方接口不在客户端保留
GODOT_DOWNLOAD_MIRROR = "https://godot-download.playereg.top"
