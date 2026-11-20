"""
utils.path 路径显示工具测试.

覆盖家目录替换与超长截断两条规则.
"""

from __future__ import annotations

from pathlib import Path

from gdpm.utils.path import shorten_path


def _fake_home(monkeypatch, home: str) -> None:
    """固定 Path.home(), 避免依赖真实家目录."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: Path(home)))


def test_home_replaced_with_tilde(monkeypatch) -> None:
    """家目录前缀替换为 ~."""
    _fake_home(monkeypatch, "/home/tester")
    assert shorten_path("/home/tester/projects/game") == "~/projects/game"


def test_short_path_unchanged(monkeypatch) -> None:
    """未超长的路径原样返回."""
    _fake_home(monkeypatch, "/home/tester")
    assert shorten_path("/tmp/a") == "/tmp/a"


def test_long_path_truncated_to_max_len(monkeypatch) -> None:
    """超长路径按 max_len 截断并以 ... 结尾."""
    _fake_home(monkeypatch, "/home/tester")
    result = shorten_path("/very/long/path/" + "x" * 60, max_len=35)
    assert len(result) == 35
    assert result.endswith("...")


def test_custom_max_len(monkeypatch) -> None:
    """自定义 max_len 决定截断长度."""
    _fake_home(monkeypatch, "/home/tester")
    assert shorten_path("abcdefghij", max_len=8) == "abcde..."
