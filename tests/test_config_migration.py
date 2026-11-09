"""
config.toml 位置迁移测试.

早期版本按 platformdirs 规范存放, 现统一到 ~/.gdpm/config.toml.
搬迁必须保内容、删旧文件, 且新位置已有文件时绝不覆盖.
"""

from __future__ import annotations

from pathlib import Path

import platformdirs

from gdpm.config import global_config
from gdpm.config.global_config import (
    GlobalConfig,
    read_global_config,
    set_config_value,
)


def _patch_paths(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """新位置与 platformdirs 旧位置都指到临时目录."""
    new_path = tmp_path / "config.toml"
    old_dir = tmp_path / "legacy"
    monkeypatch.setattr(global_config, "get_config_path", lambda: new_path)
    monkeypatch.setattr(platformdirs, "user_config_dir", lambda name="": str(old_dir))
    return new_path, old_dir / "config.toml"


def test_migrates_from_legacy_platformdirs_location(
    tmp_path: Path, monkeypatch
) -> None:
    new_path, old_path = _patch_paths(tmp_path, monkeypatch)
    old_path.parent.mkdir(parents=True)
    old_path.write_text(
        '[defaults]\ndefault_engine = "steam-godot@4.7-stable"\n',
        encoding="utf-8",
    )

    config = read_global_config()

    # 内容搬到新位置并可正常解析
    assert config.default_engine == "steam-godot@4.7-stable"
    assert new_path.exists()
    # 旧文件被删除, 不留双配置源
    assert not old_path.exists()


def test_existing_new_config_never_clobbered(tmp_path: Path, monkeypatch) -> None:
    new_path, old_path = _patch_paths(tmp_path, monkeypatch)
    set_config_value("default_engine", "new@2.0-stable")
    old_path.parent.mkdir(parents=True)
    old_path.write_text(
        '[defaults]\ndefault_engine = "old@1.0-stable"\n', encoding="utf-8"
    )

    config = read_global_config()

    assert config.default_engine == "new@2.0-stable"
    assert new_path.exists()
    # 新位置已存在时旧文件原样保留 (不覆盖)
    assert old_path.exists()


def test_no_legacy_file_returns_defaults(tmp_path: Path, monkeypatch) -> None:
    _patch_paths(tmp_path, monkeypatch)
    config = read_global_config()
    assert config.default_engine == ""
    assert config.addons_dir == "addons"


def test_default_cache_location_is_user_dir() -> None:
    """缓存默认在 ~/.gdpm 专用用户目录 (npm ~/.npm / Maven ~/.m2 同风格)."""
    assert GlobalConfig().cache_dir == str(Path.home() / ".gdpm" / "cache")
