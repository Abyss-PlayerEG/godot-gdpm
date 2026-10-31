"""
锁文件条目模型. 描述 gdpm.lock 中一条已锁定的插件记录.

----

Note:
    - LockEntry: 不可变锁文件条目数据类.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LockEntry:
    """
    锁文件条目.

    ----

    Note:
        - name: 插件名称.
        - version: 锁定的版本号, 本地插件为 "local".
        - source: 来源标识 (如商店 URL 或 local).
    """

    name: str
    version: str
    source: str
