# v0.1.0b1

## English

### New Features

- **Godot Engine Management** — Install, uninstall, and switch Godot engine versions directly from CLI.
  - `gdpm godot install <version>` — Download and install from GitHub (supports `--csharp`).
  - `gdpm godot uninstall <version>` — Remove installed engine.
  - `gdpm godot list` / `gdpm godot list -r` — List installed or remote versions with pagination.
  - `gdpm godot add <path>` — Add a local Godot engine (e.g., Steam version).
  - `gdpm godot remove <name>` — Remove a local engine.
  - `gdpm godot use <id>` — Set engine for current project (`Name@Version` format).
  - `gdpm godot default <id>` — Set fallback engine for projects without explicit config.
  - `gdpm godot info` — Show current engine configuration.
  - `gdpm godot open` — Open Godot editor (`--run` to run project instead).
- **`gdpm create`** — Interactive project creation with engine selection, template detection, and Godot version compatibility.
- **Global Cache** — Shared cache across projects with split index, `gdpm cache info` / `gdpm cache clean`.
- **Export/Import** — `gdpm export` / `gdpm import` with zip archive support.
- **GitHub Token Support** — Auto-detect token from `~/.gdpm/github_token.txt` for higher API rate limits.
- **`gdpm info` Redesign** — Rich panel with plugin name, version, description, and install details.
- **Download Progress Bar** — Progress bar in `gdpm sync` for parallel downloads (max 5 concurrent).
- **`gdpm sync --frozen`** — Lock file sync for CI environments.
- **Shell Completion** — Tab completion for zsh, bash, fish in install/uninstall scripts.
- **Build Script** — PyInstaller-based build with `scripts/build.py`.
- **`-i` Info Panel** — Version, platform, and install type in `gdpm -i`.
- **`-V` Colored Output** — Version display with platform info, styled like uv.

### Installation

```bash
pip install godot-gdpm==0.1.0b1
```

Or download from GitHub Releases:

```bash
# macOS / Linux
tar -xzf gdpm_v0.1.0b1_*.tar.gz
cd gdpm
./install.sh

# Windows
# Extract zip, run install.bat
```

### Improvements

- Subcommand help redesigned with Rich panels and usage examples.
- `gdpm list` uses Rich panel with color-coded source prefixes.
- `gdpm search` output formatted with panels.
- `gdpm godot add` detects binary, shows version, checks duplicates.
- `gdpm godot list -id` shows compact engine ID view.
- macOS install scripts auto-remove quarantine attributes.
- Hash verification for engine downloads.
- Version normalization (`4.7` → `4.7-stable`).
- Platform-aware download URL resolution via GitHub API.
- `GdpmConsole` auto-adds spacing to all CLI output.
- Suppress SSL verification for GitHub API requests.

### Bug Fixes

- Fixed `gdpm godot open` blocking terminal until Godot exits.
- Fixed `gdpm sync` parallel download passing zip_path correctly.
- Fixed `gdpm create` engine version filtering and deduplication.
- Fixed `gdpm init` preventing overwrite of existing config.
- Fixed `gdpm list` sorting and folder name display.
- Fixed `gdpm info` working outside gdpm projects.
- Fixed deprecated `rmtree` onerror and `Popen` context manager.
- Fixed legacy `except` syntax for PyCharm compatibility.
- Fixed mypy, pylint, and deptry errors.
- Fixed `-h` output with consistent blank line handling.
- Fixed cache index path and download destination directory.
- Fixed `gdpm add --local` scan message formatting.

### Infrastructure

- Pylint added to CI workflow.
- Multi-platform Nuitka build support.
- `scripts/check.py` with legacy syntax check.
- VS Code workspace file.
- AGENTS.md for AI agent context.

---

## 中文

### 新功能

- **Godot 引擎管理** — 直接通过 CLI 安装、卸载和切换 Godot 引擎版本。
  - `gdpm godot install <版本>` — 从 GitHub 下载并安装（支持 `--csharp`）。
  - `gdpm godot uninstall <版本>` — 移除已安装的引擎。
  - `gdpm godot list` / `gdpm godot list -r` — 列出已安装或远程版本，并支持分页。
  - `gdpm godot add <路径>` — 添加本地 Godot 引擎（如 Steam 版本）。
  - `gdpm godot remove <名称>` — 移除本地引擎。
  - `gdpm godot use <id>` — 为当前项目设置引擎（`Name@Version` 格式）。
  - `gdpm godot default <id>` — 为未显式配置引擎的项目设置回退引擎。
  - `gdpm godot info` — 显示当前引擎配置。
  - `gdpm godot open` — 打开 Godot 编辑器（加 `--run` 则直接运行项目）。
- **`gdpm create`** — 交互式创建项目，包含引擎选择、模板检测与 Godot 版本兼容性检查。
- **全局缓存** — 跨项目共享缓存，带拆分索引，提供 `gdpm cache info` / `gdpm cache clean`。
- **导出/导入** — `gdpm export` / `gdpm import` 支持 zip 归档。
- **GitHub Token 支持** — 自动从 `~/.gdpm/github_token.txt` 检测令牌，提高 API 速率限制。
- **`gdpm info` 重设计** — 使用 Rich 面板展示插件名称、版本、描述及安装详情。
- **下载进度条** — `gdpm sync` 中为并行下载（最多 5 个并发）提供进度条。
- **`gdpm sync --frozen`** — 面向 CI 环境的锁定文件同步。
- **Shell 补全** — 安装/卸载脚本内置 zsh、bash、fish 的 Tab 补全。
- **构建脚本** — 基于 PyInstaller 的构建，通过 `scripts/build.py` 执行。
- **`-i` 信息面板** — `gdpm -i` 显示版本、平台和安装类型。
- **`-V` 彩色输出** — 版本显示包含平台信息，样式类似 uv。

### 安装

```bash
pip install godot-gdpm==0.1.0b1
```

或从 GitHub Releases 下载：

```bash
# macOS / Linux
tar -xzf gdpm_v0.1.0b1_*.tar.gz
cd gdpm
./install.sh

# Windows
# 解压 zip，运行 install.bat
```

### 改进

- 子命令帮助经 Rich 面板重设计，并附使用示例。
- `gdpm list` 使用 Rich 面板，带彩色来源前缀。
- `gdpm search` 输出使用面板格式化。
- `gdpm godot add` 检测二进制文件、显示版本并检查重复。
- `gdpm godot list -id` 显示紧凑的引擎 ID 视图。
- macOS 安装脚本自动移除隔离属性。
- 引擎下载的哈希校验。
- 版本规范化（`4.7` → `4.7-stable`）。
- 通过 GitHub API 按平台解析下载 URL。
- `GdpmConsole` 为所有 CLI 输出自动添加空行间距。
- 对 GitHub API 请求禁用 SSL 验证。

### Bug 修复

- 修复 `gdpm godot open` 阻塞终端直到 Godot 退出。
- 修复 `gdpm sync` 并行下载时正确传递 zip_path 参数。
- 修复 `gdpm create` 引擎版本过滤与去重。
- 修复 `gdpm init` 阻止覆盖已有配置。
- 修复 `gdpm list` 排序和文件夹名称显示。
- 修复 `gdpm info` 在非 gdpm 项目外正常工作。
- 修复已弃用的 `rmtree` 的 onerror 回调与 `Popen` 上下文管理器。
- 修复遗留的 `except` 语法以兼容 PyCharm。
- 修复 mypy、pylint 与 deptry 报错。
- 修复 `-h` 输出中空行处理不一致的问题。
- 修复缓存索引路径与下载目标目录。
- 修复 `gdpm add --local` 扫描信息的格式。

### 基础设施

- CI 工作流中加入 Pylint。
- 支持多平台 Nuitka 构建。
- 包含遗留语法检查的 `scripts/check.py`。
- VS Code 工作区文件。
- 用于 AI 代理上下文的 AGENTS.md。

---

# v0.0.6

## English

### Changes

- **Optimized Build** — Changed from `--onefile` to `--onedir` for faster startup (~1s vs ~10s).
- **Platform Archives** — Each platform archive includes install/uninstall scripts.

### Installation

```bash
# macOS / Linux
tar -xzf gdpm_v0.0.6_*.tar.gz
cd gdpm
./install.sh

# Windows
# Extract zip, run install.bat
```

### New Features

- **Local Plugin Management** — `gdpm add --local` to pack local plugins into `gdpm-local/` with hash-based change detection.
- **Install Scripts** — Platform-specific install/uninstall scripts (macOS, Linux, Windows) included in release archives.
- **macOS Gatekeeper Bypass** — Install script automatically removes quarantine attributes.
- **Global `-y/--yes` Option** — Skip all confirmation prompts with `gdpm -y <command>`.
- **Common Options Display** — Help output shows shared options (`-h`, `-V`, `-y`).

### Improvements

- Auto-detect Godot version from `project.godot` (supports 1.x through 4.x).
- Unified version format (`__version__` uses PyPI-compatible format).
- Local plugins skipped during version checks and updates.
- Version display shows tag separately (e.g., `gdpm v0.0.2 [beta]`).
- Hash-based change detection for local plugins (skip unchanged).
- Rename detection for local plugins.

### Bug Fixes

- Fixed compatibility check for plugins with `None` max Godot version.
- Fixed `gdpm lock` to skip local plugins.
- Fixed `gdpm sync` to update lock file for local plugins.
- Fixed Windows build workflow (cache paths, entry point, archive).

### Infrastructure

- AGENTS.md for AI agent context.
- Code quality check script (`scripts/check.py`).
- Version management script (`scripts/version.py`).

---

## 中文

### 变更

- **优化构建** — 从 `--onefile` 切换为 `--onedir`，启动速度大幅提升（约1秒 vs 约10秒）。
- **平台打包** — 每个平台的压缩包内均包含安装/卸载脚本。

### 安装

```bash
# macOS / Linux
tar -xzf gdpm_v0.0.6_*.tar.gz
cd gdpm
./install.sh

# Windows
# 解压 zip 后运行 install.bat
```

### 新功能

- **本地插件管理** — `gdpm add --local` 可将本地插件打包到 `gdpm-local/` 目录，并支持基于哈希的变更检测。
- **安装脚本** — 发布压缩包中附带各平台（macOS、Linux、Windows）的安装/卸载脚本。
- **绕过 macOS Gatekeeper** — 安装脚本会自动移除隔离属性。
- **全局 `-y/--yes` 选项** — 使用 `gdpm -y <命令>` 可跳过所有确认提示。
- **通用选项展示** — 帮助信息中显示共享选项（`-h`、`-V`、`-y`）。

### 改进

- 从 `project.godot` 自动检测 Godot 版本（支持 1.x 至 4.x）。
- 统一版本格式（`__version__` 采用与 PyPI 兼容的格式）。
- 版本检查与更新时跳过本地插件。
- 版本显示单独展示标签（例如 `gdpm v0.0.2 [beta]`）。
- 本地插件基于哈希的变更检测（跳过未变更的插件）。
- 本地插件支持重命名检测。

### Bug 修复

- 修复了对最大 Godot 版本为 `None` 的插件的兼容性检查。
- 修复 `gdpm lock` 以跳过本地插件。
- 修复 `gdpm sync` 为本地插件更新锁定文件的问题。
- 修复 Windows 构建工作流（缓存路径、入口点、打包）。

### 基础设施

- 添加 `AGENTS.md` 为 AI 代理提供上下文。
- 代码质量检查脚本（`scripts/check.py`）。
- 版本管理脚本（`scripts/version.py`）。

---

# v0.0.3

## English

### New Features

- **Godot Asset Store Integration** — Search, browse, and install plugins directly from the official Godot Asset Store API.
- **Dependency Management** — Automatic dependency resolution with `gdproject.toml` and `gdpm.lock`.
- **Version Constraints** — Support for semver syntax (`^1.0.0`, `~1.5.0`, `>=1.0.0,<2.0.0`).
- **Template Detection** — Automatically identifies project templates vs addons.
- **Godot Version Compatibility** — Checks plugin compatibility with your project's Godot version.
- **Plugin Tracking** — `tag.gdpm` system for tracking bundled plugin sub-packages.
- **Auto-detect Godot Version** — Reads `project.godot` to detect Godot version (supports 1.x through 4.x).

### CLI Commands

- `gdpm init` — Initialize a new gdpm project
- `gdpm add <plugin>` — Add plugins to the project
- `gdpm remove <plugin>` — Remove plugins
- `gdpm sync` — Sync addons/ to lock file state
- `gdpm lock` — Generate or update lock file
- `gdpm list` — List installed plugins
- `gdpm status` — Show plugin status and available updates
- `gdpm search <query>` — Search Godot Asset Store
- `gdpm info <plugin>` — Show plugin details
- `gdpm update` — Update plugins to newer versions

### Improvements

- Progress bars with download speed for plugin installations.
- Beautiful CLI help interface with rich formatting.
- Short options `-V` (version) and `-h` (help).
- Version tag support (dev, beta, alpha, rc, stable).
- PyPI-compatible version formats.

### Infrastructure

- GitHub Actions CI with mypy, ruff, and format checks.
- Multi-platform build workflow (Linux, macOS arm64/x64, Windows).
- PyPI publishing with trusted publishers.
- Code quality tools: mypy, ruff, vulture, deptry, pre-commit.

---

## 中文

### 新功能

- **Godot 资源商店集成** — 直接从官方 Godot 资源商店 API 搜索、浏览并安装插件。
- **依赖管理** — 通过 `gdproject.toml` 和 `gdpm.lock` 自动解析依赖。
- **版本约束** — 支持语义化版本语法（`^1.0.0`、`~1.5.0`、`>=1.0.0,<2.0.0`）。
- **模板检测** — 自动区分项目模板与普通插件。
- **Godot 版本兼容性** — 检查插件与您项目的 Godot 版本的兼容性。
- **插件追踪** — 用于追踪捆绑插件子包的 `tag.gdpm` 系统。
- **自动检测 Godot 版本** — 读取 `project.godot` 以检测 Godot 版本（支持 1.x 至 4.x）。

### CLI 命令

- `gdpm init` — 初始化一个新的 gdpm 项目
- `gdpm add <插件>` — 向项目中添加插件
- `gdpm remove <插件>` — 移除插件
- `gdpm sync` — 将 addons/ 同步到锁定文件状态
- `gdpm lock` — 生成或更新锁定文件
- `gdpm list` — 列出已安装的插件
- `gdpm status` — 显示插件状态及可用更新
- `gdpm search <查询>` — 搜索 Godot 资源商店
- `gdpm info <插件>` — 显示插件详情
- `gdpm update` — 更新插件至新版本

### 改进

- 安装插件时显示带下载速度的进度条。
- 美观的 CLI 帮助界面，采用丰富的格式。
- 短选项 `-V`（版本）和 `-h`（帮助）。
- 支持版本标签（dev、beta、alpha、rc、stable）。
- 兼容 PyPI 的版本格式。

### 基础设施

- GitHub Actions CI，包含 mypy、ruff 及格式检查。
- 多平台构建工作流（Linux、macOS arm64/x64、Windows）。
- 通过可信发布者发布至 PyPI。
- 代码质量工具：mypy、ruff、vulture、deptry、pre-commit。