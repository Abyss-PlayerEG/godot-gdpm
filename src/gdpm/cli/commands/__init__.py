"""
CLI 命令包

- 收拢 gdpm 全部命令: 14 个根命令 + godot / config 两个命令组.
- 入口 gdpm.cli.app 只从本包挂载命令; 本包各模块依赖 gdpm.cli.base
  等基础设施, 不反向依赖入口.

----

Notes
----
- 根命令: add / cache / create / export / info / init / list / lock /
  remove / search / status / sync / update / import_cmd.
- godot/: Godot 引擎管理命令组.
- config/: 全局配置命令组.
"""
