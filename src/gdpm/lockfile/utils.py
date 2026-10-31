"""
锁文件工具函数, 在读写 gdpm.lock 之上提供增量更新等便捷操作.

Lock file utility functions. Provide convenience operations such as
incremental updates on top of reading and writing gdpm.lock.

----

Note:
    - update_lockfile: 按增删集合增量更新锁文件 /
        Incrementally update the lock file with additions and removals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gdpm.lockfile.lock import read_lockfile, write_lockfile

if TYPE_CHECKING:
    from pathlib import Path

    from gdpm.models.lock import LockEntry


def update_lockfile(
    lock_path: Path,
    updates: dict[str, LockEntry],
    removes: list[str] | None = None,
) -> None:
    """
    增量更新锁文件, 合并新增/更新条目并删除指定条目后整体重写 gdpm.lock.

    Incrementally update the lock file. Merge added/updated entries,
    drop the specified ones, then rewrite gdpm.lock as a whole.

    ----

    Args:
        lock_path: gdpm.lock 的路径 / Path to gdpm.lock.
        updates: 以名称为键的待新增/更新条目 /
            Dict of name -> LockEntry to add or update.
        removes: 待删除的依赖名称列表, 可为 None /
            List of names to remove, may be None.
    """
    entries = {e.name: e for e in read_lockfile(lock_path)}
    entries.update(updates)

    if removes:
        for name in removes:
            entries.pop(name, None)

    write_lockfile(list(entries.values()), lock_path)
