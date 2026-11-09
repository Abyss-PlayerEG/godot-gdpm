"""
create 命令版本处理测试.

对应计划验收: rc/beta 标签不拼坏, stable 排序优先, 版本精确匹配.
"""

from __future__ import annotations

from gdpm.cli.commands.create import (
    _engine_matches,
    _engine_sort_key,
    _get_godot_version_tag,
)


def test_tag_stable() -> None:
    assert _get_godot_version_tag("4.7-stable") == "4.7"


def test_tag_rc_not_mangled() -> None:
    """rc 版本不再拼成 '4.71'."""
    assert _get_godot_version_tag("4.7-rc1") == "4.7"


def test_tag_beta_not_mangled() -> None:
    """beta 版本不再拼成 '4.72'."""
    assert _get_godot_version_tag("4.7-beta2") == "4.7"


def test_tag_patch_version() -> None:
    assert _get_godot_version_tag("3.6.2-stable") == "3.6"


def test_sort_stable_before_prerelease() -> None:
    ids = ["a@4.8-beta1", "a@4.7-stable", "a@3.6.2-stable"]
    ids.sort(key=_engine_sort_key)
    assert ids[0] == "a@4.7-stable"
    assert ids[-1] == "a@4.8-beta1"


def test_sort_numeric_version_desc() -> None:
    """数值版本降序, 4.10 应排在 4.7 之前 (非字符串序)."""
    ids = ["a@4.7-stable", "a@4.10-stable"]
    ids.sort(key=_engine_sort_key)
    assert ids[0] == "a@4.10-stable"


def test_match_exact() -> None:
    assert _engine_matches("gdpm-godot@4.7-stable", "4.7-stable")


def test_match_no_substring_false_positive() -> None:
    """子串误匹配修复: 4.7 不应命中 4.7.1."""
    assert not _engine_matches("gdpm-godot@4.7.1-stable", "4.7-stable")
    assert not _engine_matches("gdpm-godot@4.70-stable", "4.7-stable")


def test_match_csharp_same_version() -> None:
    assert _engine_matches("gdpm-godot@4.7-stable-csharp", "4.7-stable")
