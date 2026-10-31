"""
gdpm import 命令: 从 zip 归档或目录导入插件.

Import plugins from a zip archive or directory.

----

Note:
    - 读取清单: 解析 manifest.json / Parse manifest.json.
    - 安装 Store 插件: 下载并安装在线插件 /
        Download and install Store plugins.
    - 解压本地插件: 释放到 addons/ 并复制 zip 到 gdpm-local/ /
        Extract local plugins into addons/ and copy zips into gdpm-local/.
    - 更新配置: 写入 gdproject.toml 与 gdpm.lock /
        Write gdproject.toml and gdpm.lock.
    - manifest.json 结构 / manifest.json structure:
        - version: 清单格式版本 / Manifest format version.
        - exported_at: 导出时间 (ISO 8601) / Export timestamp (ISO 8601).
        - project: 项目名与 Godot 约束 / Project name and Godot constraint.
        - plugins: 插件列表, 每项含 name, version, source, type, file
            (仅 local) 与 publisher (仅 store) / Plugin list, each entry
            holds name, version, source, type, file (local only) and
            publisher (store only).
    - import_cmd(): 命令入口 / Command entry.
    - _import_store(): 异步安装 Store 插件 / Async Store plugin installer.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import zipfile
from pathlib import Path

import click

from gdpm.cache.file_cache import FileCache
from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, require_project
from gdpm.cli.options import yes_option
from gdpm.config.project import read_project_config, write_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.dependency import Dependency
from gdpm.models.lock import LockEntry
from gdpm.store.client import StoreClient
from gdpm.utils.local import LOCAL_DIR_NAME, tag_plugin


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm import plugins.zip", "Import from zip archive"),
        ("gdpm import ./backup/", "Import from directory"),
        ("gdpm import -y plugins.zip", "Import without confirmation"),
    ],
)
@click.argument("source", type=click.Path(exists=True))
@yes_option
def import_cmd(source: str, yes: bool) -> None:
    """从 zip 归档或目录导入插件 / Import plugins from a zip archive or directory."""
    root = require_project()
    source_path = Path(source)

    # 判定来源类型并读取 manifest / Determine source type and read manifest
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

    # 按 type 字段区分 Store 插件与本地插件 /
    # Split Store plugins and local plugins by the type field
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

    # 导入 Store 插件 / Import Store plugins
    if store_plugins:

        async def _import_store() -> None:
            """异步下载并安装 Store 插件 / Download and install Store plugins."""
            nonlocal imported
            store = StoreClient()
            cache = FileCache(root / ".gdpm" / "cache")
            manager = PluginManager(addons_dir, cache, store)

            try:
                for p in store_plugins:
                    name = p["name"]
                    publisher = p.get("publisher", "")
                    version = p.get("version", "")

                    # 检查是否已安装 / Check if already installed
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

    # 导入本地插件 / Import local plugins
    for p in local_plugins:
        name = p["name"]
        zip_file = p.get("file", "")

        # 检查是否已安装 / Check if already installed
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

        # 定位 zip 来源路径 / Locate the zip source path
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

        # 复制 zip 到 gdpm-local/ / Copy the zip into gdpm-local/
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

        # 解压到 addons/ (先清空旧目录) /
        # Extract into addons/ (clearing any old directory first)
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

    # 更新配置和锁文件 / Update config and lock file
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
