"""
utils.zip 压缩包分析与解压测试.

覆盖 addons/ 布局识别、三种解压策略与 zip-slip 路径穿越防护.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

import pytest

from gdpm.utils.zip import (
    analyze_zip,
    extract_addon_from_zip,
    extract_full_zip,
    extract_zip,
)

if TYPE_CHECKING:
    from pathlib import Path


def _make_zip(path: Path, members: dict[str, str]) -> Path:
    """用给定成员名/内容构造真实 zip."""
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return path


def test_analyze_detects_root_addons(tmp_path) -> None:
    """根部 addons/ 前缀的目录被识别为插件."""
    zip_path = _make_zip(
        tmp_path / "plugin.zip",
        {
            "addons/foo/plugin.cfg": "",
            "addons/foo/main.gd": "",
            "addons/bar/plugin.cfg": "",
        },
    )
    result = analyze_zip(zip_path)
    assert result.has_addons is True
    assert result.addon_dirs == ["bar", "foo"]


def test_analyze_detects_nested_addons(tmp_path) -> None:
    """嵌套 prefix/addons/ 前缀同样识别."""
    zip_path = _make_zip(tmp_path / "plugin.zip", {"pkg/addons/nest/plugin.cfg": ""})
    result = analyze_zip(zip_path)
    assert result.has_addons is True
    assert result.addon_dirs == ["nest"]


def test_analyze_detects_plugin_cfg_dir(tmp_path) -> None:
    """顶层目录含 plugin.cfg 时视为插件, 不要求 addons 前缀."""
    zip_path = _make_zip(
        tmp_path / "plugin.zip",
        {"myplug/plugin.cfg": "", "docs/readme.md": ""},
    )
    result = analyze_zip(zip_path)
    assert result.has_addons is True
    assert result.addon_dirs == ["myplug"]


def test_analyze_single_top_dir_is_plugin(tmp_path) -> None:
    """仅一个顶层目录时按单一插件目录处理."""
    zip_path = _make_zip(tmp_path / "plugin.zip", {"solo/a.txt": "a"})
    result = analyze_zip(zip_path)
    assert result.has_addons is True
    assert result.addon_dirs == ["solo"]


def test_analyze_detects_assets(tmp_path) -> None:
    """资产特征目录被识别, 且不误判为插件."""
    zip_path = _make_zip(
        tmp_path / "assets.zip",
        {"assets/a.png": "", "sounds/b.ogg": ""},
    )
    result = analyze_zip(zip_path)
    assert result.has_addons is False
    assert result.has_assets is True
    assert result.asset_dirs == ["assets", "sounds"]


def test_analyze_plain_archive(tmp_path) -> None:
    """无插件也无资产特征时两个标志都为 False."""
    zip_path = _make_zip(tmp_path / "plain.zip", {"a/x.txt": "", "b/y.txt": ""})
    result = analyze_zip(zip_path)
    assert result.has_addons is False
    assert result.has_assets is False


def test_analyze_empty_zip(tmp_path) -> None:
    """空归档不产生任何标志."""
    zip_path = _make_zip(tmp_path / "empty.zip", {})
    result = analyze_zip(zip_path)
    assert result.has_addons is False
    assert result.has_assets is False


def test_extract_addons_prefix(tmp_path) -> None:
    """addons/ 布局解压到目标目录, 返回排序后的插件目录名."""
    zip_path = _make_zip(
        tmp_path / "plugin.zip",
        {
            "addons/foo/plugin.cfg": "cfg",
            "addons/foo/sub/x.gd": "x",
            "addons/bar/plugin.cfg": "bar",
        },
    )
    dest = tmp_path / "dest"
    dirs = extract_addon_from_zip(zip_path, dest, "foo")
    assert dirs == ["bar", "foo"]
    assert (dest / "foo" / "plugin.cfg").read_text() == "cfg"
    assert (dest / "foo" / "sub" / "x.gd").read_text() == "x"


def test_extract_nested_addons_prefix(tmp_path) -> None:
    """嵌套 addons/ 前缀按相对路径解压."""
    zip_path = _make_zip(tmp_path / "plugin.zip", {"pkg/addons/nest/plugin.cfg": "n"})
    dest = tmp_path / "dest"
    dirs = extract_addon_from_zip(zip_path, dest, "nest")
    assert dirs == ["nest"]
    assert (dest / "nest" / "plugin.cfg").read_text() == "n"


def test_extract_preserves_plugin_cfg_dir(tmp_path) -> None:
    """plugin.cfg 顶层目录连同目录本身一起保留."""
    zip_path = _make_zip(
        tmp_path / "plugin.zip",
        {"myplug/plugin.cfg": "cfg", "myplug/x.gd": "x"},
    )
    dest = tmp_path / "dest"
    dirs = extract_addon_from_zip(zip_path, dest, "myplug")
    assert dirs == ["myplug"]
    assert (dest / "myplug" / "plugin.cfg").read_text() == "cfg"


def test_extract_single_top_dir_preserves_dir(tmp_path) -> None:
    """单一顶层目录作为插件目录保留."""
    zip_path = _make_zip(tmp_path / "plugin.zip", {"solo/a.txt": "a"})
    dest = tmp_path / "dest"
    dirs = extract_addon_from_zip(zip_path, dest, "solo")
    assert dirs == ["solo"]
    assert (dest / "solo" / "a.txt").read_text() == "a"


def test_extract_creates_directory_entries(tmp_path) -> None:
    """目录成员创建对应空目录."""
    zip_path = _make_zip(
        tmp_path / "plugin.zip",
        {"addons/foo/": "", "addons/foo/a.gd": "a"},
    )
    dest = tmp_path / "dest"
    extract_addon_from_zip(zip_path, dest, "foo")
    assert (dest / "foo").is_dir()
    assert (dest / "foo" / "a.gd").read_text() == "a"


def test_extract_empty_zip_returns_empty(tmp_path) -> None:
    """空归档没有可解压内容."""
    zip_path = _make_zip(tmp_path / "empty.zip", {})
    assert extract_addon_from_zip(zip_path, tmp_path / "dest", "x") == []


def test_extract_unrecognized_layout_returns_empty(tmp_path) -> None:
    """无法识别的多顶层目录布局返回空列表."""
    zip_path = _make_zip(tmp_path / "plain.zip", {"a/x.txt": "", "b/y.txt": ""})
    assert extract_addon_from_zip(zip_path, tmp_path / "dest", "x") == []


@pytest.mark.parametrize(
    "member",
    [
        "addons/../../evil.py",
        "addons/..\\..\\evil.py",
        "addons//tmp/evil.py",
    ],
)
def test_extract_rejects_zip_slip(tmp_path, member: str) -> None:
    """越界成员拒绝解压, 目标目录之外不产生文件."""
    zip_path = _make_zip(tmp_path / "evil.zip", {member: "pwned"})
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(ValueError, match="Unsafe path"):
        extract_addon_from_zip(zip_path, dest, "p")
    assert not (tmp_path / "evil.py").exists()


def test_extract_full_zip(tmp_path) -> None:
    """完整解压保留归档目录结构."""
    zip_path = _make_zip(tmp_path / "p.zip", {"a/b.txt": "b"})
    dest = tmp_path / "out"
    extract_full_zip(zip_path, dest)
    assert (dest / "a" / "b.txt").read_text() == "b"


def test_extract_zip(tmp_path) -> None:
    """基础解压入口行为与完整解压一致."""
    zip_path = _make_zip(tmp_path / "p.zip", {"c/d.txt": "d"})
    dest = tmp_path / "out"
    extract_zip(zip_path, dest)
    assert (dest / "c" / "d.txt").read_text() == "d"
