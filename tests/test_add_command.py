"""
gdpm add 命令测试.

覆盖在线安装主链路、跳过/拒绝分支、错误提示与本地 zip 安装;
Store/Manager 用内存假实现, 项目文件全部落在 tmp_path.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from gdpm.cli.commands.add import _parse_spec, add
from gdpm.config.project import ProjectConfig, write_project_config
from gdpm.models.dependency import Dependency
from gdpm.store.utils import ResolvedPlugin


class FakeStore:
    """Store 桩: 预置详情/版本/搜索结果并记录关闭调用."""

    def __init__(
        self,
        versions: list[dict[str, str]] | None = None,
        tags: list[str] | None = None,
        search_results: list[SimpleNamespace] | None = None,
        plugin_error: Exception | None = None,
    ) -> None:
        self.versions = versions if versions is not None else [{"version": "v1.0.0"}]
        self.tags = tags if tags is not None else ["addon"]
        self.search_results = search_results or []
        self.plugin_error = plugin_error
        self.closed = False

    async def get_plugin(self, publisher: str, slug: str) -> SimpleNamespace:
        """返回仅含 tags 的插件详情."""
        if self.plugin_error:
            raise self.plugin_error
        return SimpleNamespace(tags=self.tags)

    async def get_versions(self, publisher: str, slug: str) -> list[dict[str, str]]:
        """返回预置版本列表."""
        return self.versions

    async def search(self, query: str, limit: int = 5) -> list[SimpleNamespace]:
        """返回预置搜索结果."""
        return self.search_results

    async def close(self) -> None:
        """记录关闭调用."""
        self.closed = True


class FakeManager:
    """PluginManager 桩: 记录下载/安装参数并模拟进度回调."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.downloads: list[tuple[str, str, str]] = []
        self.installs: list[tuple[Path, str, str]] = []

    async def download(
        self,
        publisher: str,
        slug: str,
        version: str = "",
        on_progress=None,
    ) -> tuple[Path, str]:
        """记录调用, 触发一次进度回调后返回假路径."""
        self.downloads.append((publisher, slug, version))
        if on_progress:
            on_progress(5, 10, 1.0)
        if self.error:
            raise self.error
        return Path("pkg.zip"), "v1.0.0"

    def install_from_zip(self, zip_path: Path, slug: str, publisher: str = "") -> None:
        """记录安装调用."""
        self.installs.append((zip_path, slug, publisher))


def _ctx(tmp_path: Path) -> SimpleNamespace:
    """构造带真实配置对象与临时路径的项目上下文."""
    config = ProjectConfig(name="proj")
    config_path = tmp_path / "gdproject.toml"
    write_project_config(config, config_path)
    return SimpleNamespace(
        root=tmp_path,
        config=config,
        config_path=config_path,
        addons_dir=tmp_path / "addons",
        lock_path=tmp_path / "gdpm.lock",
        lock_map={},
        all_deps={},
    )


def _patch_services(
    monkeypatch,
    ctx: SimpleNamespace,
    store: FakeStore,
    manager: FakeManager,
    *,
    resolved: ResolvedPlugin | None = None,
    template: bool = False,
) -> None:
    """替换项目上下文、Store/Manager 与发布者解析."""
    if resolved is None:
        resolved = ResolvedPlugin(publisher="pub", slug="myplug", found=True)

    async def _resolve(_store, _name):
        return resolved

    monkeypatch.setattr("gdpm.cli.commands.add.get_project_context", lambda: ctx)
    monkeypatch.setattr(
        "gdpm.cli.commands.add.get_services",
        lambda _ctx: SimpleNamespace(store=store, manager=manager),
    )
    monkeypatch.setattr("gdpm.cli.commands.add.resolve_publisher", _resolve)
    monkeypatch.setattr("gdpm.cli.commands.add.is_template", lambda _tags: template)


def test_parse_spec_plain_name() -> None:
    """无 @ 时整串为插件名, 约束为空."""
    assert _parse_spec("limbo-ai") == ("limbo-ai", "")


def test_parse_spec_with_version() -> None:
    """name@version 拆分为名称与约束."""
    assert _parse_spec("limbo-ai@1.5.0") == ("limbo-ai", "1.5.0")


def test_parse_spec_with_empty_constraint() -> None:
    """name@ 视为空约束."""
    assert _parse_spec("limbo-ai@") == ("limbo-ai", "")


def test_add_requires_plugin_argument() -> None:
    """未提供插件时直接报错退出."""
    result = CliRunner().invoke(add, [])
    assert result.exit_code == 1
    assert "No plugins specified" in result.output


def test_add_installs_plugin_and_updates_files(tmp_path, monkeypatch) -> None:
    """在线安装成功: 写配置与锁文件并提示 Added."""
    ctx = _ctx(tmp_path)
    store = FakeStore()
    manager = FakeManager()
    _patch_services(monkeypatch, ctx, store, manager)

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 0, result.output
    assert "Added" in result.output
    assert "myplug" in ctx.config.dependencies
    assert (ctx.config_path).read_text().count("myplug") == 1
    assert "myplug" in (ctx.lock_path).read_text()
    assert manager.downloads == [("pub", "myplug", "1.0.0")]
    assert manager.installs == [(Path("pkg.zip"), "myplug", "pub")]
    assert store.closed is True


def test_add_skips_existing_dependency(tmp_path, monkeypatch) -> None:
    """已在依赖中时跳过安装."""
    ctx = _ctx(tmp_path)
    ctx.config.dependencies["myplug"] = Dependency.from_spec("myplug", "*")
    store = FakeStore()
    manager = FakeManager()
    _patch_services(monkeypatch, ctx, store, manager)

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 0
    assert "already" in result.output
    assert manager.downloads == []


def test_add_rejects_project_template(tmp_path, monkeypatch) -> None:
    """模板类插件不可作为依赖安装."""
    ctx = _ctx(tmp_path)
    store = FakeStore()
    manager = FakeManager()
    _patch_services(monkeypatch, ctx, store, manager, template=True)

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 1
    assert "project template" in result.output
    assert manager.downloads == []


def test_add_reports_resolve_failure(tmp_path, monkeypatch) -> None:
    """发布者解析失败时累积错误并退出."""
    ctx = _ctx(tmp_path)
    unresolved = ResolvedPlugin(
        publisher="", slug="myplug", found=False, error="Plugin not found"
    )
    _patch_services(monkeypatch, ctx, FakeStore(), FakeManager(), resolved=unresolved)

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 1
    assert "Plugin not found" in result.output


def test_add_uses_constraint_selected_version(tmp_path, monkeypatch) -> None:
    """版本约束命中后下载选中的具体版本, 而非约束串."""
    ctx = _ctx(tmp_path)
    store = FakeStore(versions=[{"version": "v2.0.0"}, {"version": "v1.5.0"}])
    manager = FakeManager()
    _patch_services(monkeypatch, ctx, store, manager)

    result = CliRunner().invoke(add, ["myplug@^1.0.0"])

    assert result.exit_code == 0, result.output
    assert manager.downloads == [("pub", "myplug", "1.5.0")]
    assert ctx.config.dependencies["myplug"].constraint.constraint == (">=1.0.0,<2.0.0")


def test_add_dev_dependency(tmp_path, monkeypatch) -> None:
    """--dev 写入开发依赖小节."""
    ctx = _ctx(tmp_path)
    _patch_services(monkeypatch, ctx, FakeStore(), FakeManager())

    result = CliRunner().invoke(add, ["myplug", "--dev"])

    assert result.exit_code == 0
    assert "myplug" in ctx.config.dev_dependencies
    assert "myplug" not in ctx.config.dependencies


def test_add_suggests_publisher_on_404(tmp_path, monkeypatch) -> None:
    """404 时搜索同名插件并给出发布者提示."""
    ctx = _ctx(tmp_path)
    store = FakeStore(
        search_results=[SimpleNamespace(slug="myplug", publisher_slug="pub")]
    )
    manager = FakeManager(error=RuntimeError("404 Not Found"))
    _patch_services(monkeypatch, ctx, store, manager)

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 1
    assert "Did you mean" in result.output
    assert "pub/myplug" in result.output


def test_add_reports_generic_download_error(tmp_path, monkeypatch) -> None:
    """非 404 下载错误直接输出失败原因."""
    ctx = _ctx(tmp_path)
    _patch_services(
        monkeypatch, ctx, FakeStore(), FakeManager(error=RuntimeError("boom"))
    )

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 1
    assert "Failed to install" in result.output
    assert "boom" in result.output


def test_add_continues_when_detail_lookup_fails(tmp_path, monkeypatch) -> None:
    """详情接口异常时继续安装."""
    ctx = _ctx(tmp_path)
    store = FakeStore(plugin_error=RuntimeError("api down"))
    manager = FakeManager()
    _patch_services(monkeypatch, ctx, store, manager)

    result = CliRunner().invoke(add, ["myplug"])

    assert result.exit_code == 0
    assert "myplug" in ctx.config.dependencies


def test_add_local_installs_zip(tmp_path, monkeypatch) -> None:
    """--local 从 zip 安装到 addons 并写入本地依赖与锁."""
    ctx = _ctx(tmp_path)
    zip_path = tmp_path / "myplug.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("myplug/plugin.cfg", "")
        zf.writestr("myplug/main.gd", "gd")
    monkeypatch.setattr("gdpm.cli.commands.add.get_project_context", lambda: ctx)

    result = CliRunner().invoke(add, ["--local", str(zip_path)])

    assert result.exit_code == 0, result.output
    assert (ctx.addons_dir / "myplug" / "myplug" / "plugin.cfg").exists()
    assert (ctx.addons_dir / "myplug" / "tag.gdpm").exists()
    assert ctx.config.dependencies["myplug"].is_local is True
    assert (ctx.root / "gdpm-local" / "myplug.zip").exists()
    assert "myplug" in (ctx.root / "gdpm.lock").read_text()


def test_add_local_without_plugins(tmp_path, monkeypatch) -> None:
    """--local 且 addons 为空时提示无本地插件."""
    ctx = _ctx(tmp_path)
    monkeypatch.setattr("gdpm.cli.commands.add.get_project_context", lambda: ctx)

    result = CliRunner().invoke(add, ["--local"])

    assert result.exit_code == 0
    assert "No local plugins" in result.output
