# AGENTS.md — gdpm

gdpm 是 Godot 插件的依赖包管理器，类似 uv/npm/cargo。Python 3.14，click + httpx + rich；
通过 PyPI 和 PyInstaller 独立二进制分发。

**本文件只记录不变量 —— 永不粘贴文件树、flag 表格或复制的常量值。**
这些内容每次重构都会腐烂（见 git history）。实时状态一律从源头发现：

- 目录布局与模块职责 → `src/gdpm/` 下各文件的首个 docstring
- CLI 命令面 → `uv run gdpm --help` / `uv run gdpm <cmd> --help`
- 常量与 URL → `src/gdpm/constants.py`（单一事实源）
- 跨模块流程 → `src/gdpm/cli/commands/` 下对应命令的入口文件
- 计划中的工作与设计文档 → `notes/todo.md`（索引）；宁可写在那里，也不要往本文件里加内容

## 快捷命令

```bash
uv run gdpm <command>          # 开发模式运行
python3 scripts/check.py       # 全部检查: mypy ruff format pylint vulture deptry test
python3 scripts/check.py fix   # 自动修复 lint/format
python3 scripts/version.py X.Y.Z [tag]   # 版本升级 —— 永远不要手工改版本文件
```

## 架构规则

- 分层顺序：`models` → `config/store/cache/lockfile` → `resolver/installer` → `cli`。
  禁止反向依赖。`gdpm.cli` 只能从 `__main__.py` 进入。
- `models/` 只 import 标准库和 `gdpm.utils` —— 不得依赖 config、store、cache、cli。
- 所有外部服务（store、cache、installer）必须经由 `Protocol` 接口访问
  （`store/protocol.py`、`cache/protocol.py`、`installer/protocol.py`），用于依赖注入与测试。
  新增服务时先新增 Protocol。
- API 调用为 async（`httpx.AsyncClient`，客户端内单例复用）；终端输出用 Rich
  （`Console`、`Progress`、`Table`）；CLI 用 Click，基于 `GdpmCommand`/`GdpmGroup`。

## 代码约定

- 严格类型：mypy strict 必须通过 —— 完整类型标注 + `from __future__ import annotations`。
- 未经明确要求不写注释。模块/文件层面改用 docstring。
- lint/format 用 ruff（仓库配置）；绝不为让检查通过而削弱规则。
- 测试用 pytest + pytest-asyncio，放在 `tests/`，一个测试只测一个行为；
  mock 网络时 patch 精确的 `httpx` 调用点、用 `tmp_path` —— 永不碰真实 `$HOME`。

## 领域不变量（产品事实，非代码事实）

- **仅走镜像**：引擎二进制和 `versions.json` 全部来自 `GODOT_DOWNLOAD_MIRROR`；
  官方 API URL 不得再出现在客户端代码中。
- **`gdpm.lock` 同时存储商店插件和本地插件**；本地条目用 `version = "local"`。
- **`tag.gdpm`** 标记 `addons/` 下哪个目录属于哪个插件（安装时写入，`add --local` 时扫描）。
- **`gdpm-local/` 提交到 git；`addons/` 通常在 .gitignore 中。**
- **`.engines-conf.json`** 为项目级 Godot 引擎固定配置；二进制放在 `~/.gdpm/engines/`
  （永不放进项目目录）。
- **版本格式** `x.y.z` + `.devN | aN | bN | rcN`，且版本存在于**两个文件**
  （`pyproject.toml`、`src/gdpm/__init__.py` + `__tag__`）—— 必须经 `scripts/version.py` 修改。

## 测试与发布

- 每次提交前：`python3 scripts/check.py` 必须全绿。修复它，绝不跳过。
- 发布流程：`version.py` → 推送 `dev` → PR → squash 合并 →
  `gh release create vX.Y.Z --title vX.Y.Z --notes-file RELEASE_NOTES.md`
  （release 触发 PyPI 发布 + 二进制构建；PyPI 发布前需先批准 GitHub 的 `pypi` environment）。
  tag 必须与 pyproject 版本一致、发布流水线会跑全量检查+冒烟测试，不满足会直接失败。
