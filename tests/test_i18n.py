"""
i18n 词典与语言解析测试 (Phase 1).

锁定三件事: 回退链 (目标语言 -> en -> 键名), 语言优先级
(GDPM_LANG > [ui] language > en), 词典覆盖率 (examples 标签与
命令键全部有词条, 防止新增命令/示例漏翻).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from gdpm.cli import i18n
from gdpm.config.global_config import GlobalConfig

if TYPE_CHECKING:
    from collections.abc import Iterator

CLI_ROOT = Path(__file__).resolve().parent.parent / "src" / "gdpm" / "cli"

# 帮助面出现的全部命令键: 根命令 16 + godot 9 + config 3 + cache 2
ROOT_COMMANDS = (
    "init",
    "create",
    "sync",
    "lock",
    "list",
    "status",
    "add",
    "remove",
    "update",
    "search",
    "info",
    "cache",
    "export",
    "import",
    "godot",
    "config",
)
GROUP_COMMANDS = (
    "godot.list",
    "godot.install",
    "godot.uninstall",
    "godot.open",
    "godot.info",
    "godot.add",
    "godot.remove",
    "godot.use",
    "godot.default",
    "config.set",
    "config.open",
    "cache.info",
    "cache.clean",
)
ALL_COMMAND_KEYS = ROOT_COMMANDS + GROUP_COMMANDS


@pytest.fixture(autouse=True)
def _reset_language_cache() -> Iterator[None]:
    """语言解析有进程内缓存, 每个用例前后清空避免串扰."""
    i18n.get_language.cache_clear()
    yield
    i18n.get_language.cache_clear()


def _example_labels() -> set[str]:
    """AST 扫描全部命令文件的 examples= 声明, 收集标签原文."""
    labels: set[str] = set()
    for path in CLI_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                for kw in dec.keywords:
                    if kw.arg == "examples":
                        for _, desc in ast.literal_eval(kw.value):
                            labels.add(desc)
    return labels


def test_t_returns_translation_for_zh() -> None:
    """目标语言有词条: 返回译文."""
    assert i18n.t("list", "zh") == "列出已安装的插件"
    assert i18n.t("project", "zh") == "项目"


def test_t_falls_back_to_english_for_untranslated() -> None:
    """目标语言缺词条: 回退英文而非报错 (加语言时的默认行为)."""
    assert i18n.t("list", "fr") == "List installed plugins"
    assert i18n.t("godot.open", "fr") == "Open Godot editor for the current project"


def test_t_falls_back_to_key_for_missing_entry() -> None:
    """键整体缺失: 返回键名本身 (响亮暴露, 不静默)."""
    assert i18n.t("no.such.key") == "no.such.key"
    assert i18n.t("no.such.key", "zh") == "no.such.key"


def test_t_example_label_uses_key_as_english() -> None:
    """示例标签词典只有 zh 条目: 英文即键名, 未知语言回退键名."""
    assert i18n.t("Output as JSON", "zh") == "以 JSON 格式输出"
    assert i18n.t("Output as JSON", "fr") == "Output as JSON"


def test_t_defaults_to_configured_language(monkeypatch) -> None:
    """t() 不传 lang 时按 get_language() 解析."""
    monkeypatch.delenv("GDPM_LANG", raising=False)
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig(language="zh"))
    assert i18n.t("list") == "列出已安装的插件"


def test_language_env_overrides_config(monkeypatch) -> None:
    """GDPM_LANG 环境变量优先于配置文件."""
    monkeypatch.setenv("GDPM_LANG", "zh")
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig(language="en"))
    assert i18n.get_language() == "zh"


def test_language_falls_back_to_config(monkeypatch) -> None:
    """无环境变量时读配置 [ui] language."""
    monkeypatch.delenv("GDPM_LANG", raising=False)
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig(language="zh"))
    assert i18n.get_language() == "zh"


def test_language_defaults_to_en(monkeypatch) -> None:
    """环境变量与配置都没有时默认英文."""
    monkeypatch.delenv("GDPM_LANG", raising=False)
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig())
    assert i18n.get_language() == "en"


def test_language_env_is_normalized(monkeypatch) -> None:
    """环境变量地区后缀与大小写被归一化 (zh_CN / ZH-CN -> zh)."""
    monkeypatch.setenv("GDPM_LANG", "zh_CN")
    assert i18n.get_language() == "zh"
    monkeypatch.setenv("GDPM_LANG", "ZH-CN")
    assert i18n.get_language() == "zh"


def test_empty_env_treated_as_unset(monkeypatch) -> None:
    """空串环境变量等价于未设置, 走配置回退."""
    monkeypatch.setenv("GDPM_LANG", "  ")
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig(language="zh"))
    assert i18n.get_language() == "zh"


def test_all_command_keys_have_translations() -> None:
    """帮助面出现的每个命令键都必须有 en+zh 词条 (含新写英文的子命令)."""
    missing = [
        key
        for key in ALL_COMMAND_KEYS
        if not {"en", "zh"} <= set(i18n._COMMANDS.get(key, {}))
    ]
    assert not missing, f"命令词条缺失: {missing}"


def test_all_example_labels_have_zh() -> None:
    """全部 examples= 标签 (扫描源码) 都有 zh 译文, 防止新增示例漏翻."""
    labels = _example_labels()
    missing = {
        label for label in labels if "zh" not in i18n._EXAMPLE_LABELS.get(label, {})
    }
    assert not missing, f"示例标签缺 zh 词条: {missing}"


def test_all_categories_have_translations() -> None:
    """分类词典 en+zh 齐全且顺序 other 最后 (兜底组)."""
    for key in i18n.category_keys():
        assert {"en", "zh"} <= set(i18n._CATEGORIES[key])
    assert i18n.category_keys()[-1] == "other"


def test_render_entries_have_explicit_english() -> None:
    """回退链 en 环节真实存在: 命令/分类/ui 词条必须显式带 en."""
    for table in (i18n._COMMANDS, i18n._CATEGORIES, i18n._UI):
        missing = [key for key, entry in table.items() if "en" not in entry]
        assert not missing, f"缺 en 词条: {missing}"
