# gdpm create - 创建新 Godot 项目

## 目标

通过交互式 CLI 创建新的 Godot 项目，类似 `pnpm create vite`。

## 命令设计

```bash
gdpm create                  # 交互式创建（当前目录）
gdpm create my-game          # 指定项目名
gdpm create my-game --open   # 创建后打开 Godot
gdpm create my-game -y       # 使用默认值，跳过交互
```

## 交互流程

```
$ gdpm create

  Project name: my-game
  Godot version (default: 4.7): 

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
4. 创建 addons/
5. gdpm init（生成 gdproject.toml）
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

由 `gdpm init` 自动生成。

## 版本检测

1. 检查 `~/.gdpm/engines/` 已安装版本
2. 检查 `~/.gdpm/local-engines.json` 本地版本
3. 默认使用最新稳定版（4.x > 3.x）
4. 用户可手动输入版本

## 与 gdpm init 的区别

| | `gdpm init` | `gdpm create` |
|--|-------------|---------------|
| 目录 | 已有目录 | 自动创建 |
| project.godot | 必须存在 | 自动生成 |
| 交互式 | 无 | 有 |
| 打开 Godot | 不支持 | `--open` 支持 |

## 实现步骤

- [ ] 创建 `cli/create.py`
- [ ] 交互式收集信息（click.prompt）
- [ ] 检测已安装 Godot 版本
- [ ] 生成 project.godot
- [ ] 创建 addons/
- [ ] 调用 init 逻辑生成 gdproject.toml
- [ ] `--open` 后台打开 Godot
- [ ] `-y` 跳过交互
- [ ] 注册到 app.py
