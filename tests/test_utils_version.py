"""
utils.version 版本规范化与解析测试.

覆盖宽松版本/约束的规范化, 解析异常与兼容性判定.
"""

from __future__ import annotations

import pytest
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from gdpm.utils.version import (
    is_compatible,
    normalize_constraint,
    normalize_version,
    parse_specifier_set,
    parse_version,
    version_matches,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", "0.0.0"),
        ("v1.2.3", "1.2.3"),
        ("VV1.2", "1.2"),
        ("  1.0.0  ", "1.0.0"),
        ("1.0.0-stable", "1.0.0.stable"),
        ("1.0.0-beta1", "1.0.0.beta1"),
        ("1.0.0-rc2", "1.0.0.rc2"),
        ("1.0.0-alpha", "1.0.0.alpha"),
        ("abc", "0.0.0"),
        ("1.2.3.4", "1.2.3.4"),
    ],
)
def test_normalize_version(raw: str, expected: str) -> None:
    """宽松版本字符串规范化为 PEP 440 风格."""
    assert normalize_version(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("^1.0.0", ">=1.0.0,<2.0.0"),
        ("^v0.5", ">=0.5,<1.0.0"),
        ("~1.2.3", ">=1.2.3,<1.3.0"),
        ("~1.2", ">=1.2,<1.3.0"),
        ("*", ">=0.0.0"),
        (">=v1.0.0", ">=1.0.0"),
        ("==V2.0", "==2.0"),
        (">=1.0,<2.0", ">=1.0,<2.0"),
        ("  >=1.0.0  ", ">=1.0.0"),
    ],
)
def test_normalize_constraint(raw: str, expected: str) -> None:
    """caret/tilde/通配符与操作符前缀统一规范化."""
    assert normalize_constraint(raw) == expected


def test_parse_version_normalizes() -> None:
    """解析前先规范化, v 前缀被剥离."""
    assert parse_version("v1.2.3") == Version("1.2.3")


def test_parse_version_invalid_raises() -> None:
    """规范化后仍非法时抛 InvalidVersion."""
    with pytest.raises(InvalidVersion):
        parse_version("1.0.0-stable")


def test_parse_specifier_set_normalizes() -> None:
    """约束解析前先规范化."""
    assert parse_specifier_set("^1.0.0") == SpecifierSet(">=1.0.0,<2.0.0")


def test_parse_specifier_set_invalid_raises() -> None:
    """非法约束抛 InvalidSpecifier."""
    with pytest.raises(InvalidSpecifier):
        parse_specifier_set(">>1.0")


@pytest.mark.parametrize(
    ("version", "constraint", "expected"),
    [
        ("1.5.0", "^1.0.0", True),
        ("2.0.0", "^1.0.0", False),
        ("4.2.1", ">=4.0.0", True),
        ("1.0", "1.0", True),
        ("1.5.0", "*", True),
        ("abc", "*", True),
        ("abc", ">=1", False),
    ],
)
def test_version_matches(version: str, constraint: str, expected: bool) -> None:
    """约束匹配; 解析失败时回退字符串比较."""
    assert version_matches(version, constraint) is expected


@pytest.mark.parametrize(
    ("project", "minimum", "maximum", "expected"),
    [
        ("", "4.0", "5.0", True),
        ("*", "4.0", "5.0", True),
        (">=4.2.0,<5.0.0", "4.0", "4.5", True),
        ("4.5", "4.0", "4.5", True),
        ("4.7", "4.0", "4.5", False),
        ("3.5", "4.0", "4.5", False),
        ("4.2", "None", "None", True),
        ("4.2", "", "", True),
        (">=4.0.0.stable", "4.0", "5.0", True),
    ],
)
def test_is_compatible(
    project: str, minimum: str, maximum: str, expected: bool
) -> None:
    """插件 Godot 版本区间判定; 缺失/异常时放行."""
    compatible, message = is_compatible(project, minimum, maximum)
    assert compatible is expected
    if expected:
        assert message == ""


def test_is_compatible_reports_max_violation() -> None:
    """高于插件最高版本时说明原因."""
    compatible, message = is_compatible("4.7", "4.0", "4.5")
    assert compatible is False
    assert "supports Godot <=4.5" in message
    assert "4.7" in message


def test_is_compatible_reports_min_violation() -> None:
    """低于插件最低版本时说明原因."""
    compatible, message = is_compatible("3.5", "4.0", "4.5")
    assert compatible is False
    assert "requires Godot >=4.0" in message
    assert "3.5" in message
