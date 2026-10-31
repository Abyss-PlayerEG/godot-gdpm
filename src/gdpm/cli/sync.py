"""
gdpm sync 命令: 将 addons/ 同步到锁文件状态.

Sync addons/ to the lock file state.

----

Note:
    - 同步本地插件: 从 gdpm-local/ 释放 zip 到 addons/ /
        Sync local plugins from gdpm-local/ into addons/.
    - 并行下载: 补齐缺失的 Store 插件 /
        Download missing Store plugins in parallel.
    - 移除多余插件: 删除锁文件之外的插件 /
        Remove plugins not listed in the lock file.
    - 更新锁文件: 记录本次变更 /
        Update the lock file with the changes.
    - MAX_PARALLEL: 最大并发下载数, 默认 5 /
        Max parallel downloads, 5 by default.
    - sync(): 命令入口, 内部定义异步 _sync() /
        Command entry with the async _sync() worker inside.
    - download_one(): 单个插件的并发下载任务 /
        Concurrent download task for a single plugin.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context, get_services
from gdpm.cli.options import yes_option
from gdpm.lockfile.utils import update_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.utils import resolve_publisher
from gdpm.utils.tag import scan_addons

if TYPE_CHECKING:
    from pathlib import Path

MAX_PARALLEL = 5  # 最大并行下载数 / Max parallel downloads


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm sync", "Sync all plugins"),
        ("gdpm sync --check", "Preview changes without applying"),
        ("gdpm sync --frozen", "Strict mode for CI"),
    ],
)
@click.option("--frozen", is_flag=True, help="Strict mode for CI")
@click.option(
    "-dr",
    "--check",
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying",
)
@click.option("-nc", "--no-cache", is_flag=True, help="Don't use local cache")
@yes_option
def sync(frozen: bool, check: bool, no_cache: bool, yes: bool) -> None:
    """将 addons/ 目录同步到锁文件状态 / Sync addons/ directory to lock file state."""
    ctx = get_project_context()

    if frozen and not ctx.lock_path.exists():
        console.print("[red]Error:[/red] No lock file found. Run 'gdpm lock' first.")
        raise SystemExit(1)

    local_names = {n for n, d in ctx.all_deps.items() if d.is_local}
    online_names = set(ctx.all_deps.keys()) - local_names

    installed_by_dep: set[str] = set()
    if ctx.addons_dir.exists():
        for _, tag in scan_addons(ctx.addons_dir):
            for name in set(ctx.all_deps.keys()):
                if tag.source.endswith(f"/{name}") or tag.slug == name:
                    installed_by_dep.add(name)

    to_install = online_names - installed_by_dep

    to_remove: set[str] = set()
    if ctx.addons_dir.exists():
        for _, tag in scan_addons(ctx.addons_dir):
            if tag.source.endswith(f"/{tag.slug}") and tag.slug not in ctx.all_deps:
                to_remove.add(tag.slug)

    if not to_install and not to_remove:
        console.print("[green]✓[/green] Everything is up to date. Nothing to do.")
        return

    if check:
        lines = []
        for name in sorted(to_install):
            entry = ctx.lock_map.get(name)
            v = entry.version if entry else "?"
            lines.append(f"  [dim]Would install:[/dim] {name} {v}")
        for name in sorted(to_remove):
            lines.append(f"  [dim]Would remove:[/dim]  {name}")
        lines.append(
            f"\n[yellow]Dry run complete.[/yellow] "
            f"{len(to_install)} install, {len(to_remove)} remove."
        )
        console.print("\n".join(lines))
        return

    async def _sync() -> None:
        """执行同步流程 / Run the sync workflow."""
        from gdpm.utils.local import sync_local_plugins

        local_synced = sync_local_plugins(ctx.root, ctx.addons_dir)
        if local_synced:
            console.print(
                f"[green]✓[/green] Synced {len(local_synced)} local plugin(s)"
            )

        svc = get_services(ctx)
        errors: list[str] = []
        lock_updates: dict[str, LockEntry] = {}

        # 准备下载任务 / Prepare download tasks
        download_tasks: list[tuple[str, str, str]] = []

        for name in sorted(to_install):
            entry = ctx.lock_map.get(name)
            deps = ctx.all_deps.get(name)
            dest_path = deps.path if deps else ""

            if entry:
                publisher = entry.source.replace("store+", "").split("/")[0]
                download_tasks.append((name, publisher, entry.version.lstrip("v")))
            elif deps:
                resolved = await resolve_publisher(svc.store, name)
                if resolved.found:
                    download_tasks.append((name, resolved.publisher, ""))
                else:
                    errors.append(f"Plugin '{name}' not found in Store")

        # 并行下载插件 / Download plugins in parallel
        if download_tasks:
            console.print(
                f"Downloading {len(download_tasks)} plugin(s) "
                f"(max {MAX_PARALLEL} parallel)..."
            )

            semaphore = asyncio.Semaphore(MAX_PARALLEL)
            progress = Progress(
                TextColumn("[bold blue]{task.fields[name]}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            )

            async def download_one(
                name: str, publisher: str, version: str
            ) -> tuple[str, str, str, bool, Path | None]:
                """
                下载单个插件, 返回结果元组.

                Download one plugin and return a result tuple.

                ----

                Args:
                    name: 插件名 / Plugin name.
                    publisher: 发布者 / Publisher slug.
                    version: 目标版本, 空串表示最新 /
                        Target version, "" means the latest.

                Returns:
                    (名称, 版本, 发布者, 是否成功, zip 路径) /
                        (name, version, publisher, success, zip path).
                """
                async with semaphore:
                    task_id = progress.add_task("download", name=name, total=None)

                    def on_progress(
                        current: int,
                        total: int,
                        speed: float,
                        _task: TaskID = task_id,
                    ) -> None:
                        """更新下载进度条 / Update the download progress bar."""
                        if progress.tasks[_task].total is None:
                            progress.update(_task, total=total)
                        progress.update(_task, completed=current)

                    try:
                        zip_path, ver = await svc.manager.download(
                            publisher,
                            name,
                            version,
                            on_progress=on_progress,
                            use_cache=not no_cache,
                        )
                        return name, ver, publisher, True, zip_path
                    except Exception:
                        return name, "", publisher, False, None

            with progress:
                results = await asyncio.gather(
                    *[download_one(n, p, v) for n, p, v in download_tasks]
                )

            # 安装已下载的插件 / Install downloaded plugins
            installed_lines = []
            console.print()
            for name, ver, publisher, success, zip_path in results:
                if not success or not zip_path:
                    errors.append(f"Failed to download {name}")
                    continue

                try:
                    deps = ctx.all_deps.get(name)
                    dest_path = deps.path if deps else ""
                    svc.manager.install_from_zip(zip_path, name, publisher, dest_path)
                    lock_updates[name] = LockEntry(
                        name=name,
                        version=ver,
                        source=f"store+{publisher}/{name}",
                    )
                    installed_lines.append(
                        f"  [green]✓[/green] Installed [bold]{name}[/bold] {ver}"
                    )
                except Exception as e:
                    errors.append(f"Failed to install {name}: {e}")

        # 移除多余插件 / Remove extra plugins
        removed_lines = []
        for name in sorted(to_remove):
            svc.manager.remove(name)
            removed_lines.append(f"  [green]✓[/green] Removed [bold]{name}[/bold]")

        # 更新锁文件 (frozen 模式下跳过) /
        # Update the lock file (skipped in frozen mode)
        if local_synced:
            for name in local_synced:
                lock_updates[name] = LockEntry(
                    name=name, version="local", source="local"
                )

        if not frozen and (lock_updates or to_remove):
            update_lockfile(ctx.lock_path, lock_updates, list(to_remove))

        await svc.store.close()

        if installed_lines:
            console.print("\n".join(installed_lines))
        if removed_lines:
            console.print("\n".join(removed_lines))

        summary = []
        installed_count = len(lock_updates)
        removed_count = len(to_remove)
        if installed_count:
            summary.append(f"{installed_count} installed")
        if removed_count:
            summary.append(f"{removed_count} removed")
        if errors:
            summary.append(f"{len(errors)} errors")

        console.print(f"[green]✓[/green] Sync complete: {', '.join(summary)}")

        for err in errors:
            console.print(f"  [red]✗[/red] {err}")

    asyncio.run(_sync())
