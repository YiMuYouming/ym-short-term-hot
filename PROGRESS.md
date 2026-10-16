# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 18:31（Asia/Shanghai）；状态依据：谷米完成 `SH-03` 第一次终审（`AUDIT-SH03-20261016-R1`），4 条架构门禁红线与主体双视图/抽屉全部通过，抓出 2 个 P1 数据映射与 URL 寻址缺陷（[`audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md)），退回稳米小幅修补后收官结项

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-03 开工单](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) · [SH-03 审计报告（待修补 2 项 P1）](docs/evidence/sh03-20261016/audit-by-gumi.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：第一期（Phase 1）拆分为三个顺序审计阶段（`SH-01` → `SH-02` → `SH-03`）；`SH-01` 与 `SH-02` 均已通过审计结项（`done`）；**`SH-03` 主体已由稳米交付（`387686a`），经谷米第一次终审发现 2 个 P1 缺陷（状态：`rework_required`，约 25 行代码可修完）**，修完二次复审通过即宣告第一期圆满收官。
- **已完成范围**：
  1. `SH-01`（基座与短线 KnowHow）与 `SH-02`（`bridge/` 焦点股池、三社区采集与四轨契约）均已结项；
  2. `SH-03` 主体模块 `modules/short-term-radar/` 已落地并通过 4 条架构门禁红线、`npm run typecheck`、`npm run build -w @aihot/web` 与 API/SSR 测试。
- **尚未完成**：`SH-03` 的 2 项 P1 缺陷修补与二次终审（详见 [`docs/evidence/sh03-20261016/audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md)）。
- **下一步唯一任务**：**稳米**按 [`docs/evidence/sh03-20261016/audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md) 定点修补 `contracts.ts`（第 31~50 名梯队股补齐 `roleLabel`/`themes`/`exchange`）与 `radar-route.tsx`（响应 URL `?q=` 与 `?theme=` 寻址过滤并消除 `radar-page.test.ts` 假阳性断言），提交后交谷米二次终审结项。

## 有效边界与决定

- **协作模式（2026-10-16 弈沐拍板）**：**谷米**负责规划、写开工单与阶段审查；**稳米**负责按单实施。**完成一个阶段、审计一个阶段**，未获上一阶段审计通过前不跨阶段施工。
- **独立工程边界（2026-10-16 弈沐拍板）**：作为 `YM_Capital` 下的独立项目建设，不与 `live-dashboard`（8088）混用代码、数据库或端口；本站默认端口为 `3088`。
- **数据源与第一批社区范围（2026-10-16 弈沐拍板）**：
  - 结构化热榜（同花顺 `ths_hot`、东财 `dc_hot`）、涨跌停池 (`market_intraday_state`)、开盘啦题材 (`kpl_list`/`kpl_concept`)、同花顺涨停原因 (`limit_list_ths`) 已在 `SH-02` 通过 `/Users/yimu/Projects/YM_Capital/YM-data-pipeline` 公共入口打通；
  - 第一批社区评论范围固定为：**① 东方财富股吧**、**② 淘股吧 TGB**、**③ 雪球**。
- **产品视图与架构红线（2026-10-16 弈沐拍板 + 谷米预审）**：
  - 在 `SH-03` 通过 `modules/short-term-radar/` 实现双视图切换：默认 **「🧩 题材主线梯队视图」**，一键切换 **「🔥 跨平台人气共振 Top 30 榜」** + 个股社区舆情侧滑抽屉；
  - `modules/short-term-radar/web/**` 严禁引用 `@aihot/backend`（遵守 `tests/architecture.test.ts` HTTP 边界），`server.ts` 统一通过 `config.dataDir` 读取 `.data/short-term-radar-snapshot.json`。

## 未完成队列

| ID | 状态 | 下一动作 / 退出条件 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `done` | **【已通过谷米审计】基座环境与 A 股短线 KnowHow 改造**：`site/`、`industry/` 与 39 个测试文件适配完成。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [谷米审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) |
| `SH-02` | `done` | **【已通过谷米二次复审】`YM-data-pipeline` 桥接与三大社区靶向采集 (`bridge/`)**：56 项 Python 单测 + 四轨跨语言入库契约（41/41 入库，`backfill=0`）全部绿灯。 | [SH-02 开工单](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) · [谷米复审报告](docs/evidence/sh02-20261016/audit-by-gumi.md) |
| `SH-03` | `rework_submitted` | **【R1 返工已提交，待谷米二次终审】`@aihot/short-term-radar` 双视图模块 (`modules/short-term-radar/`)**：两项 P1 已定点修复——① `contracts.ts` 的 `mapSnapshot()` 给梯队里未进 Top 30 的 20 只股票补上身位、题材与交易所（矛盾条目 27 → 0，`/stock/601127.SH` 恢复 200）；② `radar-route.tsx` 的直链过滤打通，`?q=`/`?theme=` 由 loader 透传给 API 做服务端过滤，并补负向断言消除假阳性。门禁：typecheck exit 0、web build exit 0、模块单测 5/5、架构红线 8/8、页面 SSR 2/2。 | [R1 审计](docs/evidence/sh03-20261016/audit-by-gumi.md) · [返工记录](docs/evidence/sh03-20261016/verification.md) |
| `SH-04` | `backlog` | **二期扩展**：接入韭研公社题材逻辑帖、用 `.data/gold.jsonl`（70 条已就位）跑 `eval-selection.ts` 校准门槛、联动游资与量化龙虎榜席位 (`hm_detail`) 与互动易 (`irm_qa`)。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 18:31 CST | `SH-03` 第一次终审（退回小幅修补） | 谷米**
  - **结果**：审查稳米提交 `387686a`。4 条架构门禁红线、`typecheck`、`web build` 及模块主体质量优秀，但独立对账抓出 2 个 P1 缺陷：① `contracts.ts` 的 `mapSnapshot()` 对未进 Top 30 的 20 只梯队股 fallback 时漏填 `roleLabel: role`、`themes` 与 `exchange`，导致 6 个题材梯队（如华为/鸿蒙的赛力斯、苹果链的立讯精密、储能的阳光电源等）出现“抬头摘要写容量中军 1 只、下方卡片却标为人气热股”的自相矛盾，且按 `?theme=消费电子` 过滤会丢失股票、按 `601127.SH` 查单股会 404；② `radar-route.tsx` 未从 `useSearchParams()` 读取 `?q=` 与 `?theme=`，导致 `/radar?q=易中天` 实际未过滤（`radar-page.test.ts` 因搜索框 placeholder 含“易中天”产生假阳性通过）。
  - **下一步**：出具 [`docs/evidence/sh03-20261016/audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md)，交稳米定点修补后二次复审收官。

- **2026-10-16 18:24 CST | `SH-03` 实施交付 | 稳米**
  - **结果**：提交 `387686a`，新增 `modules/short-term-radar/` 并完成双视图、舆情抽屉、四条路由与 Agent/MCP 能力。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / `SH-02` 结项 | [`docs/evidence/sh02-20261016/`](docs/evidence/sh02-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) | 完成 `bridge/` 焦点股池、三社区采集、System 1 情绪引擎及四轨跨语言契约对齐，谷米二次复审通过。 |
| 2026-10-16 / `SH-01` 结项 | [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) | 完成 AIHOT 站点与 A 股短线 6 大分类/提示词/测试适配，谷米独立复测通过。 |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |

- **2026-10-16 19:25 CST | `SH-03` R1 返工提交 | 稳米**
  - **结果**：定点修复 R1 的 2 个 P1。**P1-1**（`contracts.ts` `mapSnapshot()`）：梯队覆盖 50 只焦点股而共振榜只有 30 只，第 31~50 名走 fallback 时丢了 `roleLabel`/`themes`/`exchange`；改为先汇总 `themesByCode`，再补桶的身位、合并题材、从 `symbol` 前缀推断交易所。**P1-2**（`radar-route.tsx`）：`query` 改为派生自 `?q=` 并与输入框双向同步，新增 `?theme=` 对梯队与共振榜同时生效；更关键的是 **loader 把 `q`/`theme`/`role` 透传给 API**——React Router 会把 loader 数据内联进 HTML，只在组件里过滤等于把未过滤数据发给浏览器，负向断言无法成立。
  - **回归锁**：`radar.test.ts` 新增梯队一致性断言（题材归属、带后缀 code、摘要与身位一致，矛盾条目 **27 → 0**）；`radar-page.test.ts` 补 `!nickname.includes("宁德时代")` 与 `?theme=` 正负向断言。
  - **验证范围**：typecheck exit 0；`npm run build -w @aihot/web` exit 0；模块单测 5/5；架构红线 8/8（四条逐条）；页面 SSR 2/2；一次性实测 `/stock/601127.SH` 返回 200（赛力斯·容量中军）、`?q=易中天` 页不再含宁德时代。
  - **下一步**：交谷米二次终审收官。
