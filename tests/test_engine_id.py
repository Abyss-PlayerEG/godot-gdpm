"""
引擎 ID (Name@Version) 解析/查找封装与 C# 后缀解析测试.

回归背景: normalize_version 会剥掉 -csharp 后缀, 候选目录循环曾先试
非 C# 目录 —— 指定 C# 引擎却打开普通版. 查找点已收敛到
_find_managed_binary, 解析与错误流收敛到 parse/resolve_engine_id.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from gdpm.cli.commands.godot.common import (
    find_engine,
    parse_engine_id,
    resolve_engine_id,
    resolve_engine_path,
)

if TYPE_CHECKING:
    from pathlib import Path


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def _setup_engines(tmp_path: Path, monkeypatch, *versions: str) -> None:
    """构造托管引擎目录, 并隔离引擎目录/本地注册表."""
    for version in versions:
        _touch(tmp_path / version / "Godot")
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.get_engines_dir", lambda: tmp_path
    )
    monkeypatch.setattr("gdpm.config.local_engines.load_local_engines", lambda: {})


def test_csharp_id_resolves_csharp_directory(tmp_path: Path, monkeypatch) -> None:
    """显式 -csharp 后缀必须命中 C# 目录 (回归: 曾被 normalize 剥后缀后先命中普通版)."""
    _touch(tmp_path / "4.7-stable" / "Godot")
    csharp = _touch(tmp_path / "4.7-stable-csharp" / "Godot")
    _setup_engines(tmp_path, monkeypatch)

    with patch("platform.system", return_value="Linux"):
        assert find_engine("gdpm-godot", "4.7-stable-csharp") == str(csharp)
        assert resolve_engine_path("gdpm-godot", "4.7-stable-csharp") == str(csharp)
        # 无后缀时保持旧行为: 优先普通版
        plain = tmp_path / "4.7-stable" / "Godot"
        assert find_engine("gdpm-godot", "4.7-stable") == str(plain)


def test_plain_version_falls_back_to_csharp(tmp_path: Path, monkeypatch) -> None:
    """只有 C# 目录时, 普通版本回退到 C# (旧行为保留)."""
    csharp = _touch(tmp_path / "4.7-stable-csharp" / "Godot")
    _setup_engines(tmp_path, monkeypatch)

    with patch("platform.system", return_value="Linux"):
        assert find_engine("gdpm-godot", "4.7-stable") == str(csharp)


def test_csharp_id_never_falls_back_to_plain(tmp_path: Path, monkeypatch) -> None:
    """只有普通目录时, C# 请求返回未找到 —— 绝不静默替换为非 C#."""
    _setup_engines(tmp_path, monkeypatch, "4.7-stable")

    with patch("platform.system", return_value="Linux"):
        assert find_engine("gdpm-godot", "4.7-stable-csharp") is None
        assert resolve_engine_path("gdpm-godot", "4.7-stable-csharp") == ""


def test_mono_suffix_resolves_csharp_directory(tmp_path: Path, monkeypatch) -> None:
    """-mono 后缀与 -csharp 同语义, 命中 C# 目录."""
    csharp = _touch(tmp_path / "4.7-stable-csharp" / "Godot")
    _setup_engines(tmp_path, monkeypatch)

    with patch("platform.system", return_value="Linux"):
        assert find_engine("gdpm-godot", "4.7-stable-mono") == str(csharp)


def test_parse_engine_id() -> None:
    """纯解析: 合法 ID 返回 (名称, 版本), 非法输入返回 None."""
    assert parse_engine_id("gdpm-godot@4.7-stable-csharp") == (
        "gdpm-godot",
        "4.7-stable-csharp",
    )
    assert parse_engine_id("steam@4.7-stable") == ("steam", "4.7-stable")
    for bad in ("4.7-stable", "name@", "@1.0", ""):
        assert parse_engine_id(bad) is None, bad


def test_resolve_engine_id_success(monkeypatch) -> None:
    """解析即查找: 后缀原样传给查找层, 成功返回三元组."""
    seen: dict[str, str] = {}

    def _fake(name: str, version: str) -> str:
        seen.update(name=name, version=version)
        return "/bin/Godot"

    monkeypatch.setattr("gdpm.cli.commands.godot.common.find_engine", _fake)

    resolved = resolve_engine_id(
        "gdpm-godot@4.7-stable-csharp", example="gdpm godot open X"
    )

    assert resolved == ("gdpm-godot", "4.7-stable-csharp", "/bin/Godot")
    # C# 意图不丢: 版本原样传入
    assert seen == {"name": "gdpm-godot", "version": "4.7-stable-csharp"}


def test_resolve_engine_id_format_error(capsys) -> None:
    """格式错误: 返回 None 并打印示例命令."""
    resolved = resolve_engine_id("4.7-stable", example="gdpm godot use some-engine")

    assert resolved is None
    out = capsys.readouterr().out
    assert "Invalid format" in out
    assert "gdpm godot use some-engine" in out


def test_resolve_engine_id_not_found(monkeypatch, capsys) -> None:
    """引擎不存在: 返回 None 并提示 list -id."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.find_engine", lambda name, version: None
    )

    resolved = resolve_engine_id("ghost@9.9", example="x")

    assert resolved is None
    out = capsys.readouterr().out
    assert "not found" in out
    assert "list -id" in out
