"""
官方 versions.json 解析与远程列表筛选测试.

对应官方API迁移计划 Phase 2: 展平, 通道推导, 日期转换, 分页与筛选语义.
stable-only 决策 (2026-11): 远程列表恒只含正式版, 非 stable 一律排除,
-c 选项已移除. 分页语义: 仅 -a 不分页, 其余模式一律按 30/页切片.
"""

from __future__ import annotations

import httpx
import pytest

from gdpm.cli.commands.godot.common import (
    RemoteRelease,
    _flavor_channel,
    _parse_display_date,
    fetch_remote_versions,
    parse_versions_json,
)
from gdpm.cli.commands.godot.list import _paginate_remote

SAMPLE = [
    {
        "name": "4.8",
        "releases": [
            {
                "name": "beta2",
                "release_date": "29 October 2026",
                "release_notes": "https://example.com/n1",
            },
            {"name": "stable", "release_date": "1 July 2026"},
        ],
    },
    {
        "name": "3.6",
        "releases": [{"name": "stable", "release_date": "22 August 2026"}],
    },
]


def test_flatten_keeps_order_and_builds_tags() -> None:
    releases = parse_versions_json(SAMPLE)
    assert [r.tag for r in releases] == ["4.8-beta2", "4.8-stable", "3.6-stable"]


def test_stable_detection() -> None:
    releases = parse_versions_json(SAMPLE)
    assert releases[0].stable is False  # beta2
    assert releases[1].stable is True  # stable
    assert releases[2].stable is True


def test_channel_derived_from_flavor() -> None:
    """通道 = flavor 去除尾部序号."""
    releases = parse_versions_json(SAMPLE)
    assert releases[0].channel == "beta"
    assert releases[1].channel == "stable"
    assert releases[2].channel == "stable"


def test_flavor_channel_helper() -> None:
    assert _flavor_channel("beta2") == "beta"
    assert _flavor_channel("rc10") == "rc"
    assert _flavor_channel("dev7") == "dev"
    assert _flavor_channel("alpha3") == "alpha"
    assert _flavor_channel("stable") == "stable"


def test_date_converted_to_iso() -> None:
    releases = parse_versions_json(SAMPLE)
    assert releases[0].date == "2026-10-29"
    assert releases[1].date == "2026-07-01"


def test_parse_display_date_edge_cases() -> None:
    assert _parse_display_date("1 May 2026") == "2026-05-01"
    # 无法解析时原样返回
    assert _parse_display_date("") == ""
    assert _parse_display_date("not a date") == "not a date"


def test_skips_incomplete_entries() -> None:
    data = [{"name": "", "releases": [{"name": "stable"}]}, {"releases": []}]
    assert parse_versions_json(data) == []


def _sample_releases() -> list[RemoteRelease]:
    """40 个 4.x (通道轮转) + 30 个 3.x stable + 5 个 2.x stable."""
    channels = ("stable", "beta", "rc", "dev")
    rel: list[RemoteRelease] = []
    for i in range(40):
        channel = channels[i % 4]
        flavor = "stable" if channel == "stable" else f"{channel}{i % 3 + 1}"
        rel.append(
            RemoteRelease(
                tag=f"4.{i}-{flavor}",
                date="2026-01-01",
                stable=channel == "stable",
                channel=channel,
            )
        )
    rel += [
        RemoteRelease(
            tag=f"3.{i}-stable", date="2025-01-01", stable=True, channel="stable"
        )
        for i in range(30)
    ]
    rel += [
        RemoteRelease(
            tag=f"2.{i}-stable", date="2016-01-01", stable=True, channel="stable"
        )
        for i in range(5)
    ]
    return rel


def test_show_all_returns_everything_unpaginated() -> None:
    """-a: 全部 stable (含旧版本), 不分页, 忽略页码."""
    all_releases = _sample_releases()
    page_items, total_pages, page = _paginate_remote(all_releases, "", True, 5)
    assert len(page_items) == 45  # 10 个 4.x stable + 30 个 3.x + 5 个 2.x
    assert total_pages == 1
    assert page == 1
    assert {r.channel for r in page_items} == {"stable"}
    assert all(r.stable for r in page_items)


def test_non_stable_never_returned() -> None:
    """stable-only 硬保证: 任何模式 (默认/-V/-a) 都不返回预发布版本."""
    all_releases = _sample_releases()
    for args in (("", False, 1), ("4.", False, 1), ("", True, 1)):
        page_items, _, _ = _paginate_remote(all_releases, *args)
        assert all(r.stable for r in page_items)
        assert all(r.channel == "stable" for r in page_items)


def test_version_filter_defaults_to_stable() -> None:
    """-V 筛选同样只看正式版, 且不分页."""
    page_items, total_pages, _ = _paginate_remote(_sample_releases(), "4.1", False, 1)
    assert total_pages == 1
    # 前缀 4.1 且 stable: 4.12, 4.16
    assert [r.tag for r in page_items] == ["4.12-stable", "4.16-stable"]


def test_version_filter_shows_old_versions() -> None:
    """显式 -V 不受旧版本隐藏限制 (如 -V 2.)."""
    page_items, total_pages, _ = _paginate_remote(_sample_releases(), "2.", False, 1)
    assert total_pages == 1
    assert [r.tag for r in page_items] == [f"2.{i}-stable" for i in range(5)]


def test_version_filter_intersects_stable() -> None:
    """-V 与 stable-only 取交集."""
    page_items, total_pages, _ = _paginate_remote(_sample_releases(), "4.1", False, 1)
    assert total_pages == 1
    # 前缀 4.1 且 stable: 4.12, 4.16 (4.10-rc2 等被 stable-only 排除)
    assert [r.tag for r in page_items] == ["4.12-stable", "4.16-stable"]


def test_default_shows_only_stable_and_paginates() -> None:
    """默认: 只看正式版, 过滤 1.x/2.x 后按 30/页切片."""
    page_items, total_pages, page = _paginate_remote(_sample_releases(), "", False, 1)
    # stable 且 3./4.: 10 个 4.x + 30 个 3.x = 40 -> 2 页
    assert total_pages == 2
    assert page == 1
    assert len(page_items) == 30
    assert all(r.stable for r in page_items)
    assert all(r.tag.startswith(("3.", "4.")) for r in page_items)

    page_items2, _, page2 = _paginate_remote(_sample_releases(), "", False, 2)
    assert page2 == 2
    assert len(page_items2) == 10


def test_page_clamped_to_valid_range() -> None:
    """越界页码收敛到有效范围."""
    _, total_pages, page = _paginate_remote(_sample_releases(), "", False, 99)
    assert total_pages == 2
    assert page == 2

    _, _, page0 = _paginate_remote(_sample_releases(), "", False, 0)
    assert page0 == 1


class _Resp:
    """versions.json 响应替身."""

    def __init__(self, data: list) -> None:
        self._data = data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> list:
        return self._data


def test_fetch_official_first_then_mirror(monkeypatch) -> None:
    """双通道: 官方优先, 失败切镜像 /versions.json, 顺序与地址写死."""
    calls: list[str] = []

    def fake_get(url: str, **kwargs):
        calls.append(url)
        if "godotengine.org" in url:
            raise httpx.ConnectError("official down")
        return _Resp(SAMPLE)

    monkeypatch.setattr("gdpm.cli.commands.godot.common.httpx.get", fake_get)

    releases = fetch_remote_versions()

    assert calls == [
        "https://godotengine.org/versions.json",
        "https://godot-download.playereg.top/versions.json",
    ]
    assert releases[0].tag == "4.8-beta2"


def test_fetch_uses_official_when_healthy(monkeypatch) -> None:
    """官方健康时只打一次, 不碰镜像."""
    calls: list[str] = []

    def fake_get(url: str, **kwargs):
        calls.append(url)
        return _Resp(SAMPLE)

    monkeypatch.setattr("gdpm.cli.commands.godot.common.httpx.get", fake_get)

    fetch_remote_versions()

    assert len(calls) == 1
    assert calls[0] == "https://godotengine.org/versions.json"


def test_fetch_raises_when_both_channels_fail(monkeypatch) -> None:
    """两通道均失败: 抛出最后一次异常 (调用方统一提示)."""

    def fake_get(url: str, **kwargs):
        raise httpx.ConnectError("all down")

    monkeypatch.setattr("gdpm.cli.commands.godot.common.httpx.get", fake_get)

    with pytest.raises(httpx.ConnectError):
        fetch_remote_versions()
