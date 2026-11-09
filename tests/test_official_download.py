"""
官方下载接口 URL 构造测试.

对应官方API迁移计划 Phase 1: slug 代际规则与 mono 命名.
所有 URL 断言均与官网 archive 页面实抓链接逐字一致.
哈希校验已按决策移除 (无官方哈希获取接口, 见官方API迁移.md Phase 3).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from gdpm.cli.commands.godot.common import _official_asset, build_download_url
from gdpm.config.global_config import GlobalConfig


@pytest.fixture(autouse=True)
def _isolated_mirror(monkeypatch) -> None:
    """URL 断言锁定官方默认: 隔离本机 env/全局配置的镜像设置."""
    monkeypatch.delenv("GDPM_GODOT_MIRROR", raising=False)
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.read_global_config",
        lambda: GlobalConfig(),
    )


def _with_platform(system: str, machine: str):
    return (
        patch("gdpm.cli.commands.godot.common.platform.system", return_value=system),
        patch("gdpm.cli.commands.godot.common.platform.machine", return_value=machine),
    )


def test_linux_x64_url_matches_official() -> None:
    sys_p, mach_p = _with_platform("Linux", "x86_64")
    with sys_p, mach_p:
        url = build_download_url("4.7.2-stable")
    assert url == (
        "https://downloads.godotengine.org/"
        "?version=4.7.2&flavor=stable&slug=linux.x86_64.zip&platform=linux.64"
    )


def test_windows_mono_url_matches_official() -> None:
    sys_p, mach_p = _with_platform("Windows", "AMD64")
    with sys_p, mach_p:
        url = build_download_url("4.7.2-stable", csharp=True)
    assert url == (
        "https://downloads.godotengine.org/"
        "?version=4.7.2&flavor=stable&slug=mono_win64.zip&platform=windows.64"
    )


def test_linux_3x_uses_x11_slug() -> None:
    """3.x 的 Linux 资产名是 x11.64, 关键词方案在这里必挂."""
    sys_p, mach_p = _with_platform("Linux", "x86_64")
    with sys_p, mach_p:
        url = build_download_url("3.6.2-stable")
    assert "slug=x11.64.zip" in url
    assert "platform=linux.64" in url


def test_macos_universal_before_4_8() -> None:
    sys_p, mach_p = _with_platform("Darwin", "arm64")
    with sys_p, mach_p:
        url = build_download_url("4.7.2-stable")
    assert "slug=macos.universal.zip" in url
    assert "platform=macos.universal" in url


def test_macos_arch_split_after_4_8() -> None:
    """4.8 起 macOS 拆分架构."""
    sys_p, mach_p = _with_platform("Darwin", "arm64")
    with sys_p, mach_p:
        url = build_download_url("4.8-beta2")
    assert "flavor=beta2" in url
    assert "slug=macos.arm64.zip" in url
    assert "platform=macos.arm64" in url


def test_linux_arm64_slug() -> None:
    sys_p, mach_p = _with_platform("Linux", "aarch64")
    with sys_p, mach_p:
        slug, platform_id = _official_asset("4.7.2")
    assert slug == "linux.arm64.zip"
    assert platform_id == "linux.arm64"


def test_mono_linux_keeps_underscore_naming() -> None:
    """mono linux 文件名是下划线 (mono_linux_x86_64), 与下载 slug 一致."""
    sys_p, mach_p = _with_platform("Linux", "x86_64")
    with sys_p, mach_p:
        slug, _ = _official_asset("4.7.2", csharp=True)
    assert slug == "mono_linux_x86_64.zip"


def test_mirror_env_overrides_base(monkeypatch) -> None:
    """环境变量 GDPM_GODOT_MIRROR 覆盖 base, query 形态与官方一致."""
    monkeypatch.setenv("GDPM_GODOT_MIRROR", "https://godot-download.playereg.top/")
    sys_p, mach_p = _with_platform("Linux", "x86_64")
    with sys_p, mach_p:
        url = build_download_url("4.7.2-stable")
    assert url == (
        "https://godot-download.playereg.top/"
        "?version=4.7.2&flavor=stable&slug=linux.x86_64.zip&platform=linux.64"
    )


def test_mirror_config_used_when_env_absent(monkeypatch) -> None:
    """env 未设时读全局配置 godot_mirror, 尾斜杠被统一去除."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.read_global_config",
        lambda: GlobalConfig(godot_mirror="https://mirror.example/"),
    )
    sys_p, mach_p = _with_platform("Linux", "x86_64")
    with sys_p, mach_p:
        url = build_download_url("4.7.2-stable")
    assert url.startswith("https://mirror.example/?version=4.7.2&")


def test_mirror_env_beats_config(monkeypatch) -> None:
    """优先级: 环境变量 > 全局配置 > 官方默认."""
    monkeypatch.setenv("GDPM_GODOT_MIRROR", "https://env-mirror.example")
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.read_global_config",
        lambda: GlobalConfig(godot_mirror="https://config-mirror.example"),
    )
    sys_p, mach_p = _with_platform("Linux", "x86_64")
    with sys_p, mach_p:
        url = build_download_url("4.7.2-stable")
    assert url.startswith("https://env-mirror.example/?version=")
