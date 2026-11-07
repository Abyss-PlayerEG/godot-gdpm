"""
gdpm config 命令测试.

覆盖: set 键名校验与整数校验, 空值重置 (稀疏删除), init 重置与幂等,
open 的三平台目录打开命令分发.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from gdpm.cli.config.init import config_init
from gdpm.cli.config.open import config_open
from gdpm.cli.config.set import config_set
from gdpm.config import global_config

if TYPE_CHECKING:
    from pathlib import Path


def _patch(tmp_path: Path, monkeypatch) -> Path:
    """配置路径隔离到临时目录 (含 init/open 的直接绑定)."""
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(global_config, "get_config_path", lambda: config_path)
    monkeypatch.setattr("gdpm.cli.config.init.get_config_path", lambda: config_path)
    monkeypatch.setattr("gdpm.cli.config.open.get_config_path", lambda: config_path)
    return config_path


def test_set_string_key_writes_sparsely(tmp_path: Path, monkeypatch) -> None:
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        config_set, ["default_engine", "steam-godot@4.7-stable"]
    )

    assert result.exit_code == 0
    text = config_path.read_text(encoding="utf-8")
    assert 'default_engine = "steam-godot@4.7-stable"' in text
    # 稀疏: 默认值不落盘
    assert "godot_path" not in text
    assert "[store]" not in text
    assert "reset to default" not in result.output


def test_set_integer_valid(tmp_path: Path, monkeypatch) -> None:
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_set, ["parallel_downloads", "8"])

    assert result.exit_code == 0
    assert "parallel_downloads = 8" in config_path.read_text(encoding="utf-8")


def test_set_integer_invalid_rejected(tmp_path: Path, monkeypatch) -> None:
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_set, ["parallel_downloads", "abc"])

    assert "positive integer" in result.output
    assert not config_path.exists()


def test_set_zero_rejected(tmp_path: Path, monkeypatch) -> None:
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_set, ["parallel_downloads", "0"])

    assert "positive integer" in result.output
    assert not config_path.exists()


def test_set_unknown_key_lists_options(tmp_path: Path, monkeypatch) -> None:
    _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_set, ["no_such_key", "x"])

    assert "Unknown config key" in result.output
    # 列出全部合法键
    for key in ("default_engine", "parallel_downloads", "store_url"):
        assert key in result.output


def test_set_empty_value_resets_and_deletes(tmp_path: Path, monkeypatch) -> None:
    config_path = _patch(tmp_path, monkeypatch)
    CliRunner().invoke(config_set, ["default_engine", "x@1.0-stable"])
    assert config_path.exists()

    result = CliRunner().invoke(config_set, ["default_engine", ""])

    assert "reset to default" in result.output
    assert not config_path.exists()


def test_init_resets_customizations(tmp_path: Path, monkeypatch) -> None:
    config_path = _patch(tmp_path, monkeypatch)
    CliRunner().invoke(config_set, ["default_engine", "x@1.0-stable"])
    assert config_path.exists()

    result = CliRunner().invoke(config_init, [])

    assert "Defaults restored" in result.output
    assert "default_engine=" in result.output
    assert not config_path.exists()


def test_init_idempotent_when_missing(tmp_path: Path, monkeypatch) -> None:
    _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_init, [])

    assert "Already at defaults" in result.output


def test_open_dispatches_platform_command(tmp_path: Path, monkeypatch) -> None:
    """三平台分别用 open / explorer / xdg-open 打开配置目录."""
    _patch(tmp_path, monkeypatch)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        "gdpm.cli.config.open.subprocess.Popen",
        lambda cmd, **kw: calls.append(cmd),
    )

    for system in ("Darwin", "Windows", "Linux"):
        monkeypatch.setattr("gdpm.cli.config.open.platform.system", lambda s=system: s)
        CliRunner().invoke(config_open, [])

    assert [cmd[0] for cmd in calls] == ["open", "explorer", "xdg-open"]
    # 打开的是配置文件所在目录 (临时目录的父级 = tmp_path)
    assert all(str(tmp_path) in cmd for cmd in calls)
