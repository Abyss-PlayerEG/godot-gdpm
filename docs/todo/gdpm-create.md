# gdpm create - 创建新 Godot 项目

## 目标

通过命令行创建新的 Godot 项目，自动生成项目文件和 gdpm 配置。

## 命令设计

```bash
gdpm create <name>              # 创建新项目
gdpm create <name> --open       # 创建后打开 Godot
gdpm create <name> --godot 4.7  # 指定 Godot 版本
```

## 示例

```bash
gdpm create my-game
# ✓ Created project 'my-game'
#   Godot: >=4.7.0
#   Created project.godot
#   Created gdproject.toml
#   Created addons/

gdpm create my-game --open
# 创建后后台启动 Godot 编辑器
```

## 流程

```
gdpm create my-game
  ↓
1. 创建目录 my-game/
2. 创建 project.godot（空文件或最小配置）
3. 创建 addons/
4. gdpm init（生成 gdproject.toml）
5. （可选）后台打开 Godot
```

## project.godot 内容

```ini
; Engine configuration file.
; It's best edited using the editor UI and not directly.

config_version=5

[application]

config/name="my-game"
config/features=PackedStringArray("4.7")
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `name` | 项目名称（目录名） | 必填 |
| `--open` / `-o` | 创建后打开 Godot | 否 |
| `--godot` / `-g` | 指定 Godot 版本 | 已安装的最新版 |

## 与 gdpm init 的区别

| | `gdpm init` | `gdpm create` |
|--|-------------|---------------|
| 目录 | 已有目录 | 自动创建 |
| project.godot | 必须存在 | 自动生成 |
| addons/ | 自动创建 | 自动创建 |
| gdproject.toml | 自动创建 | 自动创建 |
| 打开 Godot | 不支持 | `--open` 支持 |

## 实现步骤

- [ ] 实现 `gdpm create <name>` 命令
- [ ] 生成 project.godot（根据已安装 Godot 版本）
- [ ] 自动调用 gdpm init 逻辑
- [ ] `--open` 后台打开 Godot
