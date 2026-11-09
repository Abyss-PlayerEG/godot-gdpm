"""
本地引擎配置管理

- 维护 ~/.gdpm/local-engines.json, 记录用户手动注册的本地 Godot 引擎.
- 默认引擎已迁移至全局 config.toml 的 [defaults] default_engine,
  旧文件中的 default 字段由 get_default_engine 读取时自动迁移清理.

----

Examples
----
配置文件结构:

    {
      "engines": {
        "steam": { "path": "...", "version": "4.7-stable" }
      }
    }

Notes
----
- LocalEngine: 本地引擎条目.
- load_local_engines: 读取全部本地引擎.
- save_local_engines: 保存全部本地引擎.
- add_local_engine: 注册本地引擎.
- remove_local_engine: 移除本地引擎.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LocalEngine:
    """
    本地 Godot 引擎条目

    记录本地 Godot 引擎的路径与版本信息.

    ----

    Attributes
    ----
    path : str
        引擎可执行文件或目录路径.
    version : str
        引擎版本标签, 如 4.7-stable.
    """

    path: str
    version: str = ""


def get_config_path() -> Path:
    """获取本地引擎配置文件路径."""
    return Path.home() / ".gdpm" / "local-engines.json"


def load_config() -> dict[str, object]:
    """
    加载原始配置字典.

    文件不存在或 JSON 非法时返回空字典.

    ----

    Returns
    ----
    dict[str, object]
        解析后的配置字典.
    """
    path = get_config_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}
    except json.JSONDecodeError, TypeError:
        return {}


def save_config(config: dict[str, object]) -> None:
    """
    保存原始配置字典.

    以缩进 2 的 JSON 格式写入, 保留非 ASCII 字符.

    ----

    Parameters
    ----
    config : dict[str, object]
        要写入的配置字典.
    """
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_local_engines() -> dict[str, LocalEngine]:
    """
    加载本地引擎配置.

    兼容旧格式 (值为纯路径字符串) 与新格式 (值为对象).

    ----

    Returns
    ----
    dict[str, LocalEngine]
        以引擎名为键的 LocalEngine 字典.
    """
    config = load_config()
    engines_raw = config.get("engines", {})
    engines = engines_raw if isinstance(engines_raw, dict) else {}

    result: dict[str, LocalEngine] = {}
    for name, value in engines.items():
        if isinstance(value, str):
            # 旧格式: 仅包含路径字符串
            result[name] = LocalEngine(path=value)
        elif isinstance(value, dict):
            result[name] = LocalEngine(
                path=value.get("path", ""),
                version=value.get("version", ""),
            )
    return result


def save_local_engines(engines: dict[str, LocalEngine]) -> None:
    """
    保存本地引擎配置.

    仅覆盖 engines 键, 保留配置中的其他字段 (如 default).

    ----

    Parameters
    ----
    engines : dict[str, LocalEngine]
        以引擎名为键的 LocalEngine 字典.
    """
    config = load_config()
    config["engines"] = {
        name: {"path": eng.path, "version": eng.version}
        for name, eng in engines.items()
    }
    save_config(config)


def add_local_engine(name: str, path: str, version: str = "") -> None:
    """
    注册本地引擎.

    同名引擎会被覆盖.

    ----

    Parameters
    ----
    name : str
        引擎名称.
    path : str
        引擎可执行文件或目录路径.
    version : str, optional
        引擎版本标签, 如 4.7-stable.
    """
    engines = load_local_engines()
    engines[name] = LocalEngine(path=path, version=version)
    save_local_engines(engines)


def remove_local_engine(name: str) -> bool:
    """
    移除本地引擎.

    按名称从本地引擎配置中删除对应条目.

    ----

    Parameters
    ----
    name : str
        引擎名称.

    Returns
    ----
    bool
        移除成功返回 True, 未找到返回 False.
    """
    engines = load_local_engines()
    if name not in engines:
        return False
    del engines[name]
    save_local_engines(engines)
    return True


def get_local_engine(name: str) -> LocalEngine | None:
    """
    按名称获取本地引擎.

    从本地引擎配置中查找指定名称的条目.

    ----

    Parameters
    ----
    name : str
        引擎名称.

    Returns
    ----
    LocalEngine | None
        LocalEngine 实例, 未找到时返回 None.
    """
    return load_local_engines().get(name)
