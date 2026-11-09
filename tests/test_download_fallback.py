"""
官方 → 自建镜像双通道下载测试.

双 base 写死在 constants (GODOT_DOWNLOAD_BASE / GODOT_DOWNLOAD_MIRROR),
无任何配置项; install 按序尝试: 官方优先, 走不通自动切换镜像.
镜像内部已完成 GitHub 中继与老版本 slug 容错, 客户端不再直连 GitHub.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

import httpx
from click.testing import CliRunner

from gdpm.cli.commands.godot.common import build_download_url, build_download_urls
from gdpm.cli.commands.godot.install import godot_install

if TYPE_CHECKING:
    from pathlib import Path


def _official_404() -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://official.test/x.zip")
    response = httpx.Response(404, request=request)
    return httpx.HTTPStatusError("404", request=request, response=response)


def test_urls_official_first_mirror_second() -> None:
    """候选顺序: 官方在前镜像在后, query 形态逐字一致 (平台无关)."""
    official, mirror = build_download_urls("4.7.2-stable")
    assert official == build_download_url("4.7.2-stable")
    assert official.startswith("https://downloads.godotengine.org/?version=4.7.2")
    assert mirror == official.replace(
        "https://downloads.godotengine.org",
        "https://godot-download.playereg.top",
    )
    assert "flavor=stable" in mirror and "slug=" in mirror


def _patch_install(
    tmp_path: Path,
    monkeypatch,
    official_error: Exception | None,
    mirror_error: Exception | None,
    calls: list[dict],
) -> None:
    """隔离引擎目录, 打桩双候选与分片下载 (假 zip 让解压链走通)."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.get_engines_dir", lambda: tmp_path
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.build_download_urls",
        lambda tag, csharp: [
            "https://official.test/x.zip",
            "https://mirror.test/x.zip",
        ],
    )

    def _fake_download(
        url: str,
        dest: Path,
        *,
        filename: str = "",
        **kwargs,
    ) -> Path:
        calls.append({"url": url, "verify": kwargs.get("verify")})
        if url.startswith("https://official") and official_error is not None:
            raise official_error
        if url.startswith("https://mirror") and mirror_error is not None:
            raise mirror_error
        dest.mkdir(parents=True, exist_ok=True)
        zip_path = dest / filename
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("Godot_fake", "fake")
        return zip_path

    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.download_file_chunked", _fake_download
    )


def test_fallback_switches_to_mirror_on_official_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """官方异常 → 自动切换镜像, 两次按序尝试, 成功装机."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, RuntimeError("official down"), None, calls)

    result = CliRunner().invoke(godot_install, ["4.3"])

    assert result.exit_code == 0
    out = result.output
    assert "Official channel failed (RuntimeError)" in out
    assert "switching to download mirror" in out
    assert "Installed Godot 4.3-stable" in out
    assert "GitHub" not in out
    assert [c["url"] for c in calls] == [
        "https://official.test/x.zip",
        "https://mirror.test/x.zip",
    ]


def test_mirror_serves_versions_official_404s(tmp_path: Path, monkeypatch) -> None:
    """官方 404 (未收录老版本) → 镜像补上, 不误报 not found."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, _official_404(), None, calls)

    result = CliRunner().invoke(godot_install, ["3.0"])

    assert result.exit_code == 0
    out = result.output
    assert "switching to download mirror" in out
    assert "Installed Godot 3.0-stable" in out
    assert "not found" not in out


def test_both_channels_failed_reports_last_error(tmp_path: Path, monkeypatch) -> None:
    """双通道全挂: 报镜像(最后)的错误, 恰好两次尝试, 无半成品."""
    calls: list[dict] = []
    _patch_install(
        tmp_path,
        monkeypatch,
        RuntimeError("official down"),
        RuntimeError("mirror down"),
        calls,
    )

    result = CliRunner().invoke(godot_install, ["4.3"])

    assert result.exit_code == 0
    out = result.output
    assert "Download failed: mirror down" in out
    assert len(calls) == 2


def test_both_404_keeps_friendly_message(tmp_path: Path, monkeypatch) -> None:
    """双通道都 404 (真·版本不存在): 保留 not found + list -r 指引."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, _official_404(), _official_404(), calls)

    result = CliRunner().invoke(godot_install, ["9.9"])

    assert result.exit_code == 0
    out = result.output
    assert "Version 9.9-stable not found" in out
    assert "godot list -r" in out
    assert len(calls) == 2
