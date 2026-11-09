"""
版本规范化与解析工具

- 提供宽松的版本解析, 兼容 Godot Asset Store 中常见的非标准格式,
  如 "4.6.2-stable", "V1.1".

----

Notes
----
- normalize_version / normalize_constraint: 版本与约束规范化.
- parse_version / parse_specifier_set: 版本与约束解析.
- version_matches / is_compatible: 版本匹配与兼容性检查.
"""

from __future__ import annotations

import re

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


def normalize_version(version: str) -> str:
    """
    将版本字符串规范化为 PEP 440 兼容格式.

    处理常见的非标准格式.

    ----

    Parameters
    ----
    version : str
        原始版本字符串.

    Returns
    ----
    str
        规范化后的版本字符串.

    Examples
    ----
    "v1.0.0" -> "1.0.0"
    "V2.0" -> "2.0"
    "1.0.0-stable" -> "1.0.0.stable"
    "1.0.0-beta1" -> "1.0.0.beta1"
    "1.0.0-rc2" -> "1.0.0.rc2"
    """
    if not version:
        return "0.0.0"

    v = version.strip()

    # 去除 v/V 前缀
    v = re.sub(r"^[vV]+", "", v)

    # 处理稳定性后缀 (-stable, -beta, -alpha, -rc)
    # -stable → .stable
    # -beta1 → .beta1
    # -rc2 → .rc2
    v = re.sub(r"-(stable|alpha|beta|rc)(\d*)$", r".\1\2", v, flags=re.IGNORECASE)

    # 将剩余连字符替换为点号
    v = v.replace("-", ".")

    # 移除点号以外的非字母数字字符
    v = re.sub(r"[^a-zA-Z0-9.]", "", v)

    # 确保以数字开头
    if not v or not v[0].isdigit():
        v = "0.0.0"

    return v


def normalize_constraint(constraint: str) -> str:
    """
    规范化版本约束字符串.

    处理常见约束形式.

    ----

    Parameters
    ----
    constraint : str
        原始约束字符串.

    Returns
    ----
    str
        规范化后的约束字符串.

    Examples
    ----
    ">=v1.0.0" -> ">=1.0.0"
    "^1.0.0" -> ">=1.0.0,<2.0.0"
    "~1.0.0" -> ">=1.0.0,<1.1.0"
    "v1.0.0" -> "==1.0.0"
    """
    c = constraint.strip()

    # 处理 ^ 约束
    if c.startswith("^"):
        base = normalize_version(c[1:])
        parts = base.split(".")
        major = int(parts[0])
        return f">={base},<{major + 1}.0.0"

    # 处理 ~ 约束
    if c.startswith("~"):
        base = normalize_version(c[1:])
        parts = base.split(".")
        major, minor = int(parts[0]), int(parts[1])
        return f">={base},<{major}.{minor + 1}.0"

    # 处理通配符
    if c == "*":
        return ">=0.0.0"

    # 规范化约束操作符后的版本
    # >=v1.0.0 → >=1.0.0
    # ==V2.0 → ==2.0
    c = re.sub(
        r"([><=!~]+)\s*[vV]?(\d[\w.]*)",
        lambda m: m.group(1) + normalize_version(m.group(2)),
        c,
    )

    return c


def parse_version(version: str) -> Version:
    """
    解析版本字符串, 解析前先规范化.

    ----

    Parameters
    ----
    version : str
        原始版本字符串.

    Returns
    ----
    packaging.version.Version
        解析后的版本对象.

    Raises
    ----
    packaging.version.InvalidVersion
        规范化后仍不是合法版本.
    """
    normalized = normalize_version(version)
    return Version(normalized)


def parse_specifier_set(constraint: str) -> SpecifierSet:
    """
    解析版本约束, 解析前先规范化.

    ----

    Parameters
    ----
    constraint : str
        原始约束字符串.

    Returns
    ----
    packaging.specifiers.SpecifierSet
        解析后的约束集合.

    Raises
    ----
    packaging.specifiers.InvalidSpecifier
        规范化后仍不是合法约束.
    """
    normalized = normalize_constraint(constraint)
    return SpecifierSet(normalized)


def version_matches(version: str, constraint: str) -> bool:
    """
    判断版本是否满足约束, 解析失败时回退为字符串比较.

    ----

    Parameters
    ----
    version : str
        版本字符串.
    constraint : str
        约束字符串.

    Returns
    ----
    bool
        满足约束返回 True.
    """
    try:
        # 通配符始终匹配
        if constraint.strip() == "*":
            return True

        ver = parse_version(version)
        spec = parse_specifier_set(constraint)
        return ver in spec
    except InvalidVersion, InvalidSpecifier:
        # 回退为字符串比较
        return normalize_version(version) == normalize_version(constraint)


def is_compatible(
    project_godot: str,
    min_godot: str,
    max_godot: str,
) -> tuple[bool, str]:
    """
    检查插件是否与项目 Godot 版本兼容.

    ----

    Parameters
    ----
    project_godot : str
        项目 Godot 版本约束.
    min_godot : str
        插件要求的最低版本.
    max_godot : str
        插件支持的最高版本.

    Returns
    ----
    tuple[bool, str]
        (是否兼容, 说明信息) 元组.
    """
    if not project_godot or project_godot == "*":
        return True, ""

    # 过滤 None 与空值
    min_godot = min_godot if min_godot and min_godot != "None" else ""
    max_godot = max_godot if max_godot and max_godot != "None" else ""

    min_v = normalize_version(min_godot) if min_godot else ""
    max_v = normalize_version(max_godot) if max_godot else ""

    if not min_v and not max_v:
        return True, ""

    try:
        # 从项目约束中提取基础版本
        # ">=4.2.0" → "4.2.0"
        # ">=4.2.0,<5.0.0" → "4.2.0"
        base = re.sub(r"[><=!~^*\s]", "", project_godot)
        base = base.split(",")[0].strip()
        project_ver = parse_version(base)

        if max_v:
            max_ver = parse_version(max_v)
            if project_ver > max_ver:
                return False, (
                    f"Plugin supports Godot <={max_godot}, "
                    f"but project uses {project_godot}"
                )

        if min_v:
            min_ver = parse_version(min_v)
            if project_ver < min_ver:
                return False, (
                    f"Plugin requires Godot >={min_godot}, "
                    f"but project uses {project_godot}"
                )

    except InvalidVersion, ValueError:
        pass

    return True, ""
