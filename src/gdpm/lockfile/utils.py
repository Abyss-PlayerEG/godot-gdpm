"""Lock file utility functions."""

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
    """Update lock file with new entries and removals.

    Args:
        lock_path: Path to gdpm.lock
        updates: Dict of name -> LockEntry to add/update
        removes: List of names to remove
    """
    entries = {e.name: e for e in read_lockfile(lock_path)}
    entries.update(updates)

    if removes:
        for name in removes:
            entries.pop(name, None)

    write_lockfile(list(entries.values()), lock_path)
