"""
本地 list 版本与通道筛选测试.

本地是库存视图: -V/-c 仅显式指定时生效, 不套用远程的默认 stable 规则.
"""

from __future__ import annotations

from gdpm.cli.godot.list import (
    _filter_local_rows,
    _local_channel,
    _sort_local_rows,
    _version_nums,
)

ROWS = [
    {"name": "gdpm-godot", "version": "4.4-stable", "source": "~/a"},
    {"name": "gdpm-godot", "version": "4.4-stable-csharp", "source": "~/b"},
    {"name": "gdpm-godot", "version": "4.7-stable", "source": "~/c"},
    {"name": "steam-godot", "version": "4.8-rc1", "source": "~/d"},
    {"name": "broken", "version": "-", "source": "~/e"},
]


def test_local_channel_derivation() -> None:
    assert _local_channel("4.4-stable") == "stable"
    assert _local_channel("4.4-stable-csharp") == "stable"
    assert _local_channel("3.6.2-stable") == "stable"
    assert _local_channel("4.8-rc1") == "rc"
    assert _local_channel("4.8-beta2") == "beta"
    assert _local_channel("4.8-dev7") == "dev"
    # 无通道信息时为空串
    assert _local_channel("-") == ""
    assert _local_channel("") == ""


def test_no_filter_returns_all_rows() -> None:
    assert _filter_local_rows(ROWS, "", None) == ROWS


def test_version_prefix_filter() -> None:
    result = _filter_local_rows(ROWS, "4.4", None)
    assert [r["version"] for r in result] == ["4.4-stable", "4.4-stable-csharp"]


def test_channel_filter_includes_csharp_variant() -> None:
    """csharp 变体的通道仍是 stable, 应被 -c stable 命中."""
    result = _filter_local_rows(ROWS, "", "stable")
    assert [r["version"] for r in result] == [
        "4.4-stable",
        "4.4-stable-csharp",
        "4.7-stable",
    ]


def test_version_and_channel_combine() -> None:
    result = _filter_local_rows(ROWS, "4.4", "stable")
    assert len(result) == 2
    result2 = _filter_local_rows(ROWS, "4.4", "rc")
    assert result2 == []


def test_unknown_version_excluded_by_filters() -> None:
    """版本为 '-' 的条目无法匹配任何显式筛选."""
    assert all(r["version"] != "-" for r in _filter_local_rows(ROWS, "4", None))
    assert all(r["version"] != "-" for r in _filter_local_rows(ROWS, "", "stable"))


def test_version_nums_parse() -> None:
    assert _version_nums("4.10-stable") == (4, 10)
    assert _version_nums("3.6.2-stable") == (3, 6, 2)
    assert _version_nums("4.8-rc1") == (4, 8)
    assert _version_nums("-") == ()
    assert _version_nums("") == ()


def test_local_rows_sorted_newest_first() -> None:
    """版本新旧排序: 数值降序 (4.10 > 4.7), 同版本 stable 优先, 未知最后."""
    rows = [
        {"name": "a", "version": "4.4-stable", "source": "s"},
        {"name": "b", "version": "3.6.2-stable", "source": "s"},
        {"name": "c", "version": "4.7-stable", "source": "s"},
        {"name": "d", "version": "4.10-stable", "source": "s"},
        {"name": "e", "version": "4.8-rc1", "source": "s"},
        {"name": "f", "version": "4.8-stable", "source": "s"},
        {"name": "g", "version": "-", "source": "s"},
    ]
    _sort_local_rows(rows)
    assert [r["version"] for r in rows] == [
        "4.10-stable",  # 数值序: 4.10 > 4.8 > 4.7 > 4.4 > 3.6.2
        "4.8-stable",  # 同版本号: stable 比 rc 新
        "4.8-rc1",
        "4.7-stable",
        "4.4-stable",
        "3.6.2-stable",
        "-",  # 无法解析的排最后
    ]


def test_sort_keeps_csharp_variant_with_stable() -> None:
    """csharp 变体与同版本非变体相邻且排在其后 (名称次序)."""
    rows = [
        {"name": "gdpm-godot", "version": "4.4-stable-csharp", "source": "s"},
        {"name": "gdpm-godot", "version": "4.4-stable", "source": "s"},
    ]
    _sort_local_rows(rows)
    assert [r["version"] for r in rows] == ["4.4-stable", "4.4-stable-csharp"]
