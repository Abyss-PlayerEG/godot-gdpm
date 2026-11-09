"""
版本显示测试: gdpm -V / --about 的标签必须带序号 (beta1/dev2/rc1).

回归背景: _version_text 只显示 __tag__, 丢掉了 __version__ 里的序号 ——
beta2/dev3 一律显示成 [beta]/[dev], 无法区分第几轮.
"""

from __future__ import annotations

import pytest

from gdpm.cli.app import _version_text


@pytest.mark.parametrize(
    ("version", "tag", "expected"),
    [
        ("0.0.1b1", "beta", "gdpm v0.0.1 [beta1]"),
        ("0.0.1b3", "beta", "gdpm v0.0.1 [beta3]"),
        ("0.1.1.dev2", "dev", "gdpm v0.1.1 [dev2]"),
        ("0.1.1.dev3", "dev", "gdpm v0.1.1 [dev3]"),
        ("0.1.0rc1", "rc", "gdpm v0.1.0 [rc1]"),
        ("0.1.0a2", "alpha", "gdpm v0.1.0 [alpha2]"),
        ("0.1.0", "", "gdpm v0.1.0"),
    ],
)
def test_version_text_shows_tag_number(
    monkeypatch, version: str, tag: str, expected: str
) -> None:
    """标签序号从 __version__ 提取并展示; stable 无方括号标签."""
    monkeypatch.setattr("gdpm.cli.app.__version__", version)
    monkeypatch.setattr("gdpm.cli.app.__tag__", tag)

    plain = _version_text().plain

    assert plain.startswith(expected)
    assert "(" in plain  # 安装方式/平台后缀仍在


def test_version_text_tag_without_number(monkeypatch) -> None:
    """标签存在但版本无序号 (手工状态) 的降级: 只显示标签不崩."""
    monkeypatch.setattr("gdpm.cli.app.__version__", "0.1.0")
    monkeypatch.setattr("gdpm.cli.app.__tag__", "beta")

    assert "[beta]" in _version_text().plain
