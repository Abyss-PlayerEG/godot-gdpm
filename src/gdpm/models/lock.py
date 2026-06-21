"""Lock file entry model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LockEntry:
    name: str
    version: str
    source: str
