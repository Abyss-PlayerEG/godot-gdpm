# 命令参考

## 项目

| 命令 | 说明 | 选项 |
|------|------|------|
| `gdpm init [name]` | 初始化 gdpm 项目 | `--godot`、`--license`、`--as-plugin`、`--force` |
| `gdpm sync` | 同步 addons/ 到锁文件状态 | `--frozen`、`--dry-run`、`--no-cache` |
| `gdpm lock` | 生成或更新锁文件 | `--check` |
| `gdpm list` | 列出已安装插件 | `--outdated`、`--json` |
| `gdpm status` | 显示插件状态和可用更新 | `--json` |

## 依赖

| 命令 | 说明 | 选项 |
|------|------|------|
| `gdpm add <plugin>` | 添加插件 | `--dev` |
| `gdpm remove <plugin>` | 移除插件 | `-r, --recursive` |
| `gdpm update` | 更新插件 | `--latest`、`--dry-run` |
| `gdpm search <query>` | 搜索 Godot Asset Store | `-n, --limit`、`--sort`、`--all`、`--json` |
| `gdpm info <plugin>` | 查看插件详情 | — |

## 通用选项

| 选项 | 说明 |
|------|------|
| `-V` | 显示版本 |
| `-h` | 显示帮助 |
