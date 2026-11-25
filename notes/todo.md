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
- [x] [测试覆盖度提升](done/测试覆盖度提升.md) — 总覆盖 43% → 58%（291 例）；version/zip/path/platform/manager/add 补测 + zip-slip 修复 + coverage gate 45%
- [x] [引擎查找与创建命令修复](done/引擎查找与创建命令修复.md) — find_engine_binary 三平台统一 + create 平台查找/版本排序/匹配修复

## 发布前应修（P1/P2）

- [ ] [引擎下载哈希校验](todo/引擎下载哈希校验.md) — **P0-1 已修复 ✅**（发版说明 4 处虚假声明已移除，改为中英导语披露"alpha2 提供"）；P1 = worker 下发 `x-gdpm-sha256` header（**设计已定**，注入点 `relayResponse`、复用 `fetchRelease` 缓存、零额外往返，**满足 P0-2 的"同源哈希"重接入条件**），P2 = 客户端比对。⚠️ 非"恢复"：旧实现是死代码且经 **P0-2（2026-11-07）决策主动移除**。**待拍板 4 项见详情页**
- [ ] [质量与安全加固](todo/质量与安全加固.md) — 剩余：3 个低覆盖文件、错误处理规范化、依赖解析器（`verify=False` 已闭环 ✅）（P0 主体见 [done/安全加固P0闭环](done/安全加固P0闭环.md)）

## 待开发

- [ ] [API 查询并发化](todo/API查询并发化.md) — lock/status/update 串行查询改 gather（目标 10 依赖 lock <3s）
- [ ] [远程版本列表缓存](todo/远程版本列表缓存.md) — `godot list -r` 结果缓存到 `cache/metadata/godot_versions.json`（fetched_at/body/url + 24h TTL + 离线降级）（**设计已定，待实现**）
- [ ] tests/ 纳入 mypy — 163 个未标注的测试函数参数（24 个文件），需逐个补 fixture 类型（`pytest.MonkeyPatch`、`Path` 等）；测试现由 ruff/format/pytest/pylint 覆盖
- [ ] 官方主页 — Vue + Vite 产品宣传页（动画、特性展示、安装指南）
- [ ] [其他待开发功能](todo/其他待开发功能.md)
- [ ] [Godot Asset Library 支持](todo/asset-library.md)
- [ ] 加载动画（Rich spinner，解决 console.status 与 console.print 冲突问题）
- [ ] [CI 工作流优化](todo/CI工作流优化.md) — 对比 Godot/uv 工作流 + `uvx zizmor` 实测 26 项 active（script injection、过宽权限、凭证残留、缓存投毒面）+ 发版门禁缺失 + 无超时上限；A/B/C/D 四批约 33 行 YAML，**zizmor 已定放进 `check.py`（不开独立 job）**，**明确不做项已记录**（勿重复讨论）
