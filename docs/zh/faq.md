# 常见问题

## gdpm 和手动下载 addon 有什么区别？

- 一条命令代替浏览 Asset Store
- 自动依赖解析
- 锁文件确保团队安装一致
- 版本约束（`^`、`~`、`>=`）

## GDPM 需要自定义注册表吗？

不需要。GDPM 直接使用官方的 [Godot Asset Store API](https://store.godotengine.org/api/v1)。

## 插件追踪是怎么工作的？

GDPM 在每个 addon 目录中写入 `tag.gdpm` 文件来追踪归属：

```
addons/
  cogito/
    tag.gdpm    → store+philip-drobar/cogito
    plugin.cfg
  input_helper/
    tag.gdpm    → store+niceg/input_helper
```

## 支持 Godot 3.x 吗？

支持。GDPM 同时支持 Godot 3.x 和 4.x。版本检测会自动读取 `project.godot`。

## 缓存存储在哪里？

全局缓存在 `~/.gdpm/cache/`。使用 `gdpm cache info` 查看大小和位置。
