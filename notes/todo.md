# GDPM Todo

## 已完成 ✅

- [x] Phase 1-4: 核心功能（init, add, remove, sync, lock, list, search, info, update, status, export）
- [x] Phase 5: 本地插件管理（add --local, tag.gdpm, hash 检测）
- [x] Phase 6: 代码重构（公共模块提取）
- [x] [全局缓存](done/全局缓存.md)
- [x] [Godot 引擎版本管理](done/Godot引擎版本管理.md)
- [x] [gdpm create](done/gdpm-create.md)
- [x] [默认引擎配置](done/默认引擎配置.md)
- [x] [GitHub Token](done/github-token.md)
- [x] [Godot 自定义引擎](done/Godot自定义引擎.md)
- [x] [Godot 移除命令](done/godot-remove.md)
- [x] [安装类型检测](done/安装类型检测.md)

## 发布前必修 P0

- [ ] [质量与安全加固](todo/质量与安全加固.md) — TLS 关闭校验、SHA256 校验失效、zip-slip、零测试（2026-11 代码评审核实）

## 待开发

- [ ] [引擎查找与创建命令修复](todo/引擎查找与创建命令修复.md) — find_engine_binary 兼容性 + create 命令平台/逻辑 bug（P0/P1）
- [ ] [GitHub API → 官方 API 迁移](todo/官方API迁移.md) — versions.json / downloads.godotengine.org / godot-builds 三件套替换（含 P0-2 修复）
- [ ] 官方主页 — Vue + Vite 产品宣传页（动画、特性展示、安装指南）
- [ ] [下载优化](todo/下载优化.md)
- [ ] [其他待开发功能](todo/其他待开发功能.md)
- [ ] [Godot Asset Library 支持](todo/asset-library.md)
- [ ] 加载动画（Rich spinner，解决 console.status 与 console.print 冲突问题）
