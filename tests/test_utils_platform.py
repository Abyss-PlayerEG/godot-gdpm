"""
utils.platform 平台标识映射测试.

覆盖各系统/架构组合到通用标识与 Godot 平台名的映射.
"""

from __future__ import annotations

import pytest

from gdpm.utils.platform import get_godot_platform, get_platform


def _set_platform(monkeypatch, system: str, machine: str) -> None:
    """替换 platform.system/machine 返回值."""
    monkeypatch.setattr("gdpm.utils.platform.platform.system", lambda: system)
    monkeypatch.setattr("gdpm.utils.platform.platform.machine", lambda: machine)


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Linux", "x86_64", "linux.x86_64"),
        ("linux", "aarch64", "linux.aarch64"),
        ("Darwin", "arm64", "macos.arm64"),
        ("Darwin", "x86_64", "macos.x86_64"),
        ("Windows", "AMD64", "windows.x86_64"),
        ("FreeBSD", "amd64", "freebsd.amd64"),
    ],
)
def test_get_platform(monkeypatch, system, machine, expected) -> None:
    """系统与架构组合映射为通用平台标识."""
    _set_platform(monkeypatch, system, machine)
    assert get_platform() == expected


@pytest.mark.parametrize(
    ("system", "expected"),
    [
        ("Linux", "Linux"),
        ("darwin", "macOS"),
        ("Windows", "Windows"),
        ("FreeBSD", "freebsd"),
    ],
)
def test_get_godot_platform(monkeypatch, system, expected) -> None:
    """系统名映射为 Godot 发行版平台名, 未知系统原样返回."""
    _set_platform(monkeypatch, system, "x86_64")
    assert get_godot_platform() == expected
