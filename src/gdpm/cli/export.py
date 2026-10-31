"""
gdpm export 命令: 将项目插件导出为 zip 归档.

Export project plugins to a zip archive.

----

Note:
    - 收集插件: 汇总依赖与 addons/ 中的插件 /
        Collect plugins from dependencies and addons/.
    - 生成清单: 写入 manifest.json / Write manifest.json.
    - 打包本地插件: 放入归档的 local-plugins/ 目录 /
        Pack local plugins under local-plugins/ in the archive.
    - manifest.json 结构 / manifest.json structure:
        - version: 清单格式版本 / Manifest format version.
        - exported_at: 导出时间 (ISO 8601) / Export timestamp (ISO 8601).
        - project: 项目名与 Godot 约束 / Project name and Godot constraint.
        - plugins: 插件列表, 每项含 name, version, source, type ("store"
            或 "local"), file (本地 zip 路径) 与 publisher (仅 store) /
            Plugin list, each entry holds name, version, source, type
            ("store" or "local"), file (local zip path) and publisher
            (store only).
    - export(): 命令入口 / Command entry.
"""

from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console, require_project
from gdpm.config.project import read_project_config
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.utils.local import LOCAL_DIR_NAME
from gdpm.utils.tag import scan_addons


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm export", "Export to default location"),
        ("gdpm export -o backup.zip", "Export to custom file"),
        ("gdpm export -o ~/backup/plugins.zip", "Export to specific path"),
    ],
)
@click.option("-o", "--output", default="", help="Output file path")
def export(output: str) -> None:
    """导出插件到 zip 归档 / Export plugins to a zip archive."""
    root = require_project()
    config = read_project_config(root / "gdproject.toml")
    lock_entries = {e.name: e for e in read_lockfile(find_lockfile(root))}
    local_dir = root / LOCAL_DIR_NAME

    all_deps = {**config.dependencies, **config.dev_dependencies}

    # 构建 manifest, 先收集声明的依赖 / Build manifest from declared deps first
    plugins: list[dict[str, str]] = []
    local_files: list[str] = []
    seen: set[str] = set()

    for name, dep in all_deps.items():
        entry = lock_entries.get(name)
        seen.add(name)

        if dep.is_local:
            # 本地插件: 记录 zip 在归档中的路径 /
            # Local plugin: record the zip path inside the archive
            local_zip = local_dir / f"{name}.zip"
            if local_zip.exists():
                local_files.append(name)
                plugins.append(
                    {
                        "name": name,
                        "version": "local",
                        "source": "local",
                        "type": "local",
                        "file": f"local-plugins/{name}.zip",
                    }
                )
        else:
            # Store 插件: 版本与来源优先取自锁文件 /
            # Store plugin: version and source come from the lock file
            plugins.append(
                {
                    "name": name,
                    "version": entry.version if entry else str(dep.constraint),
                    "source": entry.source if entry else "",
                    "publisher": dep.publisher_slug,
                    "type": "store",
                }
            )

    # 同时扫描 addons/ 中未在配置里的插件 /
    # Also scan addons/ for installed plugins not in config
    for _, tag in scan_addons(root / config.addons_dir):
        if tag.slug in seen:
            continue
        seen.add(tag.slug)

        if tag.is_local:
            local_zip = local_dir / f"{tag.slug}.zip"
            if local_zip.exists():
                local_files.append(tag.slug)
                plugins.append(
                    {
                        "name": tag.slug,
                        "version": "local",
                        "source": "local",
                        "type": "local",
                        "file": f"local-plugins/{tag.slug}.zip",
                    }
                )
        else:
            entry = lock_entries.get(tag.slug)
            plugins.append(
                {
                    "name": tag.slug,
                    "version": entry.version if entry else "?",
                    "source": tag.source,
                    "type": "store",
                }
            )

    manifest = {
        "version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "project": {
            "name": config.name,
            "godot": config.godot,
        },
        "plugins": plugins,
    }

    # 创建 zip 归档 / Create the zip archive
    if not output:
        output_dir = root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        output = str(output_dir / f"{config.name}-{date_str}.zip")

    output_path = Path(output)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 写入 manifest.json / Write manifest.json
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

        # 添加本地插件 zip / Add local plugin zips
        for name in local_files:
            local_zip = local_dir / f"{name}.zip"
            zf.write(local_zip, f"local-plugins/{name}.zip")

    local_msg = f"\n  {len(local_files)} local plugin(s)" if local_files else ""
    console.print(
        f"[green]✓[/green] Exported to [cyan]{output_path}[/cyan]\n"
        f"  {len(plugins)} plugin(s){local_msg}"
    )
