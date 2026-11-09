"""
自建镜像单通道下载测试.

客户端唯一通道 = constants.GODOT_DOWNLOAD_MIRROR (官方 URL 已从 gdpm 移除),
回源与 GitHub 中继由 Worker 服务端处理; 本文件覆盖 install 的单次下载编排:
成功装机、失败报错、404 友好指引, 全程无切换/回退行为.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

import httpx
from click.testing import CliRunner

from gdpm.cli.commands.godot.common import build_download_url
from gdpm.cli.commands.godot.install import godot_install

if TYPE_CHECKING:
    from pathlib import Path


def _not_found() -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://mirror.test/x.zip")
    response = httpx.Response(404, request=request)
    return httpx.HTTPStatusError("404", request=request, response=response)


def test_url_is_mirror_with_official_query() -> None:
    """镜像 base + 官方同款 query 形态."""
    url = build_download_url("4.3-stable")
    assert url.startswith(
        "https://godot-download.playereg.top/?version=4.3&flavor=stable"
    )
    assert "slug=" in url and "platform=" in url


def _patch_install(
    tmp_path: Path,
    monkeypatch,
    download_error: Exception | None,
    calls: list[dict],
) -> None:
    """隔离引擎目录, 打桩唯一下载通道与分片下载 (假 zip 让解压链走通)."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.get_engines_dir", lambda: tmp_path
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.build_download_url",
        lambda tag, csharp: "https://mirror.test/x.zip",
    )

    def _fake_download(
        url: str,
        dest: Path,
        *,
        filename: str = "",
        **kwargs,
    ) -> Path:
        calls.append({"url": url, "verify": kwargs.get("verify")})
        if download_error is not None:
            raise download_error
        dest.mkdir(parents=True, exist_ok=True)
        zip_path = dest / filename
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("Godot_fake", "fake")
        return zip_path

    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.download_file_chunked", _fake_download
    )


def test_single_download_succeeds(tmp_path: Path, monkeypatch) -> None:
    """唯一通道单次下载即成功, 无任何切换/官方/GitHub 字样."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, None, calls)

    result = CliRunner().invoke(godot_install, ["4.3"])

    assert result.exit_code == 0
    assert "Installed Godot 4.3-stable" in result.output
    assert len(calls) == 1
    assert calls[0]["url"] == "https://mirror.test/x.zip"
    for absent in ("switching", "GitHub", "Official", "candidate"):
        assert absent not in result.output, absent


def test_download_failure_reported(tmp_path: Path, monkeypatch) -> None:
    """镜像失败: 直接报错, 恰好一次尝试, 无半成品."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, RuntimeError("mirror down"), calls)

    result = CliRunner().invoke(godot_install, ["4.3"])

    assert result.exit_code == 0
    assert "Download failed: mirror down" in result.output
    assert len(calls) == 1


def test_404_keeps_friendly_message(tmp_path: Path, monkeypatch) -> None:
    """404 (真·版本不存在): 保留 not found + list -r 指引."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, _not_found(), calls)

    result = CliRunner().invoke(godot_install, ["9.9"])

    assert result.exit_code == 0
    assert "Version 9.9-stable not found" in result.output
    assert "godot list -r" in result.output
    assert len(calls) == 1
