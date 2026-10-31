"""
全局配置管理, 读写 gdpm 全局配置文件 config.toml, 管理跨项目共享的默认设置.

----

example:
    配置文件结构:

        [defaults]
        godot_path = "godot"
        addons_dir = "addons"
        parallel_downloads = 4

        [store]
        base_url = "https://store.godotengine.org/api/v1"

        [cache]
        dir = "~/.gdpm/cache"

----

Note:
    - GlobalConfig: 全局配置数据类.
    - get_config_path: 获取配置文件路径.
    - read_global_config: 读取全局配置.
    - write_global_config: 写入全局配置.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import platformdirs


@dataclass
class GlobalConfig:
    """
    全局配置数据类.

    ----

    Note:
        - godot_path: Godot 可执行文件路径或命令名.
        - addons_dir: 插件安装目录名.
        - parallel_downloads: 并行下载数.
        - cache_dir: 下载缓存目录.
        - store_url: Godot Asset Store API 基础地址.
    """

    godot_path: str = "godot"
    addons_dir: str = "addons"
    parallel_downloads: int = 4
    cache_dir: str = ""
    store_url: str = "https://store.godotengine.org/api/v1"

    def __post_init__(self) -> None:
        """
        初始化后处理, 若 cache_dir 为空, 回退到 ~/.gdpm/cache.
        """
        if not self.cache_dir:
            self.cache_dir = str(Path.home() / ".gdpm" / "cache")


def get_config_path() -> Path:
    """获取全局配置文件路径."""
    return Path(platformdirs.user_config_dir("gdpm")) / "config.toml"


def read_global_config() -> GlobalConfig:
    """
    读取全局配置, 配置文件不存在时返回默认配置.

    Returns:
        GlobalConfig 实例.
    """
    path = get_config_path()
    if not path.exists():
        return GlobalConfig()

    with open(path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    defaults = data.get("defaults", {})
    store = data.get("store", {})
    cache = data.get("cache", {})

    return GlobalConfig(
        godot_path=defaults.get("godot_path", "godot"),
        addons_dir=defaults.get("addons_dir", "addons"),
        parallel_downloads=defaults.get("parallel_downloads", 4),
        cache_dir=cache.get("dir", ""),
        store_url=store.get("base_url", "https://store.godotengine.org/api/v1"),
    )


def write_global_config(config: GlobalConfig) -> None:
    """
    写入全局配置, 按 [defaults]/[store]/[cache] 三节序列化为 TOML 并覆盖写入.

    ----

    Args:
        config: 要持久化的全局配置.
    """
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("[defaults]")
    lines.append(f'godot_path = "{config.godot_path}"')
    lines.append(f'addons_dir = "{config.addons_dir}"')
    lines.append(f"parallel_downloads = {config.parallel_downloads}")
    lines.append("")
    lines.append("[store]")
    lines.append(f'base_url = "{config.store_url}"')
    lines.append("")
    lines.append("[cache]")
    lines.append(f'dir = "{config.cache_dir}"')
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
