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
- [x] [GitHub API → 官方 API 迁移](done/官方API迁移.md) — 最终落地为自建镜像唯一通道（versions.json + 下载中转）
- [x] [帮助系统重构与多语言](done/帮助系统重构与多语言.md) — 纯函数渲染器 + 数据驱动 + help i18n
- [x] [CLI 目录结构重构](done/cli目录结构重构.md) — `commands/` 收拢 + `base.py` 拆基类
- [x] [下载优化](done/下载优化.md) — 并行下载 + 分片下载

## 发布前必修 P0

- [ ] [质量与安全加固](todo/质量与安全加固.md) — 剩余：zip-slip 未修复、核心模型/锁文件/zip 无测试、错误处理规范化（TLS 与 SHA256 项已闭环）

## 待开发

- [ ] [引擎查找与创建命令修复](todo/引擎查找与创建命令修复.md) — 主体已完成，剩硬编码默认版本评估 + `create --open` 手动验收
- [ ] [API 查询并发化](todo/API查询并发化.md) — lock/status/update 串行查询改 gather（目标 10 依赖 lock <3s）
- [ ] [远程版本列表缓存](todo/远程版本列表缓存.md) — `godot list -r` 结果缓存到 `cache/metadata/godot_versions.json`（fetched_at/body/url + 24h TTL + 离线降级）（**设计已定，待实现**）
- [ ] 官方主页 — Vue + Vite 产品宣传页（动画、特性展示、安装指南）
- [ ] [其他待开发功能](todo/其他待开发功能.md)
- [ ] [Godot Asset Library 支持](todo/asset-library.md)
- [ ] 加载动画（Rich spinner，解决 console.status 与 console.print 冲突问题）
