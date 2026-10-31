"""
依赖项模型. 描述插件依赖的声明信息, 包括名称, 版本约束与来源.

----

Note:
    - Dependency: 不可变依赖项数据类.
"""

from __future__ import annotations

from dataclasses import dataclass

from gdpm.models.version import VersionConstraint


@dataclass(frozen=True)
class Dependency:
    """
    插件依赖项.

    ----

    Note:
        - name: 依赖插件名称.
        - constraint: 版本约束.
        - publisher_slug: 发布者 slug, 用于商店定位.
        - path: 本地路径 (本地依赖时使用).
        - is_local: 是否为本地依赖.
        - is_dev: 是否为开发依赖.
        - source: 来源标识 (如商店 URL 或 local).
    """

    name: str
    constraint: VersionConstraint
    publisher_slug: str = ""
    path: str = ""
    is_local: bool = False
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
        is_local: bool = False,
        is_dev: bool = False,
    ) -> Dependency:
        """
        从版本规范字符串构建依赖. 支持 caret (^), tilde (~) 与通配 (*) 简写,
        其余按原样作为约束.

        ----

        Note:
            - "^1.2.3" -> ">=1.2.3,<2.0.0" (锁定主版本).
            - "~1.2.3" -> ">=1.2.3,<1.3.0" (锁定主次版本).
            - "*" -> ">=0.0.0" (任意版本).

        ----

        Args:
            name: 依赖插件名称.
            spec: 版本规范字符串.
            publisher_slug: 发布者 slug.
            path: 本地路径.
            is_local: 是否为本地依赖.
            is_dev: 是否为开发依赖.

        Returns:
            Dependency: 解析后的依赖项.
        """
        if spec.startswith("^"):
            # caret: 允许不改动主版本的更新
            base = spec[1:]
            parts = base.split(".")
            major = int(parts[0])
            constraint = f">={base},<{major + 1}.0.0"
        elif spec.startswith("~"):
            # tilde: 仅允许补丁位更新
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
            is_local=is_local,
            is_dev=is_dev,
        )
