"""Version and version constraint models."""

from __future__ import annotations

from dataclasses import dataclass, field

from packaging.version import Version as PkgVersion

from gdpm.utils.version import normalize_version, version_matches


@dataclass(frozen=True)
class Version:
    version: str
    _parsed: PkgVersion = field(init=False, repr=False)

    def __post_init__(self) -> None:
        normalized = normalize_version(self.version)
        object.__setattr__(self, "_parsed", PkgVersion(normalized))

    @property
    def major(self) -> int:
        return self._parsed.major

    @property
    def minor(self) -> int:
        return self._parsed.minor

    @property
    def patch(self) -> int:
        return self._parsed.micro

    @property
    def is_prerelease(self) -> bool:
        return self._parsed.is_prerelease

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed < other._parsed

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed <= other._parsed

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed > other._parsed

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed >= other._parsed

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed == other._parsed

    def __hash__(self) -> int:
        return hash(self._parsed)

    def __str__(self) -> str:
        return self.version


@dataclass(frozen=True)
class VersionConstraint:
    constraint: str

    def matches(self, version: Version) -> bool:
        return version_matches(version.version, self.constraint)

    def __str__(self) -> str:
        return self.constraint
