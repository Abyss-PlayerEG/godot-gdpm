# CI/CD 工作流优化

> 来源：与 [Godot 官方仓库](https://github.com/godotengine/godot) 和 [uv](https://github.com/astral-sh/uv)
> 的 GitHub 工作流对比，外加本地跑 `uvx zizmor .github/workflows/` 的实测告警。
> 优先级：A = 安全（实测 high/medium，零结构风险）、B = 健壮性（两个参照系共同印证的缺口）、
> C = 持续防护、D = 可选深化。
>
> 验收命令：`uvx zizmor --min-severity=low .github/workflows/`（**exit 0 / No findings**）
>
> **进度（2026-11-25）**：A1–A5、B1、B2、C1、C2 已完成并本地验证 —— zizmor 由
> **36 项（21 high / 4 medium）** 降至 **0 项 low+**（余 1 info = A6 未做的 `superfluous-actions`），
> `python3 scripts/check.py` 8 项全绿。**B1 已完成 CI 彩排双路径验收**（见下表）。
> **待办：A6（可选）、C-b（C-a 的替代）、2 个可选升级、D 批。**

## 批次 A —— 安全修复（zizmor 实测，约 13 行）

- [x] **A1 script injection** — `build.yml:102` 的 `TAG="${{ github.event.release.tag_name }}"`
      是内联插值进 shell 脚本。改 env 间接：`env: TAG_NAME: ${{ github.event.release.tag_name }}`
      → 脚本内用 `"$TAG_NAME"`。值只进环境变量、永不进脚本源码。
      git ref 允许 `;` `$` 反引号；单人仓库实际风险≈0，但成本仅 3 行。
      （zizmor: `template-injection` error/high，有 autofix）

- [x] **A2 权限下沉** — `build.yml:14-15` 的 workflow 级 `contents: write` 让
      `build`/`checksums` 也拿到写权限，而只有 `upload` 挂附件需要。
      删 workflow 级，在 `upload:` 下单独声明。效果：写权限 job 数 3 → 1。
      （zizmor: `excessive-permissions` error/high）

- [x] **A3 凭证残留** — 三处 checkout 补 `persist-credentials: false`：
      `build.yml:53`、`ci.yml:29`、`publish.yml:25`。
      CI 会执行仓库代码（pytest 291 例），token 不应留在 `.git/config`。
      （zizmor: `artipacked` ×3 warning，有 autofix）

- [x] **A4 显式只读权限** — `ci.yml` 无 `permissions` 块（仓库默认已是 `read`，
      实测 `actions/permissions/workflow` = `read`），补 `permissions: { contents: read }`
      以自证最小权限并消掉告警。`build.yml:22` 同理。
      （zizmor: `excessive-permissions` warning）

- [x] **A5 缓存只读** — 发版触发的工作流不应回写缓存，否则可能成为投毒源：
      `build.yml:64`、`publish.yml:36` 的 `actions/cache` 加 `lookup-only: true`
      （CI 填、发版只读，方向单一）。（zizmor: `cache-poisoning` ×2 error，有 autofix）

- [ ] **A6（可选）消掉社区 action** — `build.yml:160` 的
      `softprops/action-gh-release@v2` 改用 runner 自带 `gh release upload`
      （注意配合 A1 的 env 写法传 tag）。
      （zizmor: `superfluous-actions` info）

## 批次 B —— 健壮性（约 12 行）

- [x] **B1 发版门禁** — `build.yml` 加 `gate` job 跑 `python3 scripts/check.py`，
      `build: needs: gate`。
      **现状缺口**：`build.yml` 与 `publish.yml` 独立触发互不依赖 → 门禁失败时
      PyPI 空着、Release 却挂着可下载二进制（半成品交付）。
      Godot 有 `static-checks` 阶段、uv 有 `release-gate` —— 两个参照系都有，唯独这里没有。

- [x] **B2 超时上限** — `ci.yml` 的 `test` job 补 `timeout-minutes: 10`、
      `publish.yml` 补 `timeout-minutes: 15`（正常 40s/1min，余量充足）。
      **现状**：无超时 → 挂死吃 GitHub **6 小时硬上限**。
      （`build.yml` 已在 `dc4988d` 加了 30 分钟）

## 批次 C —— 持续防护（**必须在 A 之后**）

### C1 接入方式（**已定：放进 `check.py`，不开独立 job**）

> 2026-11-25 决策。对比过"独立 job"与"放进 check.py"两种放置方式，选后者：
> **本地提交前自动覆盖**（AGENTS.md 要求提交前 `check.py` 全绿）+
> **本地/CI 同一条命令零漂移** + **与现有 7 项完全同构**（都是 `check.py <name>` 步骤）。
> 代价：墙钟 40s → 53s（独立 job 并行是 0 增长）——13 秒换"push 之前就发现"，划算。
> 已知取舍：PR 上的 check 名会是 `test (3.14)`（与其余 7 项一致），zizmor 挂了需点进
> run 页面看步骤名 `zizmor (workflow security)`——这是保持同构的固有代价，接受。

**版本锁定（已定：`uv add --group dev zizmor` → `uv run zizmor`）**

不用 `uvx zizmor`——它不锁版本，zizmor 出个 breaking change 你代码没动 CI 就红。
加进 dev 依赖组后版本锁在 `uv.lock`，与其余 7 项的 `uv run <tool>` 调用方式**完全一致**。
（若不想动 lockfile，备选 `uvx zizmor@<固定版本>`，但要手动跟版本。）

**改动清单**：

- [x] `uv add --group dev zizmor`
- [x] `scripts/check.py` 的 `CHECKS` 表加 2 行：
      `"zizmor": lambda: _run("zizmor (workflow security)", ["uv", "run", "zizmor", ".github/workflows/"])`
      （顺带更新文件顶部 docstring 的命令列表）
- [x] `.github/workflows/ci.yml` 加 1 步：`python3 scripts/check.py zizmor`
- [x] 验证 `deptry`/`vulture` 不会因新增 dev 依赖而报错（若报，需加豁免配置）

### C2 `unpinned-uses` 17 项 —— **接入前必须二选一**

现在跑会直接红（26 项 active）；A 批做完后仍剩 17 项 `@v4` 未锁 SHA，不处理则 check.py 永久红：

- [x] **C-a（推荐）**：加 `.github/zizmor.yml` 忽略/降级 `unpinned-uses`，其余全开
      —— 拿到 A1–A5 的自动防护，放弃 SHA 锁定这一项
- [ ] **C-b（彻底）**：SHA 锁定全部 17 处 + 装 Renovate 自动更新
      —— 不装 Renovate 则 action 会陈旧、错过安全更新，反而更危险

### 可选升级（初版不做）

- [ ] SARIF 上传到 GitHub Security 标签页（`security-events: write` + `github/codeql-action/upload-sarif`，uv 的做法）——告警可跟踪而非一次性日志
- [ ] 加入分支保护必检 —— 先观察误报率，确认无误报再加（否则 zizmor 误报会卡死 PR）

## 批次 D —— 可选深化

- [ ] **D1** `pypa/gh-action-pypi-publish@release/v1` → `uv publish dist/*`
      —— 该引用是**分支**（最易变形式），改后消掉最易变引用 + 少一个第三方 +
      dogfooding（契合"类似 uv"的定位）。`id-token: write` 已具备，需实测 trusted publishing
- [ ] **D2** SHA 锁定 17 处（**须配 Renovate**，见 C-b）
- [ ] **D3** 三工作流的 setup 六步抽 composite action（消 12 行重复；仅 3 个工作流，收益中等）
- [ ] **D4** 分支保护 check 名解耦 —— 现 `test (3.14)` 写死在保护规则里，
      改矩阵 → check 名变 → **PR 静默卡死**直到手改保护

## 明确不做（已论证，勿重复讨论）

- ❌ 按平台拆多个工作流（Godot 模式）—— 有聚合 job `checksums`/`upload` 依赖全部 4 腿，且构建仅 60–90s
- ❌ 50 文件拆分 / `plan` flag 编排 / 自托管 runner / AI 诊断（uv 模式）—— 规模不匹配
- ❌ `changed-files` 跳过检查 —— 40 秒的 CI 不值得引第三方 action（供应链信任面）
- ❌ 给 `build.yml` 加 `concurrency: cancel-in-progress` —— 会取消进行中的发版构建，导致附件挂一半
- ❌ 并行拆分 7 项检查 —— 省 14s 但 runner 分钟 ×3、要改分支保护；实测 7 项仅 26s
  （`pylint` 12s + `test` 10s 占 97%），收益不抵成本

## 执行顺序与验收

⚠️ **顺序不可换**：C1（接入 check.py）一旦完成，`check.py` 不绿就提交不了
（AGENTS.md 硬约束）——所以必须 A → C2 → C1，否则本地提交流程当场卡死。

| 批次 | 改动量 | 验收 |
|---|---|---|
| A | ~13 行 YAML | ✅ **已验收**：36 项（21 high / 4 medium）→ 0 项 low+；回归测试回退 A1 → `exit=1` + `template-injection` |
| B | ~14 行 YAML | ✅ **已验收（2026-11-25）**：彩排 run `45584037084` → `gate: success` + 4 腿全绿 + `upload: skipped`；
  探针分支（故意 F401）run `45584676889` → `gate: failure` + **`build: skipped`** + checksums/upload skipped + run=failure |
| C2 | 5 行配置 | ✅ **已验收**：`unpinned-uses` 17 项 high 归零，规则仍活跃（`ref-pin` 策略而非 disable） |
| C1 | 2 行 Python + 1 行 YAML + 1 个依赖 | ✅ **已验收**：8 项全绿含 `zizmor`；CI run `45583628408` 步骤 `Run zizmor: success`；回归测试通过 |
| D | 按需 | 各自独立提交 |
