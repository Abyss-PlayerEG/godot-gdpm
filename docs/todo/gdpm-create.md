# gdpm create - 创建新 Godot 项目

## 目标

通过交互式 CLI 创建新的 Godot 项目，类似 `npm init`。

## 命令设计

```bash
gdpm create                  # 交互式创建（当前目录）
gdpm create my-game          # 指定项目名
gdpm create my-game --open   # 创建后打开 Godot
```

## 交互流程

```
$ gdpm create

  Project name: my-game
  Godot version (default: 4.7): 4.7
  Description: My awesome game
  Author: playereg
  License: MIT

  ✓ Created project 'my-game'
    Godot: >=4.7.0
    Created project.godot
    Created gdproject.toml
    Created addons/
```

## 交互项

| 问题 | 默认值 | 说明 |
|------|--------|------|
| Project name | 目录名 | 项目名称 |
| Godot version | 已安装最新版 | 指定版本 |
| Description | 空 | 项目描述 |
| Author | 空 | 作者 |
| License | MIT | 许可证 |

## 参数

| 参数 | 说明 |
|------|------|
| `name` | 项目名（可选，跳过交互） |
| `--open` / `-o` | 创建后打开 Godot |
| `-y` / `--yes` | 使用默认值，跳过交互 |

## 流程

```
gdpm create my-game
  ↓
1. 交互式收集信息（或使用参数/默认值）
2. 创建目录 my-game/
3. 生成 project.godot
4. 生成 gdproject.toml
5. 创建 addons/
6. （可选）后台打开 Godot
```

## 生成文件

### project.godot

```ini
; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=5

[application]

config/name="my-game"
config/features=PackedStringArray("4.7")
```

### gdproject.toml

```toml
name = "my-game"
godot = ">=4.7.0"
description = "My awesome game"
author = "playereg"
license = "MIT"
addons_dir = "addons"
```

## 与 gdpm init 的区别

| | `gdpm init` | `gdpm create` |
|--|-------------|---------------|
| 目录 | 已有目录 | 自动创建 |
| project.godot | 必须存在 | 自动生成 |
| 交互式 | 无 | 有（类似 npm init） |
| 描述/作者/许可证 | 不收集 | 收集 |

## 实现步骤

- [ ] 实现交互式 CLI（click.prompt）
- [ ] 生成 project.godot
- [ ] 生成 gdproject.toml（含描述、作者、许可证）
- [ ] 创建 addons/
- [ ] `--open` 后台打开 Godot
- [ ] `-y` 跳过交互
