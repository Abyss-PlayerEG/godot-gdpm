"""
CLI 上下文工具. 定义命令共享的项目上下文与服务上下文, 并提供对应的构建函数.

----

Note:
    - ProjectContext: 项目根目录, 配置, 锁文件与依赖的聚合.
    - ServiceContext: 商店客户端与插件管理器的容器.
    - get_project_context / get_services: 上下文构建函数.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import require_project
from gdpm.config.global_config import read_global_config
from gdpm.config.project import ProjectConfig, read_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.store.client import StoreClient

if TYPE_CHECKING:
    from gdpm.models.dependency import Dependency
    from gdpm.models.lock import LockEntry


@dataclass
class ProjectContext:
    """
    项目上下文, 聚合配置与锁文件信息.

    ----

    Attributes:
        root: 项目根目录.
        config: 项目配置对象.
        config_path: gdproject.toml 的路径.
        addons_dir: 插件安装目录.
        lock_path: 锁文件路径.
        lock_map: 锁条目表, 按插件名索引.
        all_deps: 运行与开发依赖合并后的依赖表.
    """

    root: Path
    config: ProjectConfig
    config_path: Path
    addons_dir: Path
    lock_path: Path
    lock_map: dict[str, LockEntry]
    all_deps: dict[str, Dependency]


@dataclass
class ServiceContext:
    """
    服务上下文, 持有商店客户端与插件管理器.

    ----

    Attributes:
        store: Godot Asset Store API 客户端.
        manager: 插件安装管理器.
    """

    store: StoreClient
    manager: PluginManager


def get_project_context() -> ProjectContext:
    """
    从当前目录加载项目上下文. 读取 gdproject.toml 与锁文件, 合并运行和
    开发依赖后返回上下文.

    Returns:
        组装完成的项目上下文.

    Raises:
        SystemExit: 非 gdpm 项目时终止.
    """
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    lock_path = find_lockfile(root)
    lock_entries = read_lockfile(lock_path)
    lock_map = {e.name: e for e in lock_entries}
    # 合并依赖: 键冲突时开发依赖覆盖运行依赖
    all_deps = {**config.dependencies, **config.dev_dependencies}

    return ProjectContext(
        root=root,
        config=config,
        config_path=config_path,
        addons_dir=addons_dir,
        lock_path=lock_path,
        lock_map=lock_map,
        all_deps=all_deps,
    )


def get_services(ctx: ProjectContext) -> ServiceContext:
    """
    创建商店客户端与插件管理器实例.

    ----

    Args:
        ctx: 项目上下文, 提供 addons 目录.

    Returns:
        组装完成的服务上下文.
    """
    store = StoreClient()
    global_config = read_global_config()
    cache = FileCache(Path(global_config.cache_dir))
    manager = PluginManager(ctx.addons_dir, cache, store)
    return ServiceContext(store=store, manager=manager)
