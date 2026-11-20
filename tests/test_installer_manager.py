"""
installer.manager 插件安装管理测试.

覆盖下载缓存命中与回退、解压安装分支、标记读写与卸载匹配;
Store 用内存假实现, 不触碰网络.
"""

from __future__ import annotations

import asyncio
import zipfile
from typing import TYPE_CHECKING, Any

import pytest

from gdpm.cache.file_cache import FileCache
from gdpm.cache.index import make_cache_key
from gdpm.installer.manager import TAG_FILENAME, PluginManager

if TYPE_CHECKING:
    from pathlib import Path


def _make_zip(path: Path, members: dict[str, str]) -> Path:
    """用给定成员名/内容构造真实 zip."""
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return path


class FakeStore:
    """内存 Store 桩: 返回预置版本并记录下载调用."""

    def __init__(self, releases: list[dict[str, str]] | None = None) -> None:
        self.releases = releases or []
        self.download_calls: list[tuple[str, str, str]] = []
        self.closed = False

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]:
        """返回预置版本列表."""
        return self.releases

    async def download(
        self,
        publisher: str,
        slug: str,
        version: str,
        dest_dir: Path,
        on_progress: Any = None,
    ) -> Path:
        """在缓存目录写一个占位 zip 并返回路径."""
        self.download_calls.append((publisher, slug, version))
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / f"{publisher}_{slug}@{version}.zip"
        target.write_text("zip", encoding="utf-8")
        return target

    async def close(self) -> None:
        """记录关闭调用."""
        self.closed = True


def _manager(tmp_path: Path, store: FakeStore | None = None) -> PluginManager:
    """构造隔离在 tmp_path 下的管理器."""
    cache = FileCache(tmp_path / "cache")
    return PluginManager(tmp_path / "project" / "addons", cache, store=store)


def test_download_latest_populates_cache(tmp_path) -> None:
    """未指定版本时取最新版本并写入缓存索引."""
    store = FakeStore([{"version": "1.2.0"}])
    manager = _manager(tmp_path, store)

    path, version = asyncio.run(manager.download("pub", "slug"))

    assert version == "1.2.0"
    assert path.exists()
    assert store.download_calls == [("pub", "slug", "1.2.0")]
    entry = manager._index.get(make_cache_key("pub", "slug", "1.2.0"))
    assert entry is not None


def test_download_uses_cache_on_second_call(tmp_path) -> None:
    """第二次下载命中缓存, 不再调用 Store."""
    store = FakeStore([{"version": "1.2.0"}])
    manager = _manager(tmp_path, store)

    first, _ = asyncio.run(manager.download("pub", "slug"))
    second, _ = asyncio.run(manager.download("pub", "slug"))

    assert first == second
    assert len(store.download_calls) == 1


def test_download_ignores_cache_when_disabled(tmp_path) -> None:
    """use_cache=False 时跳过缓存直接下载."""
    store = FakeStore([{"version": "1.2.0"}])
    manager = _manager(tmp_path, store)

    asyncio.run(manager.download("pub", "slug"))
    asyncio.run(manager.download("pub", "slug", use_cache=False))

    assert len(store.download_calls) == 2


def test_download_invalidates_index_when_file_missing(tmp_path) -> None:
    """索引存在但缓存文件缺失时清理索引并重新下载."""
    store = FakeStore([{"version": "1.2.0"}])
    manager = _manager(tmp_path, store)

    first, _ = asyncio.run(manager.download("pub", "slug"))
    first.unlink()

    second, _ = asyncio.run(manager.download("pub", "slug"))

    assert second.exists()
    assert len(store.download_calls) == 2


def test_download_no_releases_raises(tmp_path) -> None:
    """没有可用版本时报错."""
    manager = _manager(tmp_path, FakeStore())

    with pytest.raises(ValueError, match="No releases found"):
        asyncio.run(manager.download("pub", "slug"))


def test_download_specific_version_normalizes_v_prefix(tmp_path) -> None:
    """指定版本去除 v 前缀匹配, 返回商店原始版本号."""
    store = FakeStore([{"version": "v2.0.0"}])
    manager = _manager(tmp_path, store)

    _path, version = asyncio.run(manager.download("pub", "slug", version="2.0.0"))

    assert version == "v2.0.0"
    assert store.download_calls == [("pub", "slug", "v2.0.0")]


def test_download_unknown_version_raises(tmp_path) -> None:
    """指定版本不存在时报错并带出版本号."""
    manager = _manager(tmp_path, FakeStore([{"version": "1.0.0"}]))

    with pytest.raises(ValueError, match=r"Version 9\.9\.9 not found"):
        asyncio.run(manager.download("pub", "slug", version="9.9.9"))


def test_analyze_delegates_to_zip_analysis(tmp_path) -> None:
    """analyze 直接返回压缩包结构分析结果."""
    zip_path = _make_zip(tmp_path / "p.zip", {"addons/foo/plugin.cfg": ""})
    result = _manager(tmp_path).analyze(zip_path)
    assert result.has_addons is True


def test_extract_to_path_writes_tag(tmp_path) -> None:
    """完整解压到目标路径并写入来源标记."""
    zip_path = _make_zip(tmp_path / "p.zip", {"addons/foo/plugin.cfg": "cfg"})
    manager = _manager(tmp_path)
    dest = tmp_path / "custom"

    manager.extract_to_path(zip_path, dest, "slug", "pub")

    assert (dest / "addons" / "foo" / "plugin.cfg").read_text() == "cfg"
    assert (dest / TAG_FILENAME).read_text() == "store+pub/slug"


def test_install_from_zip_addons_branch(tmp_path) -> None:
    """addons 布局安装到 addons 目录, 每个插件目录写标记."""
    zip_path = _make_zip(
        tmp_path / "p.zip",
        {"addons/foo/plugin.cfg": "cfg", "addons/bar/plugin.cfg": ""},
    )
    manager = _manager(tmp_path, FakeStore())

    result = manager.install_from_zip(zip_path, "slug", "pub")

    addons = tmp_path / "project" / "addons"
    assert result == {"dest": str(addons), "addon_dirs": ["bar", "foo"]}
    assert (addons / "foo" / TAG_FILENAME).read_text() == "store+pub/slug"
    assert (addons / "bar" / TAG_FILENAME).read_text() == "store+pub/slug"


def test_install_from_zip_custom_path(tmp_path) -> None:
    """显式自定义路径时完整解压并写标记."""
    zip_path = _make_zip(tmp_path / "p.zip", {"whatever.txt": "x"})
    manager = _manager(tmp_path)

    result = manager.install_from_zip(zip_path, "slug", "pub", dest_path="custom")

    dest = tmp_path / "project" / "custom"
    assert (dest / "whatever.txt").read_text() == "x"
    assert (dest / TAG_FILENAME).read_text() == "store+pub/slug"
    assert result == {"dest": str(dest), "addon_dirs": []}


def test_install_from_zip_custom_path_trailing_slash(tmp_path) -> None:
    """尾部斜杠时标记写入唯一根目录内部."""
    zip_path = _make_zip(tmp_path / "p.zip", {"root/plugin.cfg": ""})
    manager = _manager(tmp_path)

    manager.install_from_zip(zip_path, "slug", dest_path="custom/")

    tag = tmp_path / "project" / "custom" / "root" / TAG_FILENAME
    assert tag.read_text() == "store+slug"


def test_install_from_zip_asset_package(tmp_path) -> None:
    """纯资产包交由调用方处理."""
    zip_path = _make_zip(tmp_path / "p.zip", {"assets/a.png": "", "models/m.txt": ""})
    manager = _manager(tmp_path)

    result = manager.install_from_zip(zip_path, "slug")

    assert result["dest"] == ""
    assert result["has_assets"] is True


def test_install_from_zip_rejects_plain_archive(tmp_path) -> None:
    """既非 addon 也非资产包时要求使用 --path."""
    zip_path = _make_zip(tmp_path / "p.zip", {"a/x.txt": "", "b/y.txt": ""})
    manager = _manager(tmp_path)

    with pytest.raises(ValueError, match="not an addon"):
        manager.install_from_zip(zip_path, "slug")


def test_install_from_zip_raises_when_nothing_extracted(tmp_path) -> None:
    """识别为 addons 布局但无可解压目录时报错."""
    zip_path = _make_zip(tmp_path / "p.zip", {"addons/": ""})
    manager = _manager(tmp_path)

    with pytest.raises(ValueError, match="extraction failed"):
        manager.install_from_zip(zip_path, "slug")


def test_write_tag(tmp_path) -> None:
    """写入来源标记."""
    manager = _manager(tmp_path)
    target = tmp_path / "target"
    target.mkdir()

    manager.write_tag(target, "slug", "pub")

    assert (target / TAG_FILENAME).read_text() == "store+pub/slug"


def test_remove_only_matching_plugin(tmp_path) -> None:
    """只删除标记匹配 slug 的目录."""
    manager = _manager(tmp_path)
    addons = tmp_path / "project" / "addons"
    for name, source in (("foo", "store+pub/myplug"), ("bar", "store+pub/other")):
        (addons / name).mkdir(parents=True)
        (addons / name / TAG_FILENAME).write_text(source, encoding="utf-8")
    (addons / "loose.txt").write_text("x", encoding="utf-8")

    manager.remove("myplug")

    assert not (addons / "foo").exists()
    assert (addons / "bar").exists()
    assert (addons / "loose.txt").exists()


def test_remove_without_addons_dir_is_noop(tmp_path) -> None:
    """addons 目录不存在时卸载直接返回."""
    _manager(tmp_path).remove("slug")


def test_find_addon_dirs_and_is_installed(tmp_path) -> None:
    """按标记查找插件目录并判断安装状态."""
    manager = _manager(tmp_path)
    addons = tmp_path / "project" / "addons"
    (addons / "foo").mkdir(parents=True)
    (addons / "foo" / TAG_FILENAME).write_text("store+pub/myplug", encoding="utf-8")

    assert manager.find_addon_dirs("myplug") == ["foo"]
    assert manager.is_installed("myplug") is True
    assert manager.find_addon_dirs("other") == []
    assert manager.is_installed("other") is False


def test_close_skips_injected_store(tmp_path) -> None:
    """外部注入的 Store 不由管理器关闭."""
    store = FakeStore()
    manager = _manager(tmp_path, store)

    asyncio.run(manager.close())

    assert store.closed is False


def test_close_closes_owned_store(tmp_path, monkeypatch) -> None:
    """自建 Store 在关闭时一并关闭."""
    created = FakeStore()
    monkeypatch.setattr("gdpm.installer.manager.StoreClient", lambda: created)
    manager = _manager(tmp_path)

    asyncio.run(manager.close())

    assert created.closed is True
