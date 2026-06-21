"""Configuration management."""

from gdpm.config.project import ProjectConfig, read_project_config, write_project_config

__all__ = [
    "ProjectConfig",
    "read_project_config",
    "write_project_config",
]
