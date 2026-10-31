"""
锁文件条目模型. 描述 gdpm.lock 中一条已锁定的插件记录.

Describes one locked plugin record in gdpm.lock.

----

Note:
    - LockEntry: 不可变锁文件条目数据类 / Immutable lock file entry dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LockEntry:
    """
    锁文件条目.

    A single lock file entry.

    ----

    Note:
        - name: 插件名称 / Plugin name.
        - version: 锁定的版本号, 本地插件为 "local" /
            Locked version string; "local" for local plugins.
        - source: 来源标识 (如商店 URL 或 local) /
            Source identifier (e.g. store URL or local).
    """

    name: str
    version: str
    source: str
