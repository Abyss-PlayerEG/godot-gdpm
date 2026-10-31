"""
配置管理, 提供 gdpm 项目配置 (gdproject.toml) 的读写能力.

----

Note:
    - ProjectConfig: 项目配置数据类.
    - read_project_config: 读取 gdproject.toml.
    - write_project_config: 写入 gdproject.toml.
"""

from gdpm.config.project import ProjectConfig, read_project_config, write_project_config

__all__ = [
    "ProjectConfig",
    "read_project_config",
    "write_project_config",
]
