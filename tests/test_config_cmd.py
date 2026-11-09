"""
gdpm config 命令测试.

覆盖: set 键名校验与整数校验, 空值重置 (删行), ~ 路径展开,
open 的三平台目录打开命令分发.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from gdpm.cli.commands.config.open import config_open
from gdpm.cli.commands.config.set import config_set
from gdpm.config import global_config


def _patch(tmp_path: Path, monkeypatch) -> Path:
    """配置路径隔离到临时目录 (含 open 的直接绑定)."""
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(global_config, "get_config_path", lambda: config_path)
    monkeypatch.setattr(
        "gdpm.cli.commands.config.open.get_config_path", lambda: config_path
    )
    return config_path


def test_set_writes_only_target_key(tmp_path: Path, monkeypatch) -> None:
    """行级写入: set 一条只出现该键, 不材料化其他默认键."""
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        config_set, ["default_engine", "steam-godot@4.7-stable"]
    )

    assert result.exit_code == 0
    text = config_path.read_text(encoding="utf-8")
    assert 'default_engine = "steam-godot@4.7-stable"' in text
    assert "[defaults]" in text
    # 其他键不得出现 (用户反馈: set 后文件冒出没设过的键)
    for absent in ("godot_path", "parallel_downloads", "[store]", "[cache]", "[ui]"):
        assert absent not in text, absent
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
    # 只列已实现的可设置键
    for key in (
        "default_engine",
        "parallel_downloads",
        "godot_mirror",
        "cache_dir",
        "language",
    ):
        assert key in result.output
    # 未实现的键不展示
    for key in ("godot_path", "addons_dir", "store_url"):
        assert key not in result.output


def test_unimplemented_keys_rejected(tmp_path: Path, monkeypatch) -> None:
    """godot_path/addons_dir/store_url 暂无消费方: 不展示也不接受设置."""
    config_path = _patch(tmp_path, monkeypatch)

    for key in ("godot_path", "addons_dir", "store_url"):
        result = CliRunner().invoke(config_set, [key, "x"])
        assert "Unknown config key" in result.output, key
        assert not config_path.exists()


def test_set_empty_value_removes_line(tmp_path: Path, monkeypatch) -> None:
    """空值重置 = 删行: 该文件只有这一个键时, 删行即删文件."""
    config_path = _patch(tmp_path, monkeypatch)
    CliRunner().invoke(config_set, ["default_engine", "x@1.0-stable"])
    assert config_path.exists()

    result = CliRunner().invoke(config_set, ["default_engine", ""])

    assert "reset to default" in result.output
    assert not config_path.exists()


def test_set_preserves_unrelated_lines(tmp_path: Path, monkeypatch) -> None:
    """set 一条只动目标行: 手写行与其他段内容逐字保留."""
    config_path = _patch(tmp_path, monkeypatch)
    config_path.write_text(
        '[store]\nbase_url = "https://mine.example/api"\n\n[ui]\nlanguage = "zh"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(config_set, ["parallel_downloads", "8"])

    assert result.exit_code == 0
    text = config_path.read_text(encoding="utf-8")
    assert 'base_url = "https://mine.example/api"' in text
    assert 'language = "zh"' in text
    assert "parallel_downloads = 8" in text


def test_default_engine_empty_line_survives_next_set(
    tmp_path: Path, monkeypatch
) -> None:
    """手写的 default_engine = "" 行在后续 set 重写后仍在 (稀疏模型曾丢弃)."""
    config_path = _patch(tmp_path, monkeypatch)
    config_path.write_text('[defaults]\ndefault_engine = ""\n', encoding="utf-8")

    result = CliRunner().invoke(config_set, ["language", "zh"])

    assert result.exit_code == 0
    text = config_path.read_text(encoding="utf-8")
    assert 'default_engine = ""' in text
    assert 'language = "zh"' in text


def test_open_dispatches_platform_command(tmp_path: Path, monkeypatch) -> None:
    """三平台分别用 open / explorer / xdg-open 打开配置目录."""
    _patch(tmp_path, monkeypatch)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        "gdpm.cli.commands.config.open.subprocess.Popen",
        lambda cmd, **kw: calls.append(cmd),
    )

    for system in ("Darwin", "Windows", "Linux"):
        monkeypatch.setattr(
            "gdpm.cli.commands.config.open.platform.system", lambda s=system: s
        )
        CliRunner().invoke(config_open, [])

    assert [cmd[0] for cmd in calls] == ["open", "explorer", "xdg-open"]
    # 打开的是配置文件所在目录 (临时目录的父级 = tmp_path)
    assert all(str(tmp_path) in cmd for cmd in calls)


def test_set_integer_capped_at_max(tmp_path: Path, monkeypatch) -> None:
    """超过上限的配置值按上限落盘 (parallel_downloads 100 -> 32)."""
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_set, ["parallel_downloads", "100"])

    assert result.exit_code == 0
    assert "parallel_downloads = 32" in config_path.read_text(encoding="utf-8")
    assert "= 32" in result.output


def test_set_godot_mirror_roundtrip(tmp_path: Path, monkeypatch) -> None:
    """godot_mirror 设置 → read_global_config 读回 (build_download_url 消费)."""
    _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(
        config_set, ["godot_mirror", "https://godot-download.playereg.top"]
    )

    assert result.exit_code == 0
    assert (
        global_config.read_global_config().godot_mirror
        == "https://godot-download.playereg.top"
    )


def test_set_cache_dir_expands_user(tmp_path: Path, monkeypatch) -> None:
    """~ 输入展开为绝对路径; 展开后等于默认值时按重置删行."""
    config_path = _patch(tmp_path, monkeypatch)

    result = CliRunner().invoke(config_set, ["cache_dir", "~/gdpm-probe"])

    assert result.exit_code == 0
    text = config_path.read_text(encoding="utf-8")
    assert str(Path.home() / "gdpm-probe") in text
    assert "~" not in text

    reset = CliRunner().invoke(config_set, ["cache_dir", "~/.gdpm/cache"])

    assert "reset to default" in reset.output
    assert not config_path.exists()
