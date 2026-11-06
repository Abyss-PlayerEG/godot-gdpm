"""
find_engine_binary 三平台布局测试.

对应计划验收: macOS .app / mono 变体 / Windows .exe / Linux 执行位恢复.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

from gdpm.cli.godot.common import find_engine_binary

if TYPE_CHECKING:
    from pathlib import Path


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def test_macos_app(tmp_path: Path) -> None:
    binary = _touch(tmp_path / "Godot.app" / "Contents" / "MacOS" / "Godot")
    with patch("platform.system", return_value="Darwin"):
        assert find_engine_binary(tmp_path) == str(binary)


def test_macos_mono_app(tmp_path: Path) -> None:
    """mono 变体: Godot_mono.app 内部二进制名为 Godot_mono."""
    binary = _touch(tmp_path / "Godot_mono.app" / "Contents" / "MacOS" / "Godot_mono")
    with patch("platform.system", return_value="Darwin"):
        assert find_engine_binary(tmp_path) == str(binary)


def test_windows_prefers_non_console(tmp_path: Path) -> None:
    editor = _touch(tmp_path / "Godot_v4.7-stable_win64.exe")
    _touch(tmp_path / "Godot_v4.7-stable_win64_console.exe")
    with patch("platform.system", return_value="Windows"):
        assert find_engine_binary(tmp_path) == str(editor)


def test_linux_binary_restores_exec_bit(tmp_path: Path) -> None:
    binary = _touch(tmp_path / "Godot_v4.7-stable_linux.x86_64")
    binary.chmod(0o644)
    with patch("platform.system", return_value="Linux"):
        result = find_engine_binary(tmp_path)
    assert result == str(binary)
    assert os.access(binary, os.X_OK)


def test_linux_mono_subdir(tmp_path: Path) -> None:
    subdir = tmp_path / "Godot_v4.7-stable_mono_linux_x86_64"
    binary = _touch(subdir / "Godot_v4.7-stable_mono_linux_x86_64")
    (subdir / "GodotSharp").mkdir()
    with patch("platform.system", return_value="Linux"):
        assert find_engine_binary(tmp_path) == str(binary)
