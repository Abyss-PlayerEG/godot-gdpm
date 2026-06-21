"""Dependency model."""

from __future__ import annotations

from dataclasses import dataclass

from gdpm.models.version import VersionConstraint


@dataclass(frozen=True)
class Dependency:
    name: str
    constraint: VersionConstraint
    publisher_slug: str = ""
    path: str = ""
    is_dev: bool = False
    source: str = ""

    @classmethod
    def from_spec(
        cls,
        name: str,
        spec: str,
        *,
        publisher_slug: str = "",
        path: str = "",
        is_dev: bool = False,
    ) -> Dependency:
        if spec.startswith("^"):
            base = spec[1:]
            parts = base.split(".")
            major = int(parts[0])
            constraint = f">={base},<{major + 1}.0.0"
        elif spec.startswith("~"):
            base = spec[1:]
            parts = base.split(".")
            major, minor = int(parts[0]), int(parts[1])
            constraint = f">={base},<{major}.{minor + 1}.0"
        elif spec == "*":
            constraint = ">=0.0.0"
        else:
            constraint = spec

        return cls(
            name=name,
            constraint=VersionConstraint(constraint),
            publisher_slug=publisher_slug,
            path=path,
            is_dev=is_dev,
        )
