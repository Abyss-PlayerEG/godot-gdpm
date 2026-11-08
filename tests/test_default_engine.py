"""
全局默认引擎配置测试.

默认引擎已从 local-engines.json 迁移到 config.toml 的 [defaults].
覆盖: 读写往返, 旧位置自动迁移, 未设置返回空, 写入不破坏其他分段.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import platformdirs

from gdpm.config import global_config, local_engines
from gdpm.config.global_config import (
    get_default_engine,
    read_global_config,
    set_config_value,
    set_default_engine,
    unset_default_engine,
)

if TYPE_CHECKING:
    from pathlib import Path


def _patch_paths(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """把新旧配置路径全部隔离到临时目录, 绝不触碰真实环境."""
    config_path = tmp_path / "config.toml"
    engines_path = tmp_path / "local-engines.json"
    legacy_dir = tmp_path / "legacy"
    monkeypatch.setattr(global_config, "get_config_path", lambda: config_path)
    monkeypatch.setattr(local_engines, "get_config_path", lambda: engines_path)
    # platformdirs 旧位置也必须隔离, 否则会搬迁/删除真实 config.toml
    monkeypatch.setattr(
        platformdirs, "user_config_dir", lambda name="": str(legacy_dir)
    )
    return config_path, engines_path


def test_default_empty_when_nothing_configured(tmp_path: Path, monkeypatch) -> None:
    _patch_paths(tmp_path, monkeypatch)
    assert get_default_engine() == ""


def test_set_get_unset_roundtrip(tmp_path: Path, monkeypatch) -> None:
    config_path, _ = _patch_paths(tmp_path, monkeypatch)

    set_default_engine("steam-godot@4.7-stable")
    assert get_default_engine() == "steam-godot@4.7-stable"
    assert 'default_engine = "steam-godot@4.7-stable"' in config_path.read_text(
        encoding="utf-8"
    )

    unset_default_engine()
    assert get_default_engine() == ""


def test_legacy_default_migrates_from_local_engines(
    tmp_path: Path, monkeypatch
) -> None:
    """旧位置 local-engines.json 的 default 字段自动迁移到 config.toml."""
    config_path, engines_path = _patch_paths(tmp_path, monkeypatch)
    engines_path.write_text(
        json.dumps(
            {
                "engines": {"steam": {"path": "/x", "version": "4.7-stable"}},
                "default": "steam@4.7-stable",
            }
        ),
        encoding="utf-8",
    )

    assert get_default_engine() == "steam@4.7-stable"
    # 已写入新位置
    assert 'default_engine = "steam@4.7-stable"' in config_path.read_text(
        encoding="utf-8"
    )
    # 旧字段被清理, engines 注册表保留
    legacy = json.loads(engines_path.read_text(encoding="utf-8"))
    assert "default" not in legacy
    assert "steam" in legacy["engines"]


def test_write_preserves_other_sections(tmp_path: Path, monkeypatch) -> None:
    """行级写入: set_default_engine 不动其他段的自定义行."""
    _patch_paths(tmp_path, monkeypatch)
    set_config_value("language", "zh")

    set_default_engine("gdpm-godot@4.7-stable")

    config = read_global_config()
    assert config.default_engine == "gdpm-godot@4.7-stable"
    assert config.language == "zh"


def test_legacy_key_dropped_on_set(tmp_path: Path, monkeypatch) -> None:
    """新位置写入后, 即便不经过 get 迁移路径, 旧字段也被清理."""
    _, engines_path = _patch_paths(tmp_path, monkeypatch)
    engines_path.write_text(
        json.dumps({"engines": {}, "default": "old@1.0-stable"}), encoding="utf-8"
    )

    set_default_engine("new@2.0-stable")

    legacy = json.loads(engines_path.read_text(encoding="utf-8"))
    assert "default" not in legacy
    assert get_default_engine() == "new@2.0-stable"


def test_single_key_write_touches_only_target(tmp_path: Path, monkeypatch) -> None:
    """行级手术: 一次写入只出现目标键, 其他默认键不得被材料化."""
    config_path, _ = _patch_paths(tmp_path, monkeypatch)

    set_default_engine("steam-godot@4.7-stable")
    text = config_path.read_text(encoding="utf-8")

    assert 'default_engine = "steam-godot@4.7-stable"' in text
    assert "[defaults]" in text
    # 其他键不得出现 (用户反馈: set 后文件冒出没设过的键)
    for absent in ("godot_path", "parallel_downloads", "[store]", "[cache]", "[ui]"):
        assert absent not in text


def test_unset_removes_line(tmp_path: Path, monkeypatch) -> None:
    """移除唯一定制项后删行; 文件因此无内容时删除文件."""
    config_path, _ = _patch_paths(tmp_path, monkeypatch)

    set_default_engine("steam-godot@4.7-stable")
    assert config_path.exists()

    unset_default_engine()
    assert not config_path.exists()
    assert get_default_engine() == ""


def test_upsert_creates_missing_section(tmp_path: Path, monkeypatch) -> None:
    """目标段不存在时新建段, 其余段不被创建."""
    config_path, _ = _patch_paths(tmp_path, monkeypatch)

    set_config_value("language", "zh")
    text = config_path.read_text(encoding="utf-8")

    assert "[ui]" in text
    assert 'language = "zh"' in text
    assert "[defaults]" not in text
    assert "[cache]" not in text
