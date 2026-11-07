"""
全局配置管理

- 读写 gdpm 全局配置文件 config.toml, 管理跨项目共享的默认设置.
- 配置为全量材料化: 所有键显式落盘, 文件即完整可编辑模板.

----

Examples
----
配置文件写出全部键, 例如:

    [defaults]
    godot_path = "godot"
    addons_dir = "addons"
    parallel_downloads = 4
    default_engine = ""

    [store]
    base_url = "https://store.godotengine.org/api/v1"

    [cache]
    dir = "/home/user/.gdpm/cache"

    [ui]
    language = "en"

可配置键:
    [defaults] godot_path / addons_dir / parallel_downloads / default_engine
    [store]    base_url
    [cache]    dir
    [ui]       language

Notes
----
- GlobalConfig: 全局配置数据类.
- get_config_path: 获取配置文件路径 (~/.gdpm/config.toml).
- read_global_config: 读取全局配置 (缺键回退默认, 兼容历史稀疏文件).
- write_global_config: 全量写入全局配置 (所有键显式落盘).
- get_default_engine: 获取全局默认引擎 ID (含旧位置自动迁移).
- set_default_engine: 设置全局默认引擎 ID.
- unset_default_engine: 移除全局默认引擎设置.
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
    全局配置数据类

    gdpm 跨项目共享的默认设置, 对应配置文件 config.toml.

    ----

    Attributes
    ----
    godot_path : str
        Godot 可执行文件路径或命令名.
    addons_dir : str
        插件安装目录名.
    parallel_downloads : int
        并行下载数.
    default_engine : str
        全局默认引擎 ID, 形如 'steam-godot@4.7-stable', 空表示未设置.
    cache_dir : str
        下载缓存目录.
    store_url : str
        Godot Asset Store API 基础地址.
    language : str
        帮助文案语言 (en/zh), 对应 [ui] language.
    """

    godot_path: str = "godot"
    addons_dir: str = "addons"
    parallel_downloads: int = 4
    default_engine: str = ""
    cache_dir: str = ""
    store_url: str = "https://store.godotengine.org/api/v1"
    language: str = "en"

    def __post_init__(self) -> None:
        """
        初始化后处理.

        若 cache_dir 为空, 回退到 ~/.gdpm/cache.
        """
        if not self.cache_dir:
            self.cache_dir = str(Path.home() / ".gdpm" / "cache")


def get_config_path() -> Path:
    """
    获取全局配置文件路径 (~/.gdpm/config.toml).

    与 gdpm 的其他运行时数据 (engines/cache/local-engines) 同居一处.
    """
    return Path.home() / ".gdpm" / "config.toml"


# 全局配置的可设置字段 (GlobalConfig 字段名, 即 config set 的合法键)
CONFIG_FIELDS: tuple[str, ...] = (
    "godot_path",
    "addons_dir",
    "parallel_downloads",
    "default_engine",
    "store_url",
    "cache_dir",
    "language",
)


def _migrate_legacy_config() -> None:
    """
    一次性搬迁: platformdirs 旧位置的 config.toml -> ~/.gdpm/config.toml.

    早期版本按 platformdirs 规范存放 (macOS 为
    ~/Library/Application Support/gdpm/), 迁到统一位置后删除旧文件,
    避免出现双配置源. 搬迁失败时静默跳过, 下次读取重试.
    """
    new_path = get_config_path()
    if new_path.exists():
        return
    try:
        old_path = Path(platformdirs.user_config_dir("gdpm")) / "config.toml"
        if old_path.exists() and old_path != new_path:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.write_bytes(old_path.read_bytes())
            old_path.unlink()
    except OSError:
        pass


def read_global_config() -> GlobalConfig:
    """
    读取全局配置.

    配置文件不存在时返回默认配置.

    ----

    Returns
    ----
    GlobalConfig
        全局配置实例.
    """
    path = get_config_path()
    # 新位置缺失时先尝试从 platformdirs 旧位置一次性搬迁
    _migrate_legacy_config()
    if not path.exists():
        return GlobalConfig()

    with open(path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    defaults = data.get("defaults", {})
    store = data.get("store", {})
    cache = data.get("cache", {})
    ui = data.get("ui", {})

    return GlobalConfig(
        godot_path=defaults.get("godot_path", "godot"),
        addons_dir=defaults.get("addons_dir", "addons"),
        parallel_downloads=defaults.get("parallel_downloads", 4),
        default_engine=defaults.get("default_engine", ""),
        cache_dir=cache.get("dir", ""),
        store_url=store.get("base_url", "https://store.godotengine.org/api/v1"),
        language=ui.get("language", "en"),
    )


def write_global_config(config: GlobalConfig) -> None:
    """
    全量写入全局配置.

    所有键显式落盘, 文件永远是完整可编辑模板 (全量材料化, 2026-11 由
    稀疏方案改为本模型): 便于查看全部可配置项与手工编辑, init 即写出
    完整默认配置. 读取端缺键仍回退默认, 兼容历史稀疏文件.

    注意:
    - 本函数基于 GlobalConfig 字段重建文件, 手写的未知键会在
      下次写入时丢失.
    - 默认值随版本演进时, 旧文件中物化的旧默认值会钉住用户配置,
      调整默认值的版本需配迁移 (删除等于旧默认值的行).

    ----

    Parameters
    ----
    config : GlobalConfig
        要持久化的全局配置.

    Returns
    ----
    None
        无.
    """
    path = get_config_path()
    sections: list[tuple[str, list[str]]] = [
        (
            "[defaults]",
            [
                f'godot_path = "{config.godot_path}"',
                f'addons_dir = "{config.addons_dir}"',
                f"parallel_downloads = {config.parallel_downloads}",
                f'default_engine = "{config.default_engine}"',
            ],
        ),
        ("[store]", [f'base_url = "{config.store_url}"']),
        ("[cache]", [f'dir = "{config.cache_dir}"']),
        ("[ui]", [f'language = "{config.language}"']),
    ]

    lines: list[str] = []
    for header, entries in sections:
        lines.append(header)
        lines.extend(entries)
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_default_engine() -> str:
    """
    获取全局默认引擎 ID.

    优先读 config.toml 的 [defaults] default_engine; 若为空且旧位置
    local-engines.json 仍残留 default 字段, 自动迁移过去.

    ----

    Returns
    ----
    str
        引擎 ID (形如 'steam-godot@4.7-stable'), 未设置时为空字符串.
    """
    config = read_global_config()
    if config.default_engine:
        return config.default_engine

    # 旧版位置迁移: local-engines.json 的 default 字段
    from gdpm.config.local_engines import load_config

    legacy = load_config().get("default")
    if legacy:
        set_default_engine(str(legacy))
        return str(legacy)
    return ""


def set_default_engine(engine_id: str) -> None:
    """
    设置全局默认引擎 ID.

    写入 config.toml 的 [defaults] default_engine, 并清理旧位置残留字段.

    ----

    Parameters
    ----
    engine_id : str
        引擎 ID, 如 'steam-godot@4.7-stable'; 空串表示清除设置.
    """
    config = read_global_config()
    config.default_engine = engine_id
    write_global_config(config)
    _drop_legacy_default()


def unset_default_engine() -> None:
    """移除全局默认引擎设置 (等价于 set_default_engine 空串)."""
    set_default_engine("")


def _drop_legacy_default() -> None:
    """
    清理旧位置残留的 default 字段.

    迁移完成后 local-engines.json 只保留 engines 注册表,
    避免两个位置同时存在产生歧义.
    """
    from gdpm.config.local_engines import load_config, save_config

    legacy = load_config()
    if "default" in legacy:
        legacy.pop("default", None)
        save_config(legacy)
