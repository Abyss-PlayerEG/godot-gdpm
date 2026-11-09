"""
全局配置管理

- 读写 gdpm 全局配置文件 config.toml, 管理跨项目共享的默认设置.
- 配置为定制清单: 文件只含你设过的行; 写入是行级手术 —— 只动目标键
  所在行, 其余行 (含手写行与等于默认值的行) 一律原样保留.

----

Examples
----
配置文件只存定制行, 例如:

    [defaults]
    default_engine = ""

    [ui]
    language = "zh"

可设置键 (仅已实现消费方的键):
    [defaults] parallel_downloads / default_engine / godot_mirror
    [cache]    dir
    [ui]       language

历史字段 godot_path / addons_dir / store_url 仍会被读取, 但暂无消费方,
已从可设置面移除 (2026-11: 展示与接受只覆盖已实现部分).

Notes
----
- GlobalConfig: 全局配置数据类.
- get_config_path: 获取配置文件路径 (~/.gdpm/config.toml).
- read_global_config: 读取全局配置 (缺键回退默认, 兼容任意稀疏度的文件).
- set_config_value: 单键行级写入/删除, 目标键之外的内容原样保留.
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
    godot_mirror : str
        Godot 引擎下载镜像 base URL (如自建 Cloudflare Worker),
        空表示走官方 downloads.godotengine.org.
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
    godot_mirror: str = ""
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


# 配置键布局: 键 → (TOML 段名, 段内键名, 是否字符串值)
# 同时是 config set 的合法键表 (CONFIG_FIELDS 由它派生)
# 只收录已有消费方的键: godot_path / addons_dir / store_url 暂无实现, 不可设置
_KEY_LAYOUT: dict[str, tuple[str, str, bool]] = {
    "parallel_downloads": ("defaults", "parallel_downloads", False),
    "default_engine": ("defaults", "default_engine", True),
    "godot_mirror": ("defaults", "godot_mirror", True),
    "cache_dir": ("cache", "dir", True),
    "language": ("ui", "language", True),
}

# 全局配置的可设置字段 (GlobalConfig 字段名, 即 config set 的合法键)
CONFIG_FIELDS: tuple[str, ...] = tuple(_KEY_LAYOUT)


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
        godot_mirror=defaults.get("godot_mirror", ""),
        cache_dir=cache.get("dir", ""),
        store_url=store.get("base_url", "https://store.godotengine.org/api/v1"),
        language=ui.get("language", "en"),
    )


def set_config_value(key: str, value: str | int | None) -> None:
    """
    单键行级写入: 只新增/修改/删除目标键所在行, 其余内容原样保留.

    行级手术模型 (2026-11, 取代全量重建): 不基于字段对象重写文件,
    手写行、等于默认值的历史行与未涉及的段落一律不动 —— set 一条
    不会让文件里冒出其他键.

    - value 为 None 或空串: 删除该键行; 所在段因此变空时连段头一并
      删除; 文件因此无任何内容时删除文件 (回到"未配置"状态)
    - value 非空: 段内原位替换 (历史重复键行去重), 段不存在则新建段

    ----

    Parameters
    ----
    key : str
        配置键 (CONFIG_FIELDS 之一).
    value : str | int | None
        新值; None/空串表示删除该键行.

    Returns
    ----
    None
        无.

    Raises
    ----
    ValueError
        key 不是合法配置键.
    """
    if key not in _KEY_LAYOUT:
        raise ValueError(f"unknown config key: {key}")
    section, toml_key, quoted = _KEY_LAYOUT[key]
    header = f"[{section}]"

    path = get_config_path()
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def is_key_line(line: str) -> bool:
        head, sep, _ = line.partition("=")
        return sep != "" and head.strip() == toml_key

    # 定位目标段: [段头行, 下一个段头前)
    start = end = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i
            end = i + 1
            while end < len(lines) and not (
                lines[end].strip().startswith("[") and lines[end].strip().endswith("]")
            ):
                end += 1
            break

    if value is None or value == "":
        if start is None or end is None:
            return
        block = lines[start + 1 : end]
        remaining = [line for line in block if not is_key_line(line)]
        has_assignment = any(
            line.strip() and not line.strip().startswith("#") and "=" in line
            for line in remaining
        )
        if has_assignment:
            lines[start + 1 : end] = remaining
        else:
            # 段内已无赋值行: 整段 (段头+残留空行/注释) 移除
            del lines[start:end]
    else:
        rendered = f'{toml_key} = "{value}"' if quoted else f"{toml_key} = {value}"
        if start is not None and end is not None:
            block = lines[start + 1 : end]
            key_idx = next(
                (k for k, line in enumerate(block) if is_key_line(line)), None
            )
            if key_idx is not None:
                # 原位替换, 并清理历史重复键行
                new_block: list[str] = []
                replaced = False
                for line in block:
                    if is_key_line(line):
                        if not replaced:
                            new_block.append(rendered)
                            replaced = True
                    else:
                        new_block.append(line)
                lines[start + 1 : end] = new_block
            else:
                # 插到段尾空行之前, 保持"条目 + 空行分隔"的排版
                insert_at = len(block)
                while insert_at > 0 and not block[insert_at - 1].strip():
                    insert_at -= 1
                lines[start + 1 : end] = [
                    *block[:insert_at],
                    rendered,
                    *block[insert_at:],
                ]
        else:
            # 段不存在: 文件尾新建段
            if lines and lines[-1].strip():
                lines.append("")
            lines.extend([header, rendered, ""])

    if not any(line.strip() for line in lines):
        # 无任何内容: 删除文件, 回到"未配置"状态
        path.unlink(missing_ok=True)
        return
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

    行级写入 config.toml 的 [defaults] default_engine (空串删除该行),
    并清理旧位置残留字段.

    ----

    Parameters
    ----
    engine_id : str
        引擎 ID, 如 'steam-godot@4.7-stable'; 空串表示清除设置.
    """
    set_config_value("default_engine", engine_id)
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
