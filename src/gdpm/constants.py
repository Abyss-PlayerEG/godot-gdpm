"""
gdpm 全局常量

- 定义项目内共享的文件名, 目录名与外部 URL 等常量.

----

Notes
----
- 项目文件名常量: 配置文件, 锁文件, 插件标签文件.
- 本地插件常量: 本地目录名与哈希清单.
- 仓库与 API URL 常量.
- Godot 下载接口 base 常量: 官方接口与自建镜像.
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
VERSIONS_JSON_URL = "https://godotengine.org/versions.json"

# Godot 引擎下载接口 base (双通道写死, 无配置项):
# 官方优先, 走不通时 install 自动切换自建镜像
GODOT_DOWNLOAD_BASE = "https://downloads.godotengine.org"
GODOT_DOWNLOAD_MIRROR = "https://godot-download.playereg.top"
