"""
gdpm godot open 命令

- 打开 Godot 编辑器或运行当前项目.

----

Notes
----
- godot_open: 打开 Godot 编辑器或运行当前项目.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import click

from gdpm.cli.base import GdpmCommand
from gdpm.cli.commands.godot.common import resolve_engine_id, resolve_engine_path
from gdpm.cli.common import console, find_project_root


@click.command(
    name="open",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot open", "Open Godot editor"),
        ("gdpm godot open --run", "Run the project"),
        ("gdpm godot open gdpm-godot@4.7-stable", "Open a specific engine by ID"),
    ],
)
@click.option(
    "--run", "-r", is_flag=True, help="Run the project instead of opening editor"
)
@click.argument("engine_id", metavar="ID", required=False)
def godot_open(engine_id: str | None, run: bool) -> None:
    """为当前项目打开 Godot 编辑器 (可按 ID 一次性指定引擎)."""
    from gdpm.config.global_config import get_default_engine

    root = find_project_root()
    conf_path = root / ".engines-conf.json"
    binary = ""

    engine_name = "?"
    engine_ver = "?"

    if engine_id:
        # 显式 ID: 一次性指定引擎, 不读也不改项目/全局配置
        resolved = resolve_engine_id(
            engine_id, example="gdpm godot open gdpm-godot@4.7-stable"
        )
        if not resolved:
            return
        name, version, binary = resolved
        engine_name = name
        engine_ver = version
    else:
        if conf_path.exists():
            try:
                conf = json.loads(conf_path.read_text(encoding="utf-8"))
                godot = conf.get("godot", {})
                binary = godot.get("path", "")
                engine_name = godot.get("name", "?")
                engine_ver = godot.get("version", "?")
            except json.JSONDecodeError, TypeError:
                pass

        if not binary:
            default_id = get_default_engine()
            if default_id:
                name, version = default_id.split("@", 1)
                binary = resolve_engine_path(name, version)
                engine_name = name
                engine_ver = version

        if not binary:
            console.print(
                "[red]Error:[/red] No Godot engine configured.\n"
                "  Use [bold]gdpm godot use <id>[/bold] for this project,\n"
                "  or [bold]gdpm godot default <id>[/bold] to set a default engine.\n"
                "\n"
                "  Available engines:\n"
                "    [bold]gdpm godot list -id[/bold]"
            )
            return

    binary_path = Path(binary)
    # .app 包时深入 Contents/MacOS 取真实二进制 (兼容 mono 变体 Godot_mono)
    if binary_path.suffix == ".app":
        for stem in ("Godot", binary_path.stem):
            macos_binary = binary_path / "Contents" / "MacOS" / stem
            if macos_binary.exists():
                binary = str(macos_binary)
                break

    args = [binary]
    # --run 仅指定项目目录, 编辑器模式追加 -e
    if run:
        args.extend(["--path", str(root)])
    else:
        args.extend(["-e", "--path", str(root)])

    console.print(f"Opening [cyan]{engine_name}@{engine_ver}[/cyan]...")

    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            # 短暂等待以捕获启动失败
            ret: int | None = proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            ret = None
        if ret is not None and ret != 0:
            console.print(f"[red]Error:[/red] Godot exited with code {ret}")
            return
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to open Godot: {e}")
        return

    console.print(f"[green]✓[/green] Opened [cyan]{engine_name}@{engine_ver}[/cyan]")
