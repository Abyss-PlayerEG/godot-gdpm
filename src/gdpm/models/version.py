"""
版本与版本约束模型. 定义插件版本解析与约束匹配的核心数据结构.

----

Note:
    - Version: 可比较的语义化版本, 内部基于 packaging.version 解析.
    - VersionConstraint: 版本约束表达式, 用于判断版本是否匹配.
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

    ----

    Note:
        - version: 原始版本字符串.
        - _parsed: 规范化后的解析结果, 不参与构造与 repr.
    """

    version: str
    _parsed: PkgVersion = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """
        规范化版本字符串并缓存解析结果.
        """
        normalized = normalize_version(self.version)
        object.__setattr__(self, "_parsed", PkgVersion(normalized))

    @property
    def major(self) -> int:
        """获取主版本号."""
        return self._parsed.major

    @property
    def minor(self) -> int:
        """获取次版本号."""
        return self._parsed.minor

    @property
    def patch(self) -> int:
        """获取补丁版本号."""
        return self._parsed.micro

    @property
    def is_prerelease(self) -> bool:
        """是否为预发布版本."""
        return self._parsed.is_prerelease

    def __lt__(self, other: object) -> bool:
        """
        判断本版本是否小于另一版本.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed < other._parsed

    def __le__(self, other: object) -> bool:
        """
        判断本版本是否小于或等于另一版本.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed <= other._parsed

    def __gt__(self, other: object) -> bool:
        """
        判断本版本是否大于另一版本.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed > other._parsed

    def __ge__(self, other: object) -> bool:
        """
        判断本版本是否大于或等于另一版本.
        """
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed >= other._parsed

    def __eq__(self, other: object) -> bool:
        """判断两个版本是否相等."""
        if not isinstance(other, Version):
            return NotImplemented
        return self._parsed == other._parsed

    def __hash__(self) -> int:
        """
        基于解析后的版本计算哈希.
        """
        return hash(self._parsed)

    def __str__(self) -> str:
        """返回原始版本字符串."""
        return self.version


@dataclass(frozen=True)
class VersionConstraint:
    """
    版本约束.

    ----

    Note:
        - constraint: 约束表达式字符串 (如 ">=1.0.0,<2.0.0").
    """

    constraint: str

    def matches(self, version: Version) -> bool:
        """
        判断版本是否满足约束.

        ----

        Args:
            version: 待检查的版本.

        Returns:
            bool: 满足约束返回 True, 否则返回 False.
        """
        return version_matches(version.version, self.constraint)

    def __str__(self) -> str:
        """返回约束表达式字符串."""
        return self.constraint
