"""
gdpm lock 命令. 解析项目依赖并生成或更新 gdpm.lock 锁文件, 支持 --check
检查模式.

----

Note:
    - lock: 命令入口, 内部通过 asyncio 运行解析与写入流程.
"""

from __future__ import annotations

import asyncio

import click

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.context import get_project_context
from gdpm.lockfile.lock import write_lockfile
from gdpm.models.lock import LockEntry
from gdpm.store.utils import resolve_publisher


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm lock", "Generate lock file"),
        ("gdpm lock --check", "Check if lock file is up to date"),
    ],
)
@click.option("--check", is_flag=True, help="Check if lock file is up to date")
def lock(check: bool) -> None:
    """生成或更新锁文件."""

    # 解析流程为异步逻辑, 在独立协程中执行
    async def _lock() -> None:
        ctx = get_project_context()
        store = ctx.store if hasattr(ctx, "store") else None

        from gdpm.store.client import StoreClient

        store = StoreClient()
        entries: list[LockEntry] = []
        errors: list[str] = []

        try:
            console.print("Resolving dependencies...")

            # 逐个解析依赖: 本地插件直接写入, 在线插件解析发布者与版本
            for name, dep in ctx.all_deps.items():
                # 本地插件
                if dep.is_local:
                    console.print(f"  {name} (local)")
                    entries.append(
                        LockEntry(name=name, version="local", source="local")
                    )
                    continue

                # 解析发布者, 未指定时经商店 API 查询
                if dep.publisher_slug:
                    publisher = dep.publisher_slug
                else:
                    resolved = await resolve_publisher(store, name)
                    if not resolved.found:
                        errors.append(resolved.error)
                        continue
                    publisher = resolved.publisher

                # 获取该插件的全部版本
                versions = await store.get_versions(publisher, name)
                if not versions:
                    errors.append(f"No versions found for '{name}'")
                    continue

                # 在版本列表中找到第一个满足约束的版本
                # 逐个版本去掉 v 前缀后匹配约束; 惰性构造 Version 对象
                matched = None
                for v in versions:
                    api_ver = v["version"].lstrip("v")
                    if dep.constraint.matches(
                        __import__("gdpm.models.version", fromlist=["Version"]).Version(
                            api_ver
                        )
                    ):
                        matched = v
                        break

                if not matched:
                    errors.append(f"No version of '{name}' satisfies {dep.constraint}")
                    continue

                ver = matched["version"]
                source = f"store+{publisher}/{name}"
                console.print(f"  {name} {ver}")

                entries.append(LockEntry(name=name, version=ver, source=source))

        finally:
            await store.close()

        # 输出解析错误; 只要有解析成功的条目就写入锁文件
        if errors:
            for err in errors:
                console.print(f"[red]✗[/red] {err}")

        if entries:
            write_lockfile(entries, ctx.lock_path)
            console.print(
                f"[green]✓[/green] Lock file updated: {len(entries)} packages"
            )
        elif not errors:
            console.print("[yellow]![/yellow] No dependencies to lock")

    asyncio.run(_lock())
