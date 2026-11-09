"""
gdpm godot install/uninstall 命令

- 安装与卸载 Godot 引擎.

----

Notes
----
- godot_install: 分片下载并解压 Godot 引擎 (仅 stable).
- _is_stable_tag: stable-only 门禁, 非 stable 通道拒绝安装.
- Ctrl+C 取消: 下载/解压两段清理现场并以 130 退出.
- godot_uninstall: 删除已安装的 Godot 引擎.
"""

from __future__ import annotations

import shutil
import zipfile
from typing import TYPE_CHECKING

import click
import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm

from gdpm.cli.base import GdpmCommand
from gdpm.cli.commands.godot.common import (
    build_download_urls,
    get_engines_dir,
    normalize_version,
)
from gdpm.cli.common import console
from gdpm.cli.i18n import t
from gdpm.config.global_config import read_global_config
from gdpm.utils.download import clamp_workers, download_file_chunked
from gdpm.utils.install import get_godot_ext, get_godot_platform

if TYPE_CHECKING:
    from collections.abc import Callable


def _create_download_tasks(
    progress: Progress, total_name: str, workers: int | None = None
) -> tuple[list[TaskID], TaskID]:
    """
    创建下载进度任务: 总进度条 (居首行) + n 条分片条 (其下方惰性显形).

    分片条初始不可见, 由分片回调首次触发时定长显形;
    每个任务必须携带 name 字段 — TextColumn 按 {task.fields[name]} 渲染,
    缺失会在显形渲染时抛 KeyError.
    样式随字段走: name 自带标记 (切片 [grey50] 灰, 总条 [bold blue] 蓝),
    TextColumn 模板保持无色 —— 单 Progress 所有任务共列, 这是按任务着色
    的唯一途径.

    ----

    Parameters
    ----
    progress : Progress
        rich 进度条实例.
    total_name : str
        总进度条显示名, 如 'Godot 4.7-stable'.
    workers : int | None, optional
        分片数, None 时回退默认; 生效值经 clamp_workers 收敛到 [1, 32],
        与 download_file_chunked 的真实切片数保持一致.

    Returns
    ----
    tuple[list[TaskID], TaskID]
        (分片任务 ID 列表, 总任务 ID).
    """
    n = clamp_workers(workers)
    # 样式进字段: 切片标签灰色, 总条保持 bold blue (模板已去色)
    # 总进度条先添加 → 渲染在首行, 分片条随后在其下方逐条显形
    task_id = progress.add_task(
        "download", name=f"[bold blue]{total_name}[/bold blue]", total=None
    )
    slice_ids = [
        progress.add_task(
            f"Slice {i + 1}/{n}",
            name=f"[grey50]Slice {i + 1}/{n}[/grey50]",
            total=None,
            visible=False,
        )
        for i in range(n)
    ]
    return slice_ids, task_id


def _make_slice_handler(
    progress: Progress, slice_ids: list[TaskID]
) -> Callable[[int | None, int, int], None]:
    """
    构造分片进度回调, 供 download_file_chunked 的 on_slice 使用.

    首次收到某片回调时为该条定长并显形; index 为 None (回退单流)
    时收起全部分片条.

    ----

    Parameters
    ----
    progress : Progress
        rich 进度条实例.
    slice_ids : list[TaskID]
        _create_download_tasks 创建的分片任务 ID 列表.

    Returns
    ----
    Callable[[int | None, int, int], None]
        形如 on_slice 的回调函数.
    """

    def handler(index: int | None, done: int, slice_total: int) -> None:
        if index is None:
            for tid in slice_ids:
                progress.update(tid, visible=False)
            return
        tid = slice_ids[index]
        if progress.tasks[int(tid)].total is None:
            progress.update(tid, total=slice_total, visible=True)
        progress.update(tid, completed=done)

    return handler


def _is_stable_tag(tag: str) -> bool:
    """
    判断 tag 是否属于 stable 通道 (空 flavor 视为 stable).

    ----

    Parameters
    ----
    tag : str
        规范化后的版本 tag, 如 '4.7-stable', '4.8-beta2'.

    Returns
    ----
    bool
        stable 通道返回 True, 非 stable (rc/beta/alpha/dev) 返回 False.
    """
    _, _, flavor = tag.partition("-")
    return flavor in ("", "stable")


@click.command(
    name="install",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot install 4.7", "Install latest 4.7 stable"),
        ("gdpm godot install 4.7 --csharp", "Install C# version"),
        ("gdpm godot install 3.6.2-stable", "Install specific version"),
    ],
)
@click.argument("version")
@click.option("--csharp", "-cs", is_flag=True, help="Install C# (mono) version")
def godot_install(version: str, csharp: bool) -> None:
    """安装一个 Godot 引擎版本 (仅 stable)."""
    if "-csharp" in version or "-mono" in version:
        csharp = True

    engines_dir = get_engines_dir()
    tag = normalize_version(version)

    # stable-only 门禁: 下载面只收正式版, 非 stable 通道一律拒绝
    if not _is_stable_tag(tag):
        console.print(
            f"[red]Error:[/red] Non-stable version [cyan]{tag}[/cyan] "
            "is not supported.\n"
            "  gdpm manages stable releases only. Use "
            "[bold]gdpm godot list -r[/bold] to see available stable versions."
        )
        return

    suffix = "-csharp" if csharp else ""
    ver_dir = engines_dir / f"{tag}{suffix}"

    if ver_dir.exists():
        # click 不渲染 rich 标记 → 用 rich Confirm (标记渲染 + 跟随语言)
        prompt = t("ui.reinstall_confirm").format(engine=f"[cyan]{tag}{suffix}[/cyan]")
        if not Confirm.ask(f"  {prompt}"):
            return
        # 确认后删除旧安装目录以便重装
        shutil.rmtree(ver_dir, onexc=lambda *args: None)

    # 官方优先, 官方走不通切换自建镜像 (两个 base 写死在 constants)
    urls = build_download_urls(tag, csharp)

    plat = get_godot_platform()
    ext = get_godot_ext()
    filename = f"Godot_v{tag}{suffix}_{plat}.{ext}"
    zip_path = engines_dir / filename

    # 统一并行度: 分片数与进度条均取全局配置 parallel_downloads
    workers = read_global_config().parallel_downloads

    def _run_download(target_url: str) -> None:
        """一次完整的进度显示 + 分片下载 (每次尝试全新进度条, 严格证书校验)."""
        progress = Progress(
            # 模板不染色: 样式由 name 字段自带 (单 Progress 共列, 按任务着色)
            TextColumn("{task.fields[name]}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )
        with progress:
            # 主进度条居首行, 分片条在其下按回调逐条显形
            slice_ids, task_id = _create_download_tasks(
                progress, f"Godot {tag}{suffix}", workers
            )

            last_downloaded = 0

            def on_progress(done: int, total_bytes: int, _speed: float) -> None:
                nonlocal last_downloaded
                # 首次回调设置总量, 之后按增量推进进度条
                if total_bytes and progress.tasks[int(task_id)].total is None:
                    progress.update(task_id, total=total_bytes)
                progress.update(task_id, advance=done - last_downloaded)
                last_downloaded = done

            on_slice = _make_slice_handler(progress, slice_ids)

            # 多片并行下载, 服务器不支持 Range 时自动回退单流
            download_file_chunked(
                target_url,
                engines_dir,
                filename=filename,
                on_progress=on_progress,
                on_slice=on_slice,
                workers=workers,
            )

    def _report_failure(error: Exception) -> None:
        """下载失败提示 (404 保留版本不存在的友好指引)."""
        if (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code == 404
        ):
            console.print(
                f"[red]Error:[/red] Version [cyan]{tag}[/cyan] not found.\n"
                "  Use [bold]gdpm godot list -r[/bold] "
                "to see available versions."
            )
        else:
            console.print(f"[red]Error:[/red] Download failed: {error}")

    def _abort_download() -> None:
        """Ctrl+C: 清理半成品压缩包, 以 130 干净退出 (不打印 Aborted/traceback)."""
        if zip_path.exists():
            zip_path.unlink()
        console.print("\n[yellow]Cancelled.[/yellow]")
        raise SystemExit(130) from None

    last_error: Exception | None = None
    for index, target_url in enumerate(urls):
        try:
            _run_download(target_url)
            last_error = None
            break
        except KeyboardInterrupt:
            _abort_download()
        except Exception as attempt_error:
            last_error = attempt_error
            if index + 1 < len(urls):
                # 官方失败才有下一站: 自动切换自建镜像
                console.print(
                    f"[dim]Official channel failed ({type(attempt_error).__name__}), "
                    "switching to download mirror...[/dim]"
                )
    if last_error is not None:
        _report_failure(last_error)
        if zip_path.exists():
            zip_path.unlink()
        return

    console.print("Extracting...")

    try:
        from gdpm.cli.commands.godot.common import prepare_engine_dir

        # 解压到版本目录并修复执行权限
        ver_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(ver_dir)

        prepare_engine_dir(ver_dir)

        zip_path.unlink()
        console.print(f"[green]✓[/green] Installed Godot [bold]{tag}{suffix}[/bold]")
    except KeyboardInterrupt:
        # Ctrl+C: 清理残留目录与压缩包, 干净退出
        if ver_dir.exists():
            shutil.rmtree(ver_dir, ignore_errors=True)
        if zip_path.exists():
            zip_path.unlink()
        console.print("\n[yellow]Cancelled.[/yellow]")
        raise SystemExit(130) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] Extraction failed: {e}")
        # 解压失败时清理残留目录和压缩包
        if ver_dir.exists():
            shutil.rmtree(ver_dir)
        if zip_path.exists():
            zip_path.unlink()


@click.command(
    name="uninstall",
    cls=GdpmCommand,
    examples=[
        ("gdpm godot uninstall 4.7", "Uninstall Godot 4.7"),
        ("gdpm godot uninstall 4.7 -cs", "Uninstall Godot 4.7 C#"),
    ],
)
@click.argument("version")
@click.option("--csharp", "-cs", is_flag=True, help="Uninstall C# (mono) version")
def godot_uninstall(version: str, csharp: bool) -> None:
    """卸载一个 Godot 引擎版本."""
    engines_dir = get_engines_dir()
    suffix = ""
    if "-csharp" in version or "-mono" in version or csharp:
        suffix = "-csharp"
        version = version.replace("-csharp", "").replace("-mono", "")
    tag = normalize_version(version)
    ver_dir = engines_dir / f"{tag}{suffix}"

    if not ver_dir.exists():
        console.print(
            f"[red]Error:[/red] Godot [cyan]{tag}{suffix}[/cyan] is not installed."
        )
        return

    shutil.rmtree(ver_dir)
    console.print(f"[green]✓[/green] Uninstalled Godot [bold]{tag}{suffix}[/bold]")
