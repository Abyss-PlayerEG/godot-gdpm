# CLI 目录结构重构（commands/ + base.py）

> 来源：2026-11-07 方案讨论定稿（L1）。**状态：Phase 1-4 已实施完成，验收通过，待验收提交。**

## 一、背景与动机（现状体检，数据实测）

| 问题 | 实测数据 |
|------|---------|
| 平铺过载 | `cli/` 顶层 23 个条目：14 个根命令文件 + 2 个命令组包 + 7 个基础设施，命令与基础设施混居难辨 |
| 命令反向依赖入口 | **25 处** `from gdpm.cli.app import ...`——23 个命令 import 入口，入口再"晚导入"命令，靠导入顺序技巧压制循环依赖 |
| 组织不一致 | godot/config 是包、14 个根命令平铺；`cache_cmd`/`import_cmd` 后缀不统一（`import` 被关键字逼迫，`cache` 不是） |
| 入口职责混杂 | app.py 三类职责：命令基类 + 全局回调（print_*） + main/挂载 |

## 二、决策记录（已讨论定案）

| 决策点 | 结论 |
|--------|------|
| 方案 | **L1：`commands/` 收拢全部命令 + `base.py` 拆出命令基类**（npm `lib/commands/` 同款布局） |
| 否决 L2（再收 `core/`） | 更整洁（顶层 3 条目），但 console/context/display 等 import 全要改（+50 行），收益/成本比 L1 低，留作后续可选 |
| 否决 L0（只拆 base） | 解决反向依赖但 23 项平铺照旧，治不了"乱" |
| 否决分类分包（project/、deps/） | 文件位置会与 `category=` 成为双份事实源，移动命令必须同步改分类，埋漂移坑 |
| 顺手统一命名 | `cache_cmd.py` → `cache.py`（消掉非必要 `_cmd` 后缀）；`import_cmd.py` 因 `import` 关键字必须保留 |
| 入口三点不动 | pyproject `gdpm = "gdpm.cli.app:main"`、`__main__.py`、`cli/__init__.py` 全部不变 |

## 三、目标结构

```
src/gdpm/cli/
├── __init__.py        # 对外暴露 main (不动)
├── app.py             # 组合根: main + print_* 回调 + 挂载 (~190 行)
├── base.py            # ★新: GdpmCommand / GdpmGroup (help 委托)
├── common.py          # console + 项目根定位
├── context.py         # 项目上下文/服务装配
├── display.py         # 输出格式化 (JSON/版本/元数据)
├── help.py            # 帮助渲染器 (纯函数构建器 + Rich 渲染 + BANNER)
├── i18n.py            # 词典 + t() + 语言配置
├── options.py         # 共享选项装饰器 (yes_option)
└── commands/          # ★ 全部命令, 入口只从此挂载
    ├── __init__.py    # 空 (仅包说明)
    ├── add.py  cache.py  create.py  export.py  info.py  init.py
    ├── list.py  lock.py  remove.py  search.py  status.py  sync.py
    ├── update.py  import_cmd.py
    ├── godot/         # 原样迁入 (7 文件)
    └── config/        # 原样迁入 (2 文件)
```

顶层 23 → **10**，基础设施与命令一眼分清。

### 依赖方向修正（本质收益）

```
现在:  23 个命令 ──依赖──▶ app(入口) ──晚导入──▶ 23 个命令   ← 环
改后:  commands ──依赖──▶ base ──▶ help/i18n                ← 单向无环
       app(组合根) ──依赖──▶ commands + base
```

## 四、实施步骤（每步独立可验证）

### Phase 1: base.py 拆出（不挪文件）

- [x] 新建 `cli/base.py`：`GdpmCommand` / `GdpmGroup` 从 app.py 移出（format_help 委托 help 渲染不变）
- [x] 23 处命令文件 `from gdpm.cli.app import GdpmCommand/GdpmGroup` → `from gdpm.cli.base import ...`
- [x] app.py 改为 `from gdpm.cli.base import GdpmGroup`（main 的 cls）；print_* 与挂载留原地
- [x] `check.py` 全绿（此步文件位置不动）

### Phase 2: 根命令迁入 commands/

- [x] 新建 `cli/commands/__init__.py`（空 + 包说明）
- [x] `git mv` 14 个根命令进 `commands/`，顺手 `cache_cmd.py` → `cache.py`
- [x] app.py 底部挂载路径改 `gdpm.cli.commands.*`（16 行 import + 16 行 add_command）
- [x] 测试路径：`test_create_version` 的 `gdpm.cli.create` → `gdpm.cli.commands.create`
- [x] `check.py` 全绿 + `gdpm --help` 冒烟

### Phase 3: godot/ config/ 迁入

- [x] `git mv godot/ config/` → `commands/`
- [x] 包内互引 16 行 `gdpm.cli.godot.` → `gdpm.cli.commands.godot.`（config 同理）
- [x] app.py 挂载 2 行路径更新
- [x] 测试 8 个文件路径更新（**含 monkeypatch/patch 字符串路径**，如 `"gdpm.cli.godot.install.CHUNK_COUNT"`）
- [x] `check.py` 全绿 + 全命令冒烟

### Phase 4: 验收

- [x] 反向断言：`grep -rn "from gdpm.cli.app import" src/gdpm/cli/commands/` → 无结果（命令不再依赖入口）
- [x] 反向断言：`cli/` 顶层条目 = 10
- [x] `python3 scripts/check.py` 全绿
- [x] 冒烟：`gdpm --help` / `gdpm godot list --help` / `gdpm config set --help` / `gdpm --version`
- [x] 计划回填勾选；**全程不提交，验收后按指示提交**

## 五、改动清单（全部机械替换）

| 项 | 量 | 说明 |
|----|----|------|
| `git mv` | 16 次 | 14 根命令 + godot/ + config/（保历史） |
| 命令 import `app` → `base` | 23 行 | Phase 1 |
| godot/config 包内互引 | 16 行 | Phase 3 |
| app.py 挂载路径 | 34 行 | Phase 2/3；类移出后 app.py 250 → ~190 |
| 测试路径 | 8 文件 ~15 行 | Phase 2/3 |
| 不变 | — | common/context/display/options/help/i18n 的 import、pyproject 入口、`__main__.py`、`cli/__init__.py` |

## 六、风险与对策

| 风险 | 对策 |
|------|------|
| 测试里字符串形式的 monkeypatch 路径漏改 | Phase 3 用 grep 模式 `gdpm.cli.godot\|gdpm.cli.config` 全量扫 src+tests 后统一替换，check.py 兜底 |
| 挪文件丢历史 | 一律 `git mv`；提交时 git 自动 rename 检测 |
| 产生新循环 import | Phase 1 后命令只 import base，app 单向 import commands，环彻底消失（晚导入技巧可保留也可简化，实施时定） |
| 入口断 | 三个入口点不动 + Phase 4 入口冒烟 |

## 七、不在本期范围

- L2 `core/` 基础设施包（后续可选，另行决策）
- 按分类分包（已否决，理由见决策表）
- `print_*` 回调迁移（既有决策：留 app.py）
- `import_cmd.py` 重命名（Python 关键字限制，无法避免）

## 八、实施记录（2026-11-08）

| 项 | 结果 |
|----|------|
| Phase 1 | `base.py` 65 行；23 处 import 改向；命令 import 上移至 app 顶部（环消失的直接证明），3 处 `type: ignore[has-type]` 随之移除；app.py 250 → **198 行** |
| Phase 2 | 14 根命令迁入（`cache_cmd` → `cache`）；`git mv` 全程保历史 |
| Phase 3 | godot/ config/ 迁入；16 文件路径替换（含测试 monkeypatch 字符串路径）；`git mv config` 因 `init.py` 删除未暂存失败一次，`git add` 该删除后重试成功 |
| Phase 4 | 三项反向断言全中（commands/ 零 `import app`、顶层 10、app 仅剩 main 引用方：`cli/__init__` / `__main__` / 测试）；`check.py` 8/8 + pylint 10.00；117 测试；6 命令广度冒烟 + 中文两面冒烟通过 |
| 顺手修正 | notes 中 7 个文档的过时 `cli/godot|sync|add...` 路径批量更新至 `commands/` 下 |
| 测试计数 | 117（与实施前一致，纯结构重构不增减测试） |
