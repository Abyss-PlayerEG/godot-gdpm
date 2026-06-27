# gdpm godot add - 添加自定义 Godot 引擎

## 目标

添加系统中已安装的 Godot 引擎到 gdpm 管理，支持 Steam 版、手动安装版等。

## 命令设计

```bash
gdpm godot add <path>              # 添加本地 Godot 路径
gdpm godot add <path> --name 4.7   # 指定别名
```

## 示例

```bash
# 添加 Steam 版 Godot
gdpm godot add ~/Library/Application\ Support/Steam/steamapps/common/Godot\ Engine/Godot.app
# 检测: ✓ 路径存在 ✓ 是 Godot 应用 ✓ 版本: 4.7-stable
# 输入别名 (默认 4.7-stable): 4.7-steam
# ✓ Added Godot 4.7-steam

# 添加手动安装的 Godot
gdpm godot add /usr/local/bin/godot --name 4.7-custom
# ✓ Added Godot 4.7-custom
```

## 检测逻辑

| 系统 | 检查 | 获取版本 |
|------|------|---------|
| macOS | `Godot.app/Contents/MacOS/Godot` 存在 | `Godot --version` |
| Linux | 文件是 ELF 可执行 | `godot --version` |
| Windows | 文件是 .exe | `godot.exe --version` |

版本解析：`4.7.0.stable.official.h` → `4.7-stable`

## 别名规则

- 检测成功后提示输入别名
- 直接回车使用解析出的版本号作为别名
- `--name` 参数优先

## 配置文件

`~/.gdpm/local-engines.json`：

```json
{
  "4.7-steam": {
    "path": "/Users/playereg/Library/Application Support/Steam/steamapps/common/Godot Engine/Godot.app",
    "version": "4.7-stable"
  },
  "4.7-custom": {
    "path": "/usr/local/bin/godot",
    "version": "4.7-stable"
  }
}
```

## 存储结构

```
~/.gdpm/
├── local-engines.json   # 本地引擎配置
├── engines/             # 下载的引擎
│   ├── 4.7-stable/
│   └── 4.7-stable-csharp/
└── cache/               # 下载缓存
```

## gdpm godot list 整合

```bash
gdpm godot list

╭──────────────────────────── Installed Godot (3) ────────────────────────────╮
│                                                                              │
│    Name                Version           Source                               │
│  ────────────────────────────────────────────────────────────────────────    │
│    gdpm-godot          4.7-stable        ~/.gdpm/engines/4.7-stable          │
│    gdpm-godot          4.7-stable-csharp ~/.gdpm/engines/4.7-stable-csharp   │
│    4.7-steam           4.7-stable        ~/.../Godot.app                     │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

- 下载的引擎：name = `gdpm-godot`
- 本地添加的引擎：name = 用户输入的别名

## 限制

- 添加的本地引擎**不支持删除**（只能手动编辑 `local-engines.json`）
- 添加的本地引擎**不支持哈希验证**
- 路径必须存在且可执行

## 实现步骤

- [ ] 创建 `~/.gdpm/local-engines.json` 读写工具
- [ ] 实现 `gdpm godot add <path>` 命令（含检测和别名）
- [ ] 修改 `gdpm godot list` 显示本地引擎（name 字段）
- [ ] 修改 `gdpm godot use` 支持本地引擎
- [ ] 修改 `gdpm godot run` 支持本地引擎
