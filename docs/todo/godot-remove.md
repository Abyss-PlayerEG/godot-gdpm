# gdpm godot remove - 移除本地引擎

## 目标

移除通过 `gdpm godot add` 添加的本地引擎。

## 命令设计

```bash
gdpm godot remove <name>           # 移除指定引擎
```

## 示例

```bash
gdpm godot remove steam-godot
# ✓ Removed engine 'steam-godot'
```

## 限制

- 只能移除本地引擎（`~/.gdpm/local-engines.json` 里的）
- 不能移除下载的引擎（用 `gdpm godot uninstall`）
- 如果该引擎是默认引擎，同时清除默认配置

## 实现步骤

- [ ] 实现 `gdpm godot remove <name>` 命令
- [ ] 移除引擎配置
- [ ] 如果是默认引擎，清除默认配置
