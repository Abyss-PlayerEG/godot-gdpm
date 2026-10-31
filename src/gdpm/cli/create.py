"""
gdpm create 命令: 创建新的 Godot 项目.

Create a new Godot project.

----

Note:
    - 询问信息: 项目名与 Godot 版本 /
        Prompt for the project name and the Godot version.
    - 生成文件: project.godot, gdproject.toml 与 addons/ 目录 /
        Generate project.godot, gdproject.toml and the addons/ directory.
    - 后续操作: 可选设置项目引擎并打开 Godot 编辑器 /
        Optionally set the project engine and open the Godot editor.
    - create(): 命令入口 / Command entry.
    - _get_installed_engines(): 收集已安装引擎 ID / Collect installed engine IDs.
    - _get_installed_versions(): 提取去重版本并过滤 csharp/mono /
        Extract unique versions, filtering out csharp/mono.
    - _get_godot_version_tag(): 版本转特性标签 / Convert a version to a features tag.
    - _set_project_engine(): 写入 .engines-conf.json / Write .engines-conf.json.
    - _open_godot(): 启动 Godot 编辑器 / Launch the Godot editor.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click
import questionary

from gdpm.cli.app import GdpmCommand
from gdpm.cli.common import console
from gdpm.cli.godot.common import get_engines_dir, normalize_version
from gdpm.config.local_engines import get_default_engine, get_local_engine
from gdpm.config.project import ProjectConfig, write_project_config


def _get_installed_engines() -> list[str]:
    """
    获取所有已安装引擎 ID.

    Get all installed engine IDs.

    Returns:
        ID 列表, 如 ['gdpm-godot@4.7-stable', 'steam@4.7-stable'] /
            List of IDs like ['gdpm-godot@4.7-stable', 'steam@4.7-stable'].
    """
    engines: list[str] = []

    # 已下载的引擎 (含 csharp) / Downloaded engines (including csharp)
    engines_dir = get_engines_dir()
    if engines_dir.exists():
        for d in engines_dir.iterdir():
            if d.is_dir() and d.name[0].isdigit():
                engines.append(f"gdpm-godot@{d.name}")

    # 本地注册的引擎 / Locally registered engines
    from gdpm.config.local_engines import load_local_engines

    for name, engine in load_local_engines().items():
        if engine.version:
            engines.append(f"{name}@{engine.version}")

    # 排序: stable 优先, 再按版本降序 / Sort: stable first, then version desc
    def sort_key(item: str) -> tuple[int, str]:
        ver = item.split("@", 1)[1]
        is_stable = 0 if "stable" in ver else 1
        return (is_stable, ver)

    engines.sort(key=sort_key, reverse=True)
    return engines


def _get_installed_versions(engines: list[str]) -> list[str]:
    """
    从引擎 ID 提取去重版本并过滤 csharp/mono.

    Get unique versions from engine IDs, filtering out csharp/mono.

    ----

    Args:
        engines: 引擎 ID 列表 / List of engine IDs.

    Returns:
        去重且不含 csharp/mono 的版本列表 /
            Unique versions without csharp/mono builds.
    """
    versions: list[str] = []
    seen: set[str] = set()

    for engine_id in engines:
        ver = engine_id.split("@", 1)[1]
        if "-csharp" in ver or "-mono" in ver:
            continue
        if ver not in seen:
            seen.add(ver)
            versions.append(ver)

    return versions


def _get_godot_version_tag(version: str) -> str:
    """
    将版本转换为 Godot 特性标签.

    Convert a version to a Godot features tag.

    ----

    example:
        >>> _get_godot_version_tag("4.7-stable")
        '4.7'
        >>> _get_godot_version_tag("3.6.2-stable")
        '3.6'

    ----

    Args:
        version: Godot 版本字符串 / A Godot version string.

    Returns:
        主次版本号标签, 如 '4.7' / Major.minor tag such as '4.7'.
    """
    ver = version.replace("-stable", "").replace("-rc", "").replace("-beta", "")
    parts = ver.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return ver


@click.command(
    cls=GdpmCommand,
    examples=[
        ("gdpm create", "Interactive create"),
        ("gdpm create my-game", "Create with name"),
        ("gdpm create my-game --open", "Create and open Godot"),
    ],
)
@click.argument("name", required=False)
@click.option(
    "--open",
    "-o",
    "open_editor",
    is_flag=True,
    help="Open Godot after create",
)
@click.option("--yes", "-y", is_flag=True, help="Use defaults, skip prompts")
def create(name: str | None, open_editor: bool, yes: bool) -> None:
    """创建新的 Godot 项目 / Create a new Godot project."""
    project_dir = Path.cwd()

    console.print("[bold cyan]✦ Create a new Godot project[/bold cyan]")

    # 获取项目名称 / Get the project name
    if not name:
        if yes:
            name = "gdpm-project"
        else:
            name = questionary.text(
                "Project name:",
                default="gdpm-project",
            ).ask()
            if not name:
                return

    # 检查目录是否已存在 / Check if the directory already exists
    target_dir = project_dir / name if name != project_dir.name else project_dir
    config_path = target_dir / "gdproject.toml"

    if config_path.exists():
        console.print(
            f"  [red]✖[/red] Project already exists ([cyan]{config_path}[/cyan])"
        )
        return

    # 获取 Godot 版本 / Get the Godot version
    engines = _get_installed_engines()
    versions = _get_installed_versions(engines)
    default_ver = versions[0] if versions else "4.7-stable"

    if yes:
        godot_ver = default_ver
    elif versions:
        godot_ver = questionary.select(
            "Godot version:",
            choices=versions,
            default=default_ver,
        ).ask()
        if not godot_ver:
            return
    else:
        godot_ver = questionary.text(
            "Godot version:",
            default="4.7-stable",
        ).ask()
        if not godot_ver:
            return

    # 规范化版本号 / Normalize the version
    for suffix in ("-stable", "-csharp", "-mono"):
        godot_ver = godot_ver.replace(suffix, "")
    version_tag = _get_godot_version_tag(godot_ver)

    # 创建项目目录 / Create the project directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # 生成 project.godot (Godot 4 与 3 格式不同) /
    # Create project.godot (Godot 4 and 3 use different formats)
    project_godot = target_dir / "project.godot"

    major = int(version_tag.split(".")[0])
    if major >= 4:
        project_godot.write_text(
            f"""; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=5

[application]

config/name="{name}"
config/features=PackedStringArray("{version_tag}")
""",
            encoding="utf-8",
        )
    else:
        project_godot.write_text(
            f"""; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=4

[application]

config/name="{name}"
config/version="{version_tag}.0"
""",
            encoding="utf-8",
        )

    # 创建 addons/ 目录 / Create the addons/ directory
    addons_dir = target_dir / "addons"
    addons_dir.mkdir(exist_ok=True)

    # 生成 gdproject.toml / Generate gdproject.toml
    config = ProjectConfig(
        name=name,
        godot=f">={version_tag}.0",
    )
    write_project_config(config, config_path)

    # 显示创建成功信息 / Show the success message
    console.print(
        f"\n  [green]✔[/green] Project [bold]{name}[/bold] created successfully!\n"
        f"  [dim]Godot:[/dim]     [cyan]>={version_tag}.0[/cyan]\n"
        f"  [dim]Directory:[/dim] [cyan]{target_dir}[/cyan]\n"
        f"  [dim]Files created:[/dim]\n"
        f"    [cyan]project.godot[/cyan]\n"
        f"    [cyan]gdproject.toml[/cyan]\n"
        f"    [cyan]addons/[/cyan]"
    )

    # 可选: 为该项目设置引擎 / Optional: set engine for this project
    # 按所选版本过滤引擎 / Filter engines by selected version
    matching_engines = [e for e in engines if godot_ver in e]

    if matching_engines and not yes:
        set_engine = questionary.confirm(
            "Set Godot engine for this project?",
            default=True,
        ).ask()

        if set_engine:
            engine_id = ""
            if len(matching_engines) == 1:
                engine_id = matching_engines[0]
            else:
                engine_id = questionary.select(
                    "Select engine:",
                    choices=matching_engines,
                    default=matching_engines[0],
                ).ask()

            if engine_id:
                _set_project_engine(target_dir, engine_id)

    # 打开 Godot 编辑器 / Open the Godot editor
    if open_editor:
        _open_godot(target_dir, godot_ver)


def _set_project_engine(project_dir: Path, engine_id: str) -> None:
    """
    为项目设置 Godot 引擎.

    Set the Godot engine for a project.

    ----

    Args:
        project_dir: 项目根目录 / Project root directory.
        engine_id: 引擎 ID, 如 gdpm-godot@4.7-stable /
            Engine ID such as gdpm-godot@4.7-stable.
    """
    import json

    from gdpm.cli.godot.common import get_engines_dir, normalize_version

    name, version = engine_id.split("@", 1)

    # 查找引擎可执行文件 / Find the engine binary
    binary = ""
    if name == "gdpm-godot":
        engines_dir = get_engines_dir()
        tag = normalize_version(version)
        ver_dir = engines_dir / tag
        if ver_dir.exists():
            for app in ver_dir.glob("*.app"):
                b = app / "Contents" / "MacOS" / "Godot"
                if b.exists():
                    binary = str(b)
                    break
            if not binary:
                for f in ver_dir.iterdir():
                    if f.is_file() and not f.suffix:
                        binary = str(f)
                        break
    else:
        from gdpm.config.local_engines import get_local_engine

        engine = get_local_engine(name)
        if engine:
            binary = engine.path

    if not binary:
        console.print("  [dim]Skipping engine setup: engine not found[/dim]")
        return

    # 写入 .engines-conf.json / Write .engines-conf.json
    conf_path = project_dir / ".engines-conf.json"
    conf = {"godot": {"name": name, "version": version, "path": binary}}
    conf_path.write_text(
        json.dumps(conf, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    console.print(f"  [dim]Engine:[/dim] [cyan]{name}@{version}[/cyan]")


def _open_godot(project_dir: Path, version: str) -> None:
    """
    为项目打开 Godot 编辑器.

    Open the Godot editor for a project.

    ----

    Args:
        project_dir: 项目根目录 / Project root directory.
        version: Godot 版本 / Godot version.
    """
    binary = ""

    # 优先使用默认引擎 / Prefer the default engine
    default = get_default_engine()
    if default:
        name, ver = default.split("@", 1)
        if name == "gdpm-godot":
            engines_dir = get_engines_dir()
            tag = normalize_version(ver)
            ver_dir = engines_dir / tag
            if ver_dir.exists():
                for app in ver_dir.glob("*.app"):
                    b = app / "Contents" / "MacOS" / "Godot"
                    if b.exists():
                        binary = str(b)
                        break
                if not binary:
                    for f in ver_dir.iterdir():
                        if f.is_file() and not f.suffix:
                            binary = str(f)
                            break
        else:
            engine = get_local_engine(name)
            if engine:
                binary = engine.path

    if not binary:
        console.print("[dim]  Skipping open: no Godot engine configured[/dim]")
        return

    try:
        with subprocess.Popen(
            [binary, "-e", "--path", str(project_dir)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ):
            pass
        console.print("  Opening [cyan]Godot[/cyan]...")
    except Exception as e:
        console.print(f"  [yellow]Warning:[/yellow] Failed to open Godot: {e}")
