"""
锁文件管理, 读写 gdpm.lock, 锁定插件的确切版本与来源.

----

Note:
    - LockEntry: 锁文件条目.
    - read_lockfile: 读取 gdpm.lock.
    - write_lockfile: 写入 gdpm.lock.
"""

from gdpm.lockfile.lock import read_lockfile, write_lockfile
from gdpm.models.lock import LockEntry

__all__ = ["LockEntry", "read_lockfile", "write_lockfile"]
