"""Lock file management."""

from gdpm.lockfile.lock import read_lockfile, write_lockfile
from gdpm.models.lock import LockEntry

__all__ = ["LockEntry", "read_lockfile", "write_lockfile"]
