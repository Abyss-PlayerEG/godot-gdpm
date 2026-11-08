"""
gdpm import 命令

- 从 zip 归档或目录导入插件: 读取清单, 安装插件, 更新配置.

----

Notes
----
- 读取清单: 解析 manifest.json.
- 安装 Store 插件: 下载并安装在线插件.
- 解压本地插件: 释放到 addons/ 并复制 zip 到 gdpm-local/.
- 更新配置: 写入 gdproject.toml 与 gdpm.lock.
- manifest.json 结构:
    - version: 清单格式版本.
    - exported_at: 导出时间 (ISO 8601).
    - project: 项目名与 Godot 约束.
    - plugins: 插件列表, 每项含 name, version, source, type, file
      (仅 local) 与 publisher (仅 store).
- import_cmd: 命令入口.
- _import_store: 异步安装 Store 插件.
- _store_import_cache: Store 导入缓存走全局配置 (与 sync/add 同根).
"""

from __future__ import annotations

import asyncio
import json
import shutil
import zipfile
from pathlib import Path

import click

from gdpm.cache.file_cache import FileCache
from gdpm.cli.base import GdpmCommand
from gdpm.cli.common import console, require_project
from gdpm.cli.options import yes_option
from gdpm.config.global_config import read_global_config
from gdpm.config.project import read_project_config, write_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient
from gdpm.utils.local import LOCAL_DIR_NAME, tag_plugin


def _store_import_cache() -> FileCache:
    """
    Store 导入的下载缓存: 走全局 cache_dir 配置 (与 sync/add 同一个缓存).

    ----

    Returns
    ----
    FileCache
        指向全局配置缓存目录的缓存实例.
    """
    return FileCache(Path(read_global_config().cache_dir))


@click.command(
    cls=GdpmCommand,
    category="dependencies",
    examples=[
        ("gdpm import plugins.zip", "Import from zip archive"),
        ("gdpm import ./backup/", "Import from directory"),
        ("gdpm import -y plugins.zip", "Import without confirmation"),
    ],
)
@click.argument("source", type=click.Path(exists=True))
@yes_option
def import_cmd(source: str, yes: bool) -> None:
    """从 zip 归档或目录导入插件."""
    root = require_project()
    source_path = Path(source)

    # 判定来源类型并读取 manifest
    if source_path.is_dir():
        manifest_path = source_path / "manifest.json"
        if not manifest_path.exists():
            console.print("[red]Error:[/red] No manifest.json found in directory")
            raise SystemExit(1)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_type = "dir"
    elif zipfile.is_zipfile(source_path):
        with zipfile.ZipFile(source_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                console.print("[red]Error:[/red] No manifest.json found in zip")
                raise SystemExit(1)
            manifest = json.loads(zf.read("manifest.json"))
        source_type = "zip"
    else:
        console.print(f"[red]Error:[/red] '{source}' is not a valid zip or directory")
        raise SystemExit(1)

    plugins = manifest.get("plugins", [])
    console.print(f"Importing {len(plugins)} plugin(s)...\n")

    config = read_project_config(root / "gdproject.toml")
    addons_dir = root / config.addons_dir
    local_dir = root / LOCAL_DIR_NAME
    lock_entries = {e.name: e for e in read_lockfile(find_lockfile(root))}

    # 按 type 字段区分 Store 插件与本地插件
    store_plugins: list[dict[str, str]] = []
    local_plugins: list[dict[str, str]] = []

    for p in plugins:
        if p.get("type") == "local":
            local_plugins.append(p)
        else:
            store_plugins.append(p)

    imported = 0
    errors: list[str] = []
    lock_updates: dict[str, LockEntry] = {}

    # 导入 Store 插件
    if store_plugins:

        async def _import_store() -> None:
            """异步下载并安装 Store 插件."""
            nonlocal imported
            store = StoreClient()
            cache = _store_import_cache()
            manager = PluginManager(addons_dir, cache, store)

            try:
                for p in store_plugins:
                    name = p["name"]
                    publisher = p.get("publisher", "")
                    version = p.get("version", "")

                    # 检查是否已安装
                    existing = config.dependencies.get(name)
                    if existing:
                        entry = lock_entries.get(name)
                        if entry and entry.version == version:
                            console.print(
                                f"  [dim]○ {name} {version} "
                                "(already installed, skipped)[/dim]"
                            )
                            continue
                        if not yes:
                            old_ver = entry.version if entry else "?"
                            if (
                                not console.input(
                                    f"  [yellow]?[/yellow] {name} "
                                    f"v{old_ver} → v{version}? (y/n): "
                                )
                                .strip()
                                .lower()
                                .startswith("y")
                            ):
                                console.print(f"  [dim]○ {name} (skipped)[/dim]")
                                continue

                    if not publisher:
                        src = p.get("source", "")
                        if "/" in src:
                            publisher = src.split("/")[-2]

                    if not publisher:
                        errors.append(f"Cannot resolve publisher for '{name}'")
                        continue

                    try:
                        ver_to_get = version.lstrip("v") if version else ""
                        zip_dl, ver = await manager.download(
                            publisher, name, ver_to_get
                        )
                        manager.install_from_zip(zip_dl, name, publisher)

                        lock_updates[name] = LockEntry(
                            name=name,
                            version=ver,
                            source=f"store+{publisher}/{name}",
                        )
                        dep = Dependency.from_spec(name, ver, publisher_slug=publisher)
                        config.dependencies[name] = dep
                        imported += 1
                        console.print(
                            f"[green]✓[/green] Installed [bold]{name}[/bold] {ver}"
                        )
                    except Exception as e:
                        errors.append(f"Failed to install {name}: {e}")
            finally:
                await store.close()

        asyncio.run(_import_store())

    # 导入本地插件
    for p in local_plugins:
        name = p["name"]
        zip_file = p.get("file", "")

        # 检查是否已安装
        if name in config.dependencies:
            if not yes:
                if (
                    not console.input(
                        f"  [yellow]?[/yellow] {name} "
                        "already installed. Overwrite? (y/n): "
                    )
                    .strip()
                    .lower()
                    .startswith("y")
                ):
                    console.print(f"  [dim]○ {name} (skipped)[/dim]")
                    continue
            else:
                console.print(
                    f"  [yellow]![/yellow] {name} already installed, overwriting..."
                )

        # 定位 zip 来源路径
        if source_type == "dir":
            zip_source = source_path / zip_file
            if not zip_source.exists():
                errors.append(f"Local plugin zip not found: {zip_file}")
                continue
        else:
            with zipfile.ZipFile(source_path, "r") as zf:
                if zip_file not in zf.namelist():
                    errors.append(f"Local plugin zip not found in archive: {zip_file}")
                    continue

        # 复制 zip 到 gdpm-local/
        local_dir.mkdir(parents=True, exist_ok=True)
        local_zip = local_dir / f"{name}.zip"

        if source_type == "dir":
            shutil.copy2(zip_source, local_zip)
        else:
            with (
                zipfile.ZipFile(source_path, "r") as zf,
                zf.open(zip_file) as src,
            ):
                local_zip.write_bytes(src.read())

        # 解压到 addons/ (先清空旧目录)
        dest = addons_dir / name
        if dest.exists():
            shutil.rmtree(dest)

        with zipfile.ZipFile(local_zip, "r") as local_zf:
            local_zf.extractall(dest)

        tag_plugin(addons_dir, name)

        lock_updates[name] = LockEntry(name=name, version="local", source="local")
        dep = Dependency.from_spec(name, "*", is_local=True)
        config.dependencies[name] = dep
        imported += 1
        console.print(f"[green]✓[/green] Installed [bold]{name}[/bold] (local)")

    # 更新配置和锁文件
    if imported:
        write_project_config(config, root / "gdproject.toml")
        update_lockfile(find_lockfile(root), lock_updates)

        console.print(
            f"[green]✓[/green] Imported {imported} plugin(s)\n"
            f"  Updated [cyan]gdproject.toml[/cyan]\n"
            f"  Updated [cyan]gdpm.lock[/cyan]"
        )

    if errors:
        for err in errors:
            console.print(f"[red]✗[/red] {err}")
