"""
help.py 纯函数构建器测试 (Phase 2, 先测后码).

固化已修语义: Usage 用真实选项拼写 (--all 而非 --show_all),
Choice 展开全部合法值, 参数按必选用 <>/[], 全路径带组名;
命令清单按 category 自动分组且描述取自词典 (docstring 不再驱动 help);
示例标签按语言查词典.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click
import pytest

from gdpm.cli import i18n
from gdpm.cli.help import (
    build_command_groups,
    build_example_rows,
    build_option_rows,
    build_usage,
    command_key,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _reset_language_cache() -> Iterator[None]:
    """语言解析有进程内缓存, 每个用例前后清空避免串扰."""
    i18n.get_language.cache_clear()
    yield
    i18n.get_language.cache_clear()


@click.group()
def _root() -> None:
    """根命令组."""


def _make_group(name: str) -> click.Group:
    @click.group(name=name)
    def group() -> None:
        """占位组."""

    return group


def test_usage_uses_real_option_spelling() -> None:
    """反向断言: --all (真实拼写) 而非 --show_all (Python 变量名) — 上次 bug 案发地."""

    @click.command()
    @click.option("--all", "show_all", is_flag=True)
    def leaf(show_all: bool) -> None:
        """示例命令."""

    ctx = click.Context(
        leaf, info_name="leaf", parent=click.Context(_root, info_name="gdpm")
    )
    usage = build_usage(ctx)

    assert "[--all]" in usage
    assert "--show_all" not in usage
    assert usage.startswith("gdpm leaf")


def test_usage_expands_choice_values_short_only() -> None:
    """短选项 Choice: [-c stable|rc|beta] 展开全部合法值."""

    @click.command()
    @click.option("-c", type=click.Choice(["stable", "rc", "beta"]), default=None)
    def leaf(c: str | None) -> None:
        """示例命令."""

    ctx = click.Context(
        leaf, info_name="leaf", parent=click.Context(_root, info_name="gdpm")
    )
    assert "[-c stable|rc|beta]" in build_usage(ctx)


def test_usage_expands_choice_values_long_form() -> None:
    """长短选项并存时用长拼写: [--channel stable|rc|beta|alpha|dev]."""

    @click.command()
    @click.option(
        "-c",
        "--channel",
        type=click.Choice(["stable", "rc", "beta", "alpha", "dev"]),
        default=None,
    )
    def leaf(channel: str | None) -> None:
        """示例命令."""

    ctx = click.Context(
        leaf, info_name="leaf", parent=click.Context(_root, info_name="gdpm")
    )
    assert "[--channel stable|rc|beta|alpha|dev]" in build_usage(ctx)


def test_usage_argument_brackets_by_requiredness() -> None:
    """必填参数 <name>, 可选参数 [name], metavar 优先 (use 的 <ID> 语义)."""

    @click.command()
    @click.argument("plugin")
    @click.argument("engine_id", metavar="ID")
    @click.argument("dest", required=False)
    def leaf(plugin: str, engine_id: str, dest: str | None) -> None:
        """示例命令."""

    ctx = click.Context(
        leaf, info_name="leaf", parent=click.Context(_root, info_name="gdpm")
    )
    usage = build_usage(ctx)

    assert "<plugin>" in usage
    assert "<ID>" in usage
    assert "[dest]" in usage


def test_usage_includes_full_group_path() -> None:
    """子命令 Usage 带完整组路径: gdpm godot list."""

    @click.command(name="list")
    @click.option("--remote", "-r", is_flag=True)
    def leaf(remote: bool) -> None:
        """示例命令."""

    group = _make_group("godot")
    root_ctx = click.Context(_root, info_name="gdpm")
    group_ctx = click.Context(group, info_name="godot", parent=root_ctx)
    ctx = click.Context(leaf, info_name="list", parent=group_ctx)

    usage = build_usage(ctx)

    assert usage.startswith("gdpm godot list")
    assert "[--remote]" in usage


def test_usage_value_option_shows_metavar() -> None:
    """值选项: [--version VERSION] / 无 metavar 时回退 VALUE."""

    @click.command()
    @click.option("-V", "--version", "version_filter", default="", metavar="VERSION")
    @click.option("--limit")
    def leaf(version_filter: str, limit: str | None) -> None:
        """示例命令."""

    ctx = click.Context(
        leaf, info_name="leaf", parent=click.Context(_root, info_name="gdpm")
    )
    usage = build_usage(ctx)

    assert "[--version VERSION]" in usage
    assert "[--limit VALUE]" in usage


def test_command_key_derives_group_prefix() -> None:
    """词典键推导: 根命令裸名, 子命令点号路径, 组用自身名."""
    root_ctx = click.Context(_root, info_name="gdpm")

    @click.command(name="list")
    def leaf() -> None:
        """示例."""

    leaf_ctx = click.Context(leaf, info_name="list", parent=root_ctx)
    assert command_key(leaf_ctx) == "list"

    group = _make_group("godot")
    group_ctx = click.Context(group, info_name="godot", parent=root_ctx)
    assert command_key(group_ctx) == "godot"

    nested_ctx = click.Context(leaf, info_name="list", parent=group_ctx)
    assert command_key(nested_ctx) == "godot.list"


def test_option_rows_annotate_defaults() -> None:
    """选项行: 普通选项带 (default: x), 默认开启标志带 (default: on)."""

    @click.command()
    @click.option("--limit", default=5)
    @click.option("--strict", is_flag=True, default=True)
    @click.option("--check", is_flag=True, default=False)
    def leaf(limit: int, strict: bool, check: bool) -> None:
        """示例命令."""

    rows = dict(build_option_rows(leaf.params, "en"))

    assert "(default: 5)" in rows["  --limit"]
    assert "(default: on)" in rows["  --strict"]
    assert "(default" not in rows["  --check"]
    zh_first = build_option_rows(leaf.params, "zh")[0][1]
    assert "(默认: 5)" in zh_first


def test_example_rows_translate_labels() -> None:
    """示例行: 标签查词典换语言, 命令原文不动."""
    examples = [("gdpm godot list", "List installed versions")]

    en_rows = build_example_rows(examples, "en")
    zh_rows = build_example_rows(examples, "zh")

    assert en_rows == ["  [dim]# List installed versions[/dim]", "  $ gdpm godot list"]
    assert zh_rows[0] == "  [dim]# 列出已安装版本[/dim]"
    assert zh_rows[1] == "  $ gdpm godot list"


def _fake_cmd(category: str | None = None, help_text: str = "") -> click.Command:
    """构造带 category 属性的命令对象 (描述故意与词典不同)."""

    @click.command()
    def cmd() -> None:
        """docstring 不参与 help 渲染."""

    cmd.help = help_text
    if category is not None:
        cmd.category = category  # type: ignore[attr-defined]
    return cmd


def test_command_groups_categorize_in_dictionary_order() -> None:
    """按 category 自动分组, 展示顺序取词典定义序, 未分类进兜底组."""
    commands = {
        "add": _fake_cmd("dependencies"),
        "init": _fake_cmd("project"),
        "godot": _fake_cmd("engine"),
        "config": _fake_cmd("config"),
        "mystery": _fake_cmd(None),
        "rogue": _fake_cmd("not-a-real-category"),
    }

    groups = build_command_groups(commands, "en")
    names = [name for name, _ in groups]

    assert names == ["Project", "Dependencies", "Engine", "Config", "Other"]
    assert ("mystery", "mystery") in dict(groups)["Other"]
    assert ("rogue", "rogue") in dict(groups)["Other"]


def test_command_group_description_comes_from_dictionary() -> None:
    """描述唯一事实源是词典: 即便 cmd.help 是别的文本也返回词典词条."""
    commands = {"list": _fake_cmd("project", help_text="完全不同的一行")}

    groups = build_command_groups(commands, "en")

    assert groups == [("Project", [("list", "List installed plugins")])]


def test_command_groups_chinese_category_names() -> None:
    """语言切换后分类名走词典."""
    commands = {"init": _fake_cmd("project")}

    groups = build_command_groups(commands, "zh")

    assert groups[0][0] == "项目"
