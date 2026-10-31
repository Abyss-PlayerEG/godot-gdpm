"""
版本与版本约束模型. 定义插件版本解析与约束匹配的核心数据结构.

Core data structures for plugin version parsing and constraint
matching.

----

Note:
    - Version: 可比较的语义化版本, 内部基于 packaging.version 解析 /
        Comparable semantic version, parsed via packaging.version.
    - VersionConstraint: 版本约束表达式, 用于判断版本是否匹配 /
        Version constraint expression used to match versions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from packaging.version import Version as PkgVersion

from gdpm.utils.version import normalize_version, version_matches


@dataclass(frozen=True)
class Version:
    """
    可比较的插件版本. 冻结数据类, 构造时将原始版本字符串规范化并解析为
    packaging.version.Version.

    A comparable plugin version. Frozen dataclass; normalizes and
    parses the raw version string into a packaging.version.Version at
    construction time.

    ----

    Note:
        - version: 原始版本字符串 / The raw version string.
        - _parsed: 规范化后的解析结果, 不参与构造与 repr /
            Normalized parsed version, excluded from init and repr.
    """

    version: str
    _parsed: PkgVersion = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """
        规范化版本字符串并缓存解析结果.

        Normalize the version string and cache the parsed result.
        """
        normalized = normalize_version(self.version)
        object.__setattr__(self, "_parsed", PkgVersion(normalized))

    @property
    def major(self) -> int:
        """获取主版本号 / Get the major version number."""
        return self._parsed.major

    @property
    def minor(self) -> int:
        """获取次版本号 / Get the minor version number."""
        return self._parsed.minor

    @property
    def patch(self) -> int:
        """获取补丁版本号 / Get the patch version number."""
        return self._parsed.micro

    @property
    def is_prerelease(self) -> bool:
        """是否为预发布版本 / Whether this is a pre-release version."""
        return self._parsed.is_prerelease

    def __lt__(self, other: object) -> bool:
        """
        判断本版本是否小于另一版本.

        Check whether this version is less than another.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed < other._parsed

    def __le__(self, other: object) -> bool:
        """
        判断本版本是否小于或等于另一版本.

        Check whether this version is less than or equal to another.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed <= other._parsed

    def __gt__(self, other: object) -> bool:
        """
        判断本版本是否大于另一版本.

        Check whether this version is greater than another.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed > other._parsed

    def __ge__(self, other: object) -> bool:
        """
        判断本版本是否大于或等于另一版本.

        Check whether this version is greater than or equal to another.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed >= other._parsed

    def __eq__(self, other: object) -> bool:
        """判断两个版本是否相等 / Check whether two versions are equal."""
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed == other._parsed

    def __hash__(self) -> int:
        """
        基于解析后的版本计算哈希.

        Compute the hash from the parsed version.
        """
        return hash(self._parsed)

    def __str__(self) -> str:
        """返回原始版本字符串 / Return the raw version string."""
        return self.version


@dataclass(frozen=True)
class VersionConstraint:
    """
    版本约束.

    A version constraint.

    ----

    Note:
        - constraint: 约束表达式字符串 (如 ">=1.0.0,<2.0.0") /
            Constraint expression string (e.g. ">=1.0.0,<2.0.0").
    """

    constraint: str

    def matches(self, version: Version) -> bool:
        """
        判断版本是否满足约束.

        Check whether a version satisfies this constraint.

        ----

        Args:
            version: 待检查的版本 / The version to check.

        Returns:
            bool: 满足约束返回 True, 否则返回 False /
                True if the version matches, False otherwise.
        """
        return version_matches(version.version, self.constraint)

    def __str__(self) -> str:
        """返回约束表达式字符串 / Return the constraint string."""
        return self.constraint
