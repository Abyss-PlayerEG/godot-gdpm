"""
帮助系统 Phase 4 验收测试 (CliRunner 快照式断言).

覆盖计划验收清单: 主/组/叶子三面关键行, 上次 bug 的反向断言
(出现 [--all], 不出现 --show_all), GDPM_LANG=zh 全中文冒烟,
缺 zh 词条回退英文不崩溃.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from gdpm.cli import i18n
from gdpm.cli.app import main
from gdpm.config.global_config import GlobalConfig
from gdpm.constants import DEVELOPER, REPO_URL

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _hermetic_language(monkeypatch) -> Iterator[None]:
    """语言环境封闭: 默认英文 (隔离真实配置与环境变量), 用例内自行设 GDPM_LANG."""
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig())
    monkeypatch.delenv("GDPM_LANG", raising=False)
    i18n.get_language.cache_clear()
    yield
    i18n.get_language.cache_clear()


def _invoke(monkeypatch, args: list[str], lang: str | None = None) -> str:
    """调用 CLI 并返回帮助输出 (折叠换行, 富文本按词换行不拆词)."""
    if lang:
        monkeypatch.setenv("GDPM_LANG", lang)
    result = CliRunner().invoke(main, args, prog_name="gdpm")
    assert result.exit_code == 0, result.output
    return result.output


def _flat(output: str) -> str:
    """把多行输出折叠成单行, 消除面板换行对断言的干扰."""
    return " ".join(output.split())


def test_main_help_english_categories_and_descriptions(monkeypatch) -> None:
    """主帮助: 分类标题与命令描述全部来自词典 (COMMANDS 字典已删除)."""
    out = _invoke(monkeypatch, ["--help"])

    for category in ("Project", "Dependencies", "Engine", "Config"):
        assert category in out
    assert "Initialize a new gdpm project" in out
    assert "Manage Godot engine versions" in out
    assert "Common Options" in out
    # 公共选项: -a/--about (原 --info 已改名, 与 info 子命令消歧)
    assert "-a, --about" in out
    assert "--info" not in out


def test_group_help_english(monkeypatch) -> None:
    """组帮助: 标题与子命令描述来自词典 (原 docstring 中文不再驱动渲染)."""
    out = _invoke(monkeypatch, ["godot", "--help"])

    assert "gdpm godot Manage Godot engine versions" in _flat(out)
    assert "List Godot engine versions" in out
    assert "Uninstall a Godot engine version" in out


def test_leaf_help_full_path_and_key_lines(monkeypatch) -> None:
    """叶子帮助: 全路径标题与 Usage, Choice 展开真实拼写."""
    out = _invoke(monkeypatch, ["godot", "list", "--help"])
    flat = _flat(out)

    assert "gdpm godot list List Godot engine versions" in flat
    assert "Usage: gdpm godot list" in flat
    assert "[--version VERSION]" in flat
    # stable-only: -c/--channel 已移除, 用法行不得出现
    assert "--channel" not in out


def test_usage_shows_real_option_spelling_not_dest_name(monkeypatch) -> None:
    """反向断言 (上次 bug 案发语义): search 出现 [--all], 不出现 --show_all."""
    out = _invoke(monkeypatch, ["search", "--help"])
    flat = _flat(out)

    assert "[--all]" in flat
    assert "--show_all" not in out


def test_usage_reverse_assertion_on_godot_list(monkeypatch) -> None:
    """godot list 同样带 -a/--all (dest=show_all): 用法行依旧显示 [--all]."""
    out = _invoke(monkeypatch, ["godot", "list", "--help"])
    flat = _flat(out)

    assert "[--all]" in flat
    assert "--show_all" not in out


def test_main_help_chinese(monkeypatch) -> None:
    """GDPM_LANG=zh 主帮助全中文: 分类/描述/用法/公共选项."""
    out = _invoke(monkeypatch, ["--help"], lang="zh")

    for category in ("项目", "依赖", "引擎", "配置"):
        assert category in out
    assert "初始化新的 gdpm 项目" in out
    assert "管理全局配置" in out
    assert "用法:" in out
    assert "公共选项" in out
    assert "显示帮助信息" in out


def test_group_help_chinese(monkeypatch) -> None:
    """GDPM_LANG=zh 组帮助: 标题与子命令描述全中文."""
    out = _invoke(monkeypatch, ["godot", "--help"], lang="zh")

    assert "gdpm godot 管理 Godot 引擎版本" in _flat(out)
    assert "列出 Godot 引擎版本" in out
    assert "卸载一个 Godot 引擎版本" in out


def test_leaf_help_chinese(monkeypatch) -> None:
    """GDPM_LANG=zh 叶子帮助: 标题与示例标签全中文, 命令原文不动."""
    out = _invoke(monkeypatch, ["config", "set", "--help"], lang="zh")
    flat = _flat(out)

    assert "gdpm config set 设置全局配置项" in flat
    assert "设置并行下载数" in out
    assert "$ gdpm config set parallel_downloads 8" in flat
    assert "选项" not in out  # 无选项命令不渲染 Options 面板


def test_missing_zh_entry_falls_back_to_english(monkeypatch) -> None:
    """回退验证: 删掉某条 zh 词条后该条显示英文而非崩溃."""
    monkeypatch.setenv("GDPM_LANG", "zh")
    original = i18n._COMMANDS["init"]
    monkeypatch.setitem(i18n._COMMANDS, "init", {"en": original["en"]})

    out = _invoke(monkeypatch, ["--help"])

    assert original["en"] in out
    assert "初始化新的 gdpm 项目" not in out


def test_language_config_drives_help(monkeypatch) -> None:
    """配置 [ui] language=zh 且无环境变量时, 帮助同样全中文."""
    monkeypatch.setattr(i18n, "read_global_config", lambda: GlobalConfig(language="zh"))

    out = _invoke(monkeypatch, ["--help"])

    assert "项目" in out
    assert "初始化新的 gdpm 项目" in out


def test_about_shows_developer_info(monkeypatch) -> None:
    """about 屏含静态开发者信息与仓库 (网络失败也显示, 面板标题 GDPM-About)."""
    monkeypatch.setattr(
        "httpx.get",
        lambda *args, **kwargs: SimpleNamespace(status_code=500),
    )

    result = CliRunner().invoke(main, ["-a"], prog_name="gdpm")

    assert result.exit_code == 0
    out = result.output
    assert "GDPM-About" in out
    assert f"Developer: {DEVELOPER}" in out
    assert REPO_URL in out


def test_about_screen_chinese(monkeypatch) -> None:
    """GDPM_LANG=zh: about 屏标题/标语/开发者标签/贡献者面板全中文."""
    monkeypatch.setenv("GDPM_LANG", "zh")
    monkeypatch.setattr(
        "httpx.get",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=200, json=lambda: [{"login": "dev"}]
        ),
    )

    result = CliRunner().invoke(main, ["-a"], prog_name="gdpm")

    assert result.exit_code == 0
    out = result.output
    assert "GDPM 关于" in out
    assert "Godot 依赖包管理器" in out
    assert f"开发者: {DEVELOPER}" in out
    assert "贡献者" in out
