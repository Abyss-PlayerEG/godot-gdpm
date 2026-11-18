"""
shell 补全测试: 脚本生成与描述语言切换.

补全描述由 Tab 时动态调用 gdpm 生成, 读取 click 的 short_help / Option.help,
因此需要用 apply_runtime_help 同步语言后断言输出.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from gdpm.cli import i18n
from gdpm.cli.app import main
from gdpm.cli.help import apply_runtime_help
from gdpm.config.global_config import GlobalConfig

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _hermetic_language(monkeypatch) -> Iterator[None]:
    """语言环境封闭: 隔离真实配置与环境变量."""
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig())
    monkeypatch.delenv("GDPM_LANG", raising=False)
    i18n.get_language.cache_clear()
    yield
    i18n.get_language.cache_clear()


def _complete(monkeypatch, words: str, lang: str) -> str:
    """模拟 Tab 时 click 的补全协议, 返回原始完成项输出."""
    monkeypatch.setenv("GDPM_LANG", lang)
    i18n.get_language.cache_clear()
    apply_runtime_help(main)
    monkeypatch.setenv("COMP_WORDS", words)
    index = len(words.split()) - (0 if words.endswith(" ") else 1)
    monkeypatch.setenv("COMP_CWORD", str(index))
    monkeypatch.setenv("_GDPM_COMPLETE", "zsh_complete")
    result = CliRunner().invoke(main, [], prog_name="gdpm")
    assert result.exit_code == 0
    return result.output


def test_completion_script_generation() -> None:
    """--completion 生成真实脚本 (源码模式下不再回退为帮助输出)."""
    result = CliRunner().invoke(main, ["--completion", "zsh"], prog_name="gdpm")

    assert result.exit_code == 0
    assert "#compdef gdpm" in result.output
    assert "_GDPM_COMPLETE=zsh_complete" in result.output


def test_completion_descriptions_follow_language(monkeypatch) -> None:
    """根命令补全描述跟随 GDPM_LANG, 且可反复切换."""
    out_en = _complete(monkeypatch, "gdpm ", "en")
    assert "Add plugins to the project" in out_en
    assert "添加一个或多个插件到项目" not in out_en

    out_zh = _complete(monkeypatch, "gdpm ", "zh")
    assert "添加一个或多个插件到项目" in out_zh
    assert "Add plugins to the project" not in out_zh

    # 切回英文仍然正确 (选项原文已缓存, 不会二次翻译)
    assert "Add plugins to the project" in _complete(monkeypatch, "gdpm ", "en")


def test_group_completion_descriptions_follow_language(monkeypatch) -> None:
    """组内子命令补全描述跟随语言."""
    assert "Add a local Godot engine" in _complete(monkeypatch, "gdpm godot ", "en")
    assert "添加本地 Godot 引擎" in _complete(monkeypatch, "gdpm godot ", "zh")


def test_option_completion_descriptions_follow_language(monkeypatch) -> None:
    """选项补全描述跟随语言 (Option.help 走 _OPTION_HELP 词典)."""
    assert "Add as dev dependency" in _complete(monkeypatch, "gdpm add --", "en")
    assert "作为开发依赖添加" in _complete(monkeypatch, "gdpm add --", "zh")
