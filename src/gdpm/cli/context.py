"""CLI context utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpm.cache.file_cache import FileCache
from gdpm.cli.common import require_project
from gdpm.config.project import ProjectConfig, read_project_config
from gdpm.installer.manager import PluginManager
from gdpm.lockfile.lock import find_lockfile, read_lockfile
from gdpm.store.client import StoreClient

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.models.dependency import Dependency
    from gdpm.models.lock import LockEntry


@dataclass
class ProjectContext:
    root: Path
    config: ProjectConfig
    config_path: Path
    addons_dir: Path
    lock_path: Path
    lock_map: dict[str, LockEntry]
    all_deps: dict[str, Dependency]


@dataclass
class ServiceContext:
    store: StoreClient
    manager: PluginManager


def get_project_context() -> ProjectContext:
    """Load project context from current directory."""
    root = require_project()
    config_path = root / "gdproject.toml"
    config = read_project_config(config_path)
    addons_dir = root / config.addons_dir
    lock_path = find_lockfile(root)
    lock_entries = read_lockfile(lock_path)
    lock_map = {e.name: e for e in lock_entries}
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
    """Create store and manager instances."""
    store = StoreClient()
    cache = FileCache(ctx.root / ".gdpm" / "cache")
    manager = PluginManager(ctx.addons_dir, cache, store)
    return ServiceContext(store=store, manager=manager)
