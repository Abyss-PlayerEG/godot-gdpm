"""
gdpm 包入口. 支持以 `python -m gdpm` 方式启动 CLI, 与 `gdpm` 命令等效.

gdpm package entry point. Enables launching the CLI via
`python -m gdpm`, equivalent to the `gdpm` command.
"""

from gdpm.cli.app import main

if __name__ == "__main__":
    main()
