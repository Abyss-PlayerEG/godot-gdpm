"""
gdpm 全局常量

- 定义项目内共享的文件名, 目录名与外部 URL 等常量
- 提供 GitHub API 认证辅助函数.

----

Notes
----
- 项目文件名常量: 配置文件, 锁文件, 插件标签文件.
- 本地插件常量: 本地目录名与哈希清单.
- 仓库与 API URL 常量.
- get_github_token: 读取 GitHub token.
- get_github_headers: 构造 GitHub API 请求头.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_FILENAME = "gdproject.toml"
LOCK_FILENAME = "gdpm.lock"
TAG_FILENAME = "tag.gdpm"
LOCAL_TAG_PREFIX = "local+"
LOCAL_DIR_NAME = "gdpm-local"
HASHES_FILE = ".hashes"

REPO_URL = "https://github.com/Abyss-PlayerEG/godot-gdpm"
ISSUES_URL = "https://github.com/Abyss-PlayerEG/godot-gdpm/issues"
GITHUB_API_URL = "https://api.github.com/repos/Abyss-PlayerEG/godot-gdpm/"
GODOT_RELEASES_URL = "https://api.github.com/repos/godotengine/godot/releases"


def get_github_token() -> str:
    """
    从 ~/.gdpm/github_token.txt 读取 GitHub token.

    文件不存在或读取失败时返回空字符串.

    ----

    Returns
    ----
    str
        token 内容 (已去除首尾空白), 失败时为空字符串.
    """
    token_path = Path.home() / ".gdpm" / "github_token.txt"
    if not token_path.exists():
        return ""

    try:
        return token_path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def get_github_headers() -> dict[str, str]:
    """
    获取 GitHub API 请求头.

    有 token 时返回带 Authorization 的请求头, 否则返回空字典.

    ----

    Returns
    ----
    dict[str, str]
        HTTP 请求头字典.
    """
    token = get_github_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}
