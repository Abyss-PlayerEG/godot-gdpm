# 命令参考

## 项目

| 命令 | 说明 | 选项 |
|------|------|------|
| `gdpm init` | 初始化 gdpm 项目（自动检测设置） | — |
| `gdpm create [name]` | 创建新 Godot 项目（交互式） | `-o, --open`、`-y, --yes` |
| `gdpm sync` | 同步 addons/ 到锁文件状态 | `--frozen`、`--dry-run`（`--check`）、`--no-cache` |
| `gdpm lock` | 生成或更新锁文件 | `--check` |
| `gdpm list` | 列出已安装插件 | `--json` |
| `gdpm status` | 显示插件状态和可用更新 | `--json` |

## 依赖

| 命令 | 说明 | 选项 |
|------|------|------|
| `gdpm add <plugin>` | 添加插件 | `--dev`、`--local` |
| `gdpm remove <plugin>` | 移除插件 | `-r, --recursive` |
| `gdpm update` | 更新插件 | `--latest`、`--dry-run`（`--check`） |
| `gdpm search <query>` | 搜索 Godot Asset Store | `-n, --limit`、`--sort`、`--all`、`--json` |
| `gdpm info <plugin>` | 查看插件详情 | — |
| `gdpm cache info` | 显示缓存大小和位置 | — |
| `gdpm cache clean` | 清理所有缓存文件 | `-y, --yes` |
| `gdpm export` | 导出插件为 zip 归档 | `-o, --output` |
| `gdpm import` | 从 zip 归档导入插件 | — |

## 引擎

| 命令 | 说明 | 选项 |
|------|------|------|
| `gdpm godot list` | 列出已安装的 Godot 引擎 | `-V, --version`、`-a, --all`、`-id` |
| `gdpm godot list -r` | 列出 GitHub 上可用的版本 | `-p, --page`、`-a, --all` |
| `gdpm godot install <ver>` | 安装 Godot 引擎 | `--csharp` |
| `gdpm godot uninstall <ver>` | 卸载 Godot 引擎 | — |
| `gdpm godot add <path>` | 添加本地 Godot 引擎 | `-n, --name` |
| `gdpm godot remove <name>` | 移除本地引擎 | — |
| `gdpm godot use <id>` | 设置项目引擎 | — |
| `gdpm godot info` | 显示当前引擎信息 | — |
| `gdpm godot open` | 打开 Godot 编辑器 | `--run`、`--path` |
| `gdpm godot default <id>` | 设置默认引擎 | `--unset` |

## 配置

| 命令 | 说明 | 选项 |
|------|------|------|
| `gdpm config set <key> <value>` | 设置全局配置键 | `parallel_downloads`、`default_engine`、`cache_dir`、`language` |
| `gdpm config open` | 打开全局配置所在目录 | — |

## 通用选项

| 选项 | 说明 |
|------|------|
| `-y, --yes` | 跳过所有确认提示 |
| `-V, --version` | 显示版本 |
| `-h, --help` | 显示帮助 |
| `-a, --about` | 显示关于横幅（版本、仓库、贡献者） |
| `--completion <zsh\|bash\|fish>` | 生成 shell 补全脚本 |
