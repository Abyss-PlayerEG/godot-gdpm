"""
scripts/version.py 发版脚本测试.

脚本曾零覆盖 (且不在任何检查门内): docstring 的 tag 映射表即规格,
外加两个历史 bug 的回归锁 —— 交互模式跳过版本校验、正则替换静默失败.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


def _load_script() -> ModuleType:
    """按文件路径加载 scripts/version.py (scripts 非包, 不可直接 import)."""
    path = Path(__file__).resolve().parent.parent / "scripts" / "version.py"
    spec = importlib.util.spec_from_file_location("gdpm_version_script", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT = _load_script()


@pytest.fixture()
def script(tmp_path: Path, monkeypatch) -> ModuleType:
    """脚本实例 + 指向临时文件的 pyproject/__init__ (不碰真实仓库)."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "gdpm"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    init = tmp_path / "__init__.py"
    init.write_text('__version__ = "0.1.0"\n__tag__ = ""\n', encoding="utf-8")
    monkeypatch.setattr(SCRIPT, "PYPROJECT_FILE", pyproject)
    monkeypatch.setattr(SCRIPT, "INIT_FILE", init)
    return SCRIPT


@pytest.mark.parametrize(
    ("version", "tag", "expected"),
    [
        ("0.0.3", "", "0.0.3"),
        ("0.0.3", "dev", "0.0.3.dev1"),
        ("0.0.3", "alpha", "0.0.3a1"),
        ("0.0.3", "beta", "0.0.3b1"),
        ("0.0.3", "rc", "0.0.3rc1"),
        ("0.0.3", "beta-2", "0.0.3b2"),
        ("0.0.3", "rc3", "0.0.3rc3"),
    ],
)
def test_get_pypi_version_matches_spec(version: str, tag: str, expected: str) -> None:
    """docstring 规格表逐行锁定."""
    assert SCRIPT.get_pypi_version(version, tag) == expected


def test_parse_tag() -> None:
    assert SCRIPT.parse_tag("beta-2") == ("beta", 2)
    assert SCRIPT.parse_tag("beta2") == ("beta", 2)
    assert SCRIPT.parse_tag("rc3") == ("rc", 3)
    assert SCRIPT.parse_tag("beta") == ("beta", 1)
    assert SCRIPT.parse_tag("") == ("", 1)
    assert SCRIPT.parse_tag("garbage") == ("garbage", 1)


def test_validate_version() -> None:
    assert SCRIPT.validate_version("0.1.0")
    for bad in ("1.0", "abc", "0.1.0.1", "v1.2.3", "0.1.0-beta"):
        assert not SCRIPT.validate_version(bad), bad


def test_validate_tag() -> None:
    for ok in ("", "dev", "alpha", "beta", "rc", "beta-2", "rc3"):
        assert SCRIPT.validate_tag(ok), ok
    for bad in ("gamma", "beta-x", "nightly"):
        assert not SCRIPT.validate_tag(bad), bad


def test_update_files_roundtrip(script: ModuleType) -> None:
    """写入后两文件一致, 且 read_current 能反解出 base+tag."""
    script.update_files("1.2.3", "beta-2")

    assert 'version = "1.2.3b2"' in script.PYPROJECT_FILE.read_text()
    init = script.INIT_FILE.read_text()
    assert '__version__ = "1.2.3b2"' in init
    assert '__tag__ = "beta"' in init

    base, tag = script.read_current()
    assert base == "1.2.3"
    assert tag == "beta-2"


def test_update_files_fails_when_pattern_missing(script: ModuleType) -> None:
    """回归锁 (bug): 模式零匹配必须报错退出, 且不落盘任何一半."""
    script.INIT_FILE.write_text("# no version lines here\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        script.update_files("9.9.9", "")

    # all-or-nothing: pyproject 未被改写
    assert 'version = "0.1.0"' in script.PYPROJECT_FILE.read_text()


def test_interactive_rejects_bad_version(
    script: ModuleType, monkeypatch, capsys
) -> None:
    """回归锁 (bug): 交互模式同样校验版本格式, 垃圾输入不落盘."""
    monkeypatch.setattr("builtins.input", lambda _prompt: "not-a-version")

    code = script.main([])

    assert code == 1
    assert "Invalid version format" in capsys.readouterr().out
    assert 'version = "0.1.0"' in script.PYPROJECT_FILE.read_text()


def test_interactive_happy_path(script: ModuleType, monkeypatch, capsys) -> None:
    """交互模式: 空 tag = stable, 正常落盘."""
    answers = iter(["1.0.0", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    code = script.main([])

    assert code == 0
    init = script.INIT_FILE.read_text()
    assert '__version__ = "1.0.0"' in init
    assert '__tag__ = ""' in init
    assert "Updated" in capsys.readouterr().out


def test_cli_keeps_current_tag_with_note(script: ModuleType, capsys) -> None:
    """CLI 省略 tag 沿用当前 tag, 并显式提示 (不再静默)."""
    script.update_files("0.1.0", "beta")
    capsys.readouterr()  # 清空前置输出

    code = script.main(["1.0.0"])

    assert code == 0
    out = capsys.readouterr().out
    assert 'keeping current tag "beta"' in out
    assert '__version__ = "1.0.0b1"' in script.INIT_FILE.read_text()
    assert '__tag__ = "beta"' in script.INIT_FILE.read_text()


def test_cli_explicit_empty_tag_clears(script: ModuleType) -> None:
    """显式 "" = stable, 清掉当前 tag."""
    script.update_files("0.1.0", "rc")

    assert script.main(["1.0.0", ""]) == 0
    assert '__tag__ = ""' in script.INIT_FILE.read_text()
    assert 'version = "1.0.0"' in script.PYPROJECT_FILE.read_text()


def test_cli_rejects_invalid_inputs(script: ModuleType, capsys) -> None:
    """CLI 模式: 非法版本/非法 tag 返回 1 且不落盘."""
    assert script.main(["not-a-version"]) == 1
    assert script.main(["1.0.0", "gamma"]) == 1
    assert 'version = "0.1.0"' in script.PYPROJECT_FILE.read_text()
    capsys.readouterr()  # 输出非空即可, 语义由上面的退出码锁定


def test_cli_rejects_extra_args(script: ModuleType) -> None:
    """argparse 接管参数: 多余参数报错退出 (旧实现静默忽略)."""
    with pytest.raises(SystemExit):
        script.main(["1.0.0", "beta", "extra"])
