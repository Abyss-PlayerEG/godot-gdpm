# Godot 引擎版本管理

## 目标

管理每个项目使用的 Godot 版本，类似 pyenv 管理 Python 版本。

## 命令设计

```bash
gdpm godot list           # 列出已安装版本
gdpm godot list-remote    # 列出可用版本（GitHub API）
gdpm godot install 4.7    # 安装指定版本
gdpm godot uninstall 4.3  # 卸载指定版本
gdpm godot use 4.7        # 设置项目版本
gdpm godot run            # 运行项目对应的 Godot
gdpm godot info           # 显示当前版本信息
```

## 存储结构

```
~/.gdpm/
├── engines/
│   ├── 4.3.0/
│   │   └── Godot_v4.3-stable_macos.universal
│   ├── 4.7.0/
│   │   └── Godot_v4.7-stable_macos.universal
│   └── 4.7.0-rc1/
│       └── Godot_v4.7-rc1_macos.universal
└── config.toml

项目/
├── gdproject.toml
├── gdpm.lock
└── .gdpm-godot            # 4.3.0
```

## 实现步骤

### 第一阶段：核心功能

- [ ] `gdpm godot list` 列出已安装版本
- [ ] `gdpm godot install 4.7` 安装指定版本
- [ ] `gdpm godot use 4.7` 设置项目版本
- [ ] `gdpm godot run` 运行项目 Godot

### 第二阶段：扩展功能

- [ ] `gdpm godot list-remote` 列出可用版本
- [ ] `gdpm godot uninstall 4.3` 卸载指定版本
- [ ] `gdpm godot info` 显示当前版本信息

### 第三阶段：高级功能

- [ ] 支持 --pre（预发布版本）
- [ ] 自动下载缺失版本
- [ ] 版本约束匹配（">=4.2"）
- [ ] Steam 版 Godot 检测

## 下载源

```
https://github.com/godotengine/godot/releases/download/{tag}/Godot_v{version}_{platform}.{ext}

示例:
https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_macos.universal.zip
https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_linux.x86_64.zip
https://github.com/godotengine/godot/releases/download/4.3-stable/Godot_v4.3-stable_win64.exe.zip
```

## 平台检测

macOS:
- `/Applications/Godot.app/Contents/MacOS/Godot`
- Steam: `~/Library/Application Support/Steam/steamapps/common/Godot Engine/Godot.app/Contents/MacOS/Godot`

Linux:
- `which godot`
- `/usr/local/bin/godot`

Windows:
- `where godot.exe`
- `%LOCALAPPDATA%\Godot\`
