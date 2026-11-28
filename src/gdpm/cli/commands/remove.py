"""
gdpm remove 命令

- 从项目移除插件: 删除依赖条目与插件目录, 同步锁文件.

----

Notes
----
- 删除依赖条目: 从 gdproject.toml 中移除.
- 删除插件目录: 移除 addons/ 下的插件目录.
- 删除本地 zip: 可选删除 gdpm-local/ 中的 zip.
- 更新锁文件: 同步 gdpm.lock.
- remove: 命令入口.
- _find_addon_dir: 按 slug 查找插件目录.
"""

from __future__ import annotations

import configparser
from typing import TYPE_CHECKING

import click

from gdpm.cli.base import GdpmCommand
from gdpm.cli.common import console, require_project
from gdpm.cli.options import yes_option
from gdpm.config.project import read_project_config, write_project_config
from gdpm.constants import TAG_FILENAME
from gdpm.lockfile.lock import find_lockfile, read_lockfile, write_lockfile

if TYPE_CHECKING:
    from pathlib import Path


@click.command(
    cls=GdpmCommand,
    category="dependencies",
    examples=[
        ("gdpm remove limbo-ai", "Remove a plugin"),
        ("gdpm remove -y limbo-ai", "Remove without confirmation"),
        ("gdpm remove -r limbo-ai", "Remove with sub-dependencies"),
    ],
)
@click.argument("plugins", nargs=-1, required=True)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Also remove unused sub-dependencies",
)
@yes_option
def remove(plugins: tuple[str, ...], recursive: bool, yes: bool) -> None:
    """从项目移除一个或多个插件."""
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    local_dir = root / "gdpm-local"

    removed: list[str] = []
    not_found: list[str] = []
    no_dir: list[str] = []

    for name in plugins:
        slug = name.split("/")[-1]

        if slug not in config.dependencies and slug not in config.dev_dependencies:
            not_found.append(slug)
            continue

        # 检查是否为本地插件
        dep = config.dependencies.get(slug) or config.dev_dependencies.get(slug)
        is_local = dep.is_local if dep else False

        config.dependencies.pop(slug, None)
        config.dev_dependencies.pop(slug, None)

        # 删除 addons/ 下的插件目录 (按 tag.gdpm 身份优先解析)
        actual_dir = _find_addon_dir(addons_dir, slug, name)
        if actual_dir and actual_dir.exists():
            import shutil

            shutil.rmtree(actual_dir)
        else:
            # 目录缺失 (已被手动删除/移出 addons/) 时依赖照常解绑, 但如实说明
            no_dir.append(slug)

        # 若存在则删除本地 zip
        if is_local:
            local_zip = local_dir / f"{slug}.zip"
            if local_zip.exists():
                delete_zip = yes or click.confirm(
                    f"  Delete {local_dir.name}/{slug}.zip?"
                )
                if delete_zip:
                    local_zip.unlink()
                    console.print(f"  [dim]Removed {local_dir.name}/{slug}.zip[/dim]")

        removed.append(slug)

    if removed:
        write_project_config(config, config_path)

        lock_path = find_lockfile(root)
        lock_entries = read_lockfile(lock_path)
        lock_map = {e.name: e for e in lock_entries}

        for name in plugins:
            slug = name.split("/")[-1]
            lock_map.pop(slug, None)

        write_lockfile(list(lock_map.values()), lock_path)

        for name in removed:
            console.print(
                f"[green]✓[/green] Removed [bold]{name}[/bold]\n"
                f"  Updated [cyan]gdproject.toml[/cyan]\n"
                f"  Updated [cyan]gdpm.lock[/cyan]"
            )
            if name in no_dir:
                console.print(
                    "  [yellow]![/yellow] No addons/ directory matched — "
                    "nothing was deleted on disk"
                )

    if not_found:
        for name in not_found:
            console.print(
                f"[yellow]![/yellow] Plugin [bold]{name}[/bold] "
                "not found in dependencies"
            )

    if not removed and not_found:
        raise SystemExit(1)


def _find_addon_dir(addons_dir: Path, slug: str, name: str = "") -> Path | None:
    """
    按身份查找 addons/ 下的插件目录.

    优先解析 tag.gdpm (安装时写入的权威商店身份 —— 目录名可以与 slug 完全
    不同, 例如解压 zip 自带的文件夹名), 与 PluginManager.remove 的匹配方式
    一致; 退路为直接目录名与 plugin.cfg 模糊匹配.

    ----

    Parameters
    ----
    addons_dir : Path
        addons/ 目录路径.
    slug : str
        插件标识 (去除发布者前缀).
    name : str
        用户输入的原始标识 (可能含 publisher/ 前缀, 用于 tag 精确匹配).

    Returns
    ----
    Path | None
        匹配的插件目录; 未找到返回 None.
    """
    if not addons_dir.exists():
        return None

    # 1) tag.gdpm: 权威身份匹配 (目录名常与 slug 不同, 本次故障的根因)
    want_store = f"store+{name}" if "/" in name else None
    store_match: Path | None = None
    local_match: Path | None = None
    for child in addons_dir.iterdir():
        if not child.is_dir():
            continue
        tag_path = child / TAG_FILENAME
        if not tag_path.exists():
            continue
        try:
            tag_content = tag_path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if want_store and tag_content == want_store:
            return child
        if tag_content.startswith("store+") and tag_content.rsplit("/", 1)[-1] == slug:
            store_match = store_match or child
        elif tag_content == f"local+{slug}":
            local_match = local_match or child
    if store_match:
        return store_match
    if local_match:
        return local_match

    # 2) 直接目录名 (目录名 == slug 的常见情形)
    direct = addons_dir / slug
    if direct.exists():
        return direct

    # 3) 模糊匹配: plugin.cfg 名称或下划线目录名

    for child in addons_dir.iterdir():
        if not child.is_dir():
            continue
        cfg = child / "plugin.cfg"
        if cfg.exists():
            try:
                parser = configparser.ConfigParser()
                parser.read(cfg)
                plugin_name = parser.get("plugin", "name", fallback="")
                if slug.replace("-", " ").lower() in plugin_name.lower():
                    return child
                if slug.replace("-", "_") == child.name:
                    return child
            except Exception:
                continue

    return None
