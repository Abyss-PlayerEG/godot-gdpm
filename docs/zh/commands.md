# 命令参考

## 项目

| 命令 | 说明 |
|------|------|
| `gdpm init` | 初始化 gdpm 项目 |
| `gdpm create [name]` | 创建新 Godot 项目（交互式） |
| `gdpm sync` | 同步 addons/ 到锁文件状态 |
| `gdpm lock` | 生成或更新锁文件 |
| `gdpm list` | 列出已安装插件 |
| `gdpm status` | 显示插件状态和可用更新 |

## 依赖

| 命令 | 说明 |
|------|------|
| `gdpm add <plugin>` | 添加插件 |
| `gdpm add --local` | 打包本地插件到 gdpm-local/ |
| `gdpm remove <plugin>` | 移除插件 |
| `gdpm update` | 更新插件 |
| `gdpm search <query>` | 搜索 Godot Asset Store |
| `gdpm info <plugin>` | 查看插件详情 |

## 引擎管理

| 命令 | 说明 |
|------|------|
| `gdpm godot list` | 列出已安装的 Godot 引擎 |
| `gdpm godot list -r` | 列出 GitHub 上可用的版本 |
| `gdpm godot install <ver>` | 安装 Godot 引擎 |
| `gdpm godot uninstall <ver>` | 卸载 Godot 引擎 |
| `gdpm godot add <path>` | 添加本地 Godot 引擎 |
| `gdpm godot remove <name>` | 移除本地引擎 |
| `gdpm godot use <id>` | 设置项目引擎 |
| `gdpm godot info` | 显示当前引擎信息 |
| `gdpm godot open` | 打开 Godot 编辑器 |
| `gdpm godot default <id>` | 设置默认引擎 |

## 缓存

| 命令 | 说明 |
|------|------|
| `gdpm cache info` | 显示缓存大小和位置 |
| `gdpm cache clean` | 清理所有缓存文件 |

## 导入/导出

| 命令 | 说明 |
|------|------|
| `gdpm export` | 导出插件为 zip 归档 |
| `gdpm import` | 从 zip 归档导入插件 |

## 全局选项

| 选项 | 说明 |
|------|------|
| `-y, --yes` | 跳过所有确认提示 |
| `-V` | 显示版本 |
| `-h` | 显示帮助 |
| `-i` | 显示详细信息 |
