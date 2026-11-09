"""
官方通道 → 旧 GitHub 方案自动切换测试.

背景: 官方 downloads.godotengine.org 对 1.x/2.x/3.0-mac 未收录 (404),
且其 ≤4.3 的 302 下一站本来就是 GitHub —— 官方走不通时 install 必须
自动切换旧方案 (GitHub 直链 + verify=False) 而非直接报错.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

import httpx
from click.testing import CliRunner

from gdpm.cli.commands.godot.common import build_github_download_urls
from gdpm.cli.commands.godot.install import godot_install

if TYPE_CHECKING:
    from pathlib import Path


class _Resp:
    """GitHub API 响应替身."""

    def __init__(self, status: int, assets: list[str] | None = None) -> None:
        self.status_code = status
        self._assets = assets or []

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return {
            "assets": [
                {"name": n, "browser_download_url": f"https://gh.test/{n}"}
                for n in self._assets
            ]
        }


def test_github_url_picks_platform_asset(monkeypatch) -> None:
    """平台关键词过滤: macOS 选 macos 资产, 且排除 mono 变体."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.get_godot_platform", lambda: "macos.universal"
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.httpx.get",
        lambda *args, **kwargs: _Resp(
            200,
            [
                "Godot_v4.3-stable_win64.exe.zip",
                "Godot_v4.3-stable_macos.universal.zip",
                "Godot_v4.3-stable_mono_macos.universal.zip",
            ],
        ),
    )

    assert build_github_download_urls("4.3-stable") == [
        "https://gh.test/Godot_v4.3-stable_macos.universal.zip"
    ]


def test_github_url_mono_filter(monkeypatch) -> None:
    """csharp=True 只接受 _mono 资产."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.get_godot_platform", lambda: "macos.universal"
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.httpx.get",
        lambda *args, **kwargs: _Resp(
            200,
            [
                "Godot_v4.3-stable_macos.universal.zip",
                "Godot_v4.3-stable_mono_macos.universal.zip",
            ],
        ),
    )

    assert build_github_download_urls("4.3-stable", csharp=True)[0].endswith(
        "mono_macos.universal.zip"
    )


def test_github_url_linux_matches_x11_and_skips_server(monkeypatch) -> None:
    """Linux: 3.x 资产名是 x11.64, 且必须排除 server 构建."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.get_godot_platform", lambda: "linux.x86_64"
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.common.httpx.get",
        lambda *args, **kwargs: _Resp(
            200,
            [
                "Godot_v3.5.3_stable_linux_server.64.zip",
                "Godot_v3.5.3-stable_x11.64.zip",
            ],
        ),
    )

    assert build_github_download_urls("3.5.3-stable") == [
        "https://gh.test/Godot_v3.5.3-stable_x11.64.zip"
    ]


def test_github_url_not_found_tries_both_repos(monkeypatch) -> None:
    """两仓库依次查询, 全无匹配返回空列表."""
    calls: list[str] = []

    def _get(url: str, **kwargs) -> _Resp:
        calls.append(url)
        return _Resp(404)

    monkeypatch.setattr("gdpm.cli.commands.godot.common.httpx.get", _get)

    assert build_github_download_urls("9.9.9-stable") == []
    assert len(calls) == 2
    # 查询顺序: 主仓库 (历史方案同源) 优先, godot-builds 兜底
    assert "repos/godotengine/godot/releases" in calls[0]
    assert "godot-builds" in calls[1]


def _patch_install(
    tmp_path: Path,
    monkeypatch,
    official_error: Exception | None,
    gh_urls: list[str],
    calls: list[dict],
    failing_gh: frozenset[str] = frozenset(),
) -> None:
    """隔离引擎目录, 打桩官方/候选 URL 与分片下载 (假 zip 让解压链走通)."""
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.get_engines_dir", lambda: tmp_path
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.build_download_url",
        lambda tag, csharp: "https://official.test/x.zip",
    )
    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.build_github_download_urls",
        lambda tag, csharp: gh_urls,
    )

    def _fake_download(
        url: str,
        dest: Path,
        *,
        filename: str = "",
        **kwargs,
    ) -> Path:
        calls.append({"url": url, "verify": kwargs.get("verify")})
        if url.startswith("https://official.test"):
            if official_error is not None:
                raise official_error
        elif url in failing_gh:
            raise RuntimeError("504 Gateway Time-out")
        dest.mkdir(parents=True, exist_ok=True)
        zip_path = dest / filename
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("Godot_fake", "fake")
        return zip_path

    monkeypatch.setattr(
        "gdpm.cli.commands.godot.install.download_file_chunked", _fake_download
    )


def test_fallback_switches_to_github_on_official_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """官方通道异常 → 自动切换 GitHub: 第二次下载 verify=False, 成功装机."""
    calls: list[dict] = []
    _patch_install(
        tmp_path,
        monkeypatch,
        RuntimeError("official down"),
        ["https://gh.test/Godot_v4.3-stable_macos.universal.zip"],
        calls,
    )

    result = CliRunner().invoke(godot_install, ["4.3"])

    assert result.exit_code == 0
    out = result.output
    assert "switching to GitHub" in out
    assert "Installed Godot 4.3-stable" in out
    # 官方严格校验, GitHub 兜底放宽 (旧方案同款)
    assert [c["verify"] for c in calls] == [True, False]
    assert calls[1]["url"].startswith("https://gh.test/")


def test_fallback_serves_404_official_assets(tmp_path: Path, monkeypatch) -> None:
    """官方 404 (如 3.0-mac 未收录) 也进兜底: 找到资产即装机, 不误报 not found."""
    request = httpx.Request("GET", "https://official.test/x.zip")
    response = httpx.Response(404, request=request)
    official_404 = httpx.HTTPStatusError("404", request=request, response=response)
    calls: list[dict] = []
    _patch_install(
        tmp_path,
        monkeypatch,
        official_404,
        ["https://gh.test/Godot_v3.0-stable_osx.fat.zip"],
        calls,
    )

    result = CliRunner().invoke(godot_install, ["3.0"])

    assert result.exit_code == 0
    assert "switching to GitHub" in result.output
    assert "Installed Godot 3.0-stable" in result.output
    assert "not found" not in result.output


def test_fallback_absent_reports_official_error(tmp_path: Path, monkeypatch) -> None:
    """兜底也找不到 (真·版本不存在): 报官方错误, 无第二次下载."""
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, RuntimeError("official down"), [], calls)

    result = CliRunner().invoke(godot_install, ["9.9"])

    assert result.exit_code == 0
    assert "Download failed: official down" in result.output
    assert "switching to GitHub" not in result.output
    assert len(calls) == 1


def test_official_404_keeps_friendly_message_when_no_fallback(
    tmp_path: Path, monkeypatch
) -> None:
    """官方 404 且兜底无果: 保留 not found + list -r 指引 (原行为)."""
    request = httpx.Request("GET", "https://official.test/x.zip")
    response = httpx.Response(404, request=request)
    official_404 = httpx.HTTPStatusError("404", request=request, response=response)
    calls: list[dict] = []
    _patch_install(tmp_path, monkeypatch, official_404, [], calls)

    result = CliRunner().invoke(godot_install, ["9.9"])

    assert result.exit_code == 0
    assert "Version 9.9-stable not found" in result.output
    assert "godot list -r" in result.output
    assert len(calls) == 1


def test_fallback_skips_failing_candidate(tmp_path: Path, monkeypatch) -> None:
    """候选按序尝试: 第一个仓库 504 时自动换下一个 (godot-builds 挂了也能装)."""
    calls: list[dict] = []
    _patch_install(
        tmp_path,
        monkeypatch,
        RuntimeError("official down"),
        [
            "https://gh.test/dead/godot-builds.zip",
            "https://gh.test/alive/godot-main.zip",
        ],
        calls,
        failing_gh=frozenset({"https://gh.test/dead/godot-builds.zip"}),
    )

    result = CliRunner().invoke(godot_install, ["4.3"])

    assert result.exit_code == 0
    assert "Installed Godot 4.3-stable" in result.output
    assert "GitHub candidate failed" in result.output
    assert [c["url"] for c in calls] == [
        "https://official.test/x.zip",
        "https://gh.test/dead/godot-builds.zip",
        "https://gh.test/alive/godot-main.zip",
    ]
    assert [c["verify"] for c in calls] == [True, False, False]
