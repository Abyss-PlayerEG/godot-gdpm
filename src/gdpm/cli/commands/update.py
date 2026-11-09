"""
gdpm update 命令

- 将插件更新到较新版本: 查询版本, 挑选兼容版本, 下载安装.

----

Notes
----
- 查询版本列表: 从 Store 获取全部版本.
- 挑选版本: 按版本约束选择最新兼容版本.
- 下载安装: 下载并安装选定版本.
- 更新锁文件: 记录新版本.
- update: 命令入口, 内部定义异步 _update.
"""

from __future__ import annotations

import asyncio

import click

from gdpm.cli.base import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context, get_services
from gdpm.cli.options import yes_option
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.lock import LockEntry
from gdpm.utils.version import normalize_version


@click.command(
    cls=GdpmCommand,
    category="dependencies",
    examples=[
        ("gdpm update", "Update all plugins"),
        ("gdpm update limbo-ai", "Update specific plugin"),
        ("gdpm update --check", "Preview updates"),
        ("gdpm update --latest", "Ignore version constraints"),
    ],
)
@click.argument("plugins", nargs=-1)
@click.option("--latest", is_flag=True, help="Ignore version constraints")
@click.option(
    "-dr",
    "--check",
    "--dry-run",
    is_flag=True,
    help="Check for updates without applying",
)
@yes_option
def update(plugins: tuple[str, ...], latest: bool, check: bool, yes: bool) -> None:
    """将插件更新到较新版本."""

    async def _update() -> None:
        """检查并应用插件更新."""
        ctx = get_project_context()

        if plugins:
            targets = {p.split("/")[-1] for p in plugins}
        else:
            targets = set(ctx.all_deps.keys())

        svc = get_services(ctx)
        updates: list[dict[str, str]] = []
        errors: list[str] = []

        try:
            console.print("Checking for updates...")

            for name in targets:
                dep = ctx.all_deps.get(name)
                if not dep:
                    errors.append(f"Plugin '{name}' not in dependencies")
                    continue

                # 跳过本地插件
                if dep.is_local:
                    console.print(f"  [dim]Skipping {name} (local plugin)[/dim]")
                    continue

                # 解析发布者
                if dep.publisher_slug:
                    publisher = dep.publisher_slug
                else:
                    from gdpm.store.utils import resolve_publisher

                    resolved = await resolve_publisher(svc.store, name)
                    if not resolved.found:
                        errors.append(resolved.error)
                        continue
                    publisher = resolved.publisher

                # 获取版本列表
                try:
                    versions = await svc.store.get_versions(publisher, name)
                except Exception as e:
                    errors.append(f"Failed to fetch versions for '{name}': {e}")
                    continue

                if not versions:
                    errors.append(f"No versions found for '{name}'")
                    continue

                # 查找当前安装的版本
                current = ctx.lock_map.get(name)
                current_ver = current.version.lstrip("v") if current else ""

                # 查找最新兼容版本
                latest_ver = None
                for v in versions:
                    api_ver = v["version"].lstrip("v")
                    # 延迟导入 Version 类
                    if latest or dep.constraint.matches(
                        __import__("gdpm.models.version", fromlist=["Version"]).Version(
                            api_ver
                        )
                    ):
                        latest_ver = v
                        break

                if not latest_ver:
                    errors.append(f"No compatible version for '{name}'")
                    continue

                new_ver = latest_ver["version"]
                if current_ver and normalize_version(new_ver) == normalize_version(
                    current_ver
                ):
                    continue

                updates.append(
                    {
                        "name": name,
                        "publisher": publisher,
                        "old_version": current_ver or "none",
                        "new_version": new_ver,
                    }
                )

        finally:
            await svc.store.close()

        if not updates:
            console.print("[green]✓[/green] All plugins are up to date.")
            return

        lines = [f"{len(updates)} update(s) available:"]
        for u in updates:
            lines.append(
                f"  [cyan]{u['name']}[/cyan]  "
                f"{u['old_version']} → [green]{u['new_version']}[/green]"
            )
        console.print("\n".join(lines))

        if check:
            console.print("[yellow]Dry run complete.[/yellow]")
            return

        # 应用更新
        svc2 = get_services(ctx)
        applied = 0
        lock_updates: dict[str, LockEntry] = {}

        try:
            for u in updates:
                try:
                    zip_path, _ver = await svc2.manager.download(
                        u["publisher"],
                        u["name"],
                        u["new_version"].lstrip("v"),
                    )
                    svc2.manager.install_from_zip(zip_path, u["name"], u["publisher"])
                    lock_updates[u["name"]] = LockEntry(
                        name=u["name"],
                        version=u["new_version"],
                        source=f"store+{u['publisher']}/{u['name']}",
                    )
                    applied += 1
                    console.print(
                        f"[green]✓[/green] Updated [bold]{u['name']}[/bold] "
                        f"{u['new_version']}"
                    )
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to update {u['name']}: {e}")
        finally:
            await svc2.store.close()

        if applied:
            update_lockfile(ctx.lock_path, lock_updates)
            console.print(f"\n[green]✓[/green] Updated {applied} plugin(s)")

    asyncio.run(_update())
