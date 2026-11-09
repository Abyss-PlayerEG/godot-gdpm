# API 查询并发化

> 来源：2026-11-07 性能实测（本机数据）。**状态：已入计划。**
> 目标：`lock` / `status` / `update` 的 Store API 查询从串行改为并发，消除秒级线性等待。

## 一、实测数据

| 场景 | 耗时 | 说明 |
|------|------|------|
| 单次查询（含 TLS 握手） | ~1.5s | 首次连接 |
| 单次查询（连接已建立） | **~1.0s** | **服务端延迟是硬底** |
| 5 次查询串行（连接复用） | 4.8s | N 个依赖 = N × ~1s |
| 5 次查询并发（连接复用） | **2.2s** | ≈2.2× 提速 |

## 二、问题定位（已核实代码）

**串行等待是唯一缺口，连接复用已经存在**：

- ✅ `StoreClient` 持有单例 `httpx.AsyncClient`（`client.py:65`），命令内所有请求复用连接——无需再做连接池
- ❌ `lock.py:58-78`：`for name, dep in ...` 循环内逐个 `await resolve_publisher(...)` / `await store.get_versions(...)`
- ❌ `status.py:106`、`update.py:95`：同样是 `for` 循环内 `await get_versions(...)`

**影响面**：

```
gdpm lock   (10 个依赖) ≈ 10~15s   ← 最痛, 每个依赖一次查询
gdpm status (N 个插件)  ≈ N × 1s
gdpm update (N 个目标)  ≈ N × 1s
gdpm search 单次        ≈ 1.3s     ← 服务端延迟, 并发也救不了单次
```

## 三、修复方案

复用 `sync.py` 已验证的模式（`asyncio.Semaphore` + `gather`）：

### Phase 1: lock 并发化（收益最大）

- [ ] 拆解单依赖的两段式查询：`resolve_publisher`（必要时）→ `get_versions`
- [ ] 每个依赖一个协程（内部两段仍顺序，协程之间并发），`gather` 收结果
- [ ] `Semaphore(3~5)` 限流——查询类请求不宜打满，避免触发官方 API 防护
- [ ] 保持现有行为：单依赖失败不拖垮整体（`return_exceptions=True` 或 try/except 收集错误）

### Phase 2: status / update 并发化

- [ ] `status.py` 的 `get_versions` 循环改 gather
- [ ] `update.py` 的 `get_versions` 循环改 gather

### Phase 3: 韧性

- [ ] 查询超时与重试策略统一（当前各处 timeout 不一）
- [ ] 速率异常（429/限流）时降级回串行或退避，而非整体报错

### Phase 4: 验收

- [ ] 实测：10 依赖 `gdpm lock` 从 ~13s 降到 **<3s**
- [ ] 实测：`gdpm status`（5 插件）耗时对比记录
- [ ] 单测：mock StoreClient，断言查询确实并发（如并发计数峰值 >1）且结果顺序与输入一致
- [ ] `python3 scripts/check.py` 全绿

## 四、不在本期范围

- 服务端 ~1s/查询延迟本身——官方 API 性能，客户端只能并发掩盖
- `gdpm search` 单次延迟——同样受限于服务端
- 查询结果缓存（如 get_versions 短期缓存）——留作后续优化候选
- 下载并发/分片——已有独立计划（[下载优化](下载优化.md)）
