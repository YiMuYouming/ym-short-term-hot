# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 17:17（Asia/Shanghai）；状态依据：谷米完成 `SH-02` 第二次复审（`AUDIT-SH02-20261016-R2`）判定 **PASS 结项**，并正式签发第一期收官阶段 `SH-03` 开工单（[`docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md`](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md)）

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-02 审计结项报告](docs/evidence/sh02-20261016/audit-by-gumi.md) · [SH-03 开工单](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：第一期（Phase 1）拆分为三个顺序审计阶段（`SH-01` → `SH-02` → `SH-03`）；**`SH-01` 与 `SH-02` 均已通过谷米独立审计结项（`done`）**；当前进入第一期收官阶段 **`SH-03`（状态：`ready`，待稳米按单实施）**。
- **已完成范围**：
  1. 独立仓库 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 基线与交接文档落盘；
  2. **`SH-01` 已完工并通过谷米审计（[`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md)）**；
  3. **Grok 三波调研弹药库已验收入库（[`docs/aihot_research/`](docs/aihot_research/INDEX.md)）**；
  4. **`SH-02` 经稳米 R1 返工（`8991289`）并通过谷米二次复审（[`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md)）**：56/56 Python 单测、22/22 Node 契约单测与 [`scripts/verify-bridge-contract.ts`](scripts/verify-bridge-contract.ts) 跨语言端到端验证全部通过（4 轨 41 条 100% 入库、`backfill=0`、`undated=0`、`hot_signal` 成功进入事件热度归组）。
- **尚未完成**：`SH-03`（`@aihot/short-term-radar` 双视图短线雷达模块与端到端联调）的代码开发、测试验证与阶段终审。
- **下一步唯一任务**：**稳米**按 [`docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md`](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) 实施 `SH-03`，完工后更新证据交谷米终审。

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
| `SH-03` | `ready` | **`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：稳米按 `WO-SH03-20261016` 实现 S1 模块注册、S2 `/api/site/radar` + `/api/v1/radar` + AgentAbility、S3 双视图看板与侧滑舆情抽屉、S4 全套自动化测试与 Web 构建门禁。 | [SH-03 开工单](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) |
| `SH-04` | `backlog` | **二期扩展**：接入韭研公社题材逻辑帖、用 `.data/gold.jsonl`（70 条已就位）跑 `eval-selection.ts` 校准门槛、联动游资龙虎榜 (`hm_detail`) 与互动易 (`irm_qa`)。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 17:17 CST | `SH-02` 二次复审通过 & `SH-03` 开工单签发 | 谷米**
  - **结果**：独立复测稳米提交 `8991289` / `0fb7354`。Python 单测 56/56 通过，`npm run typecheck` 零报错，`ingest/provenance/architecture` 22/22 通过，[`scripts/verify-bridge-contract.ts`](scripts/verify-bridge-contract.ts) 端到端验证四轨 41 条 payload 100% 入库（`planned === created`，`backfill=0`，`undated=0`，`hot_signal` 轨 `settleNonEditorial` 返回 `group=true`）。出具 [`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) R2 PASS 结论，并签发 [`docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md`](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md)。
  - **下一步**：交稳米实施 `SH-03`。

- **2026-10-16 16:30 CST | `SH-02` R1 返工提交 | 稳米**
  - **结果**：提交 `8991289` / `0fb7354`，逐条修复 R1 审计指出的 4 项跨语言契约缺陷并新增 `scripts/verify-bridge-contract.ts`。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / `SH-02` 结项 | [`docs/evidence/sh02-20261016/`](docs/evidence/sh02-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) | 完成 `bridge/` 焦点股池、三社区采集、System 1 情绪引擎及四轨跨语言契约对齐，谷米二次复审通过。 |
| 2026-10-16 / `SH-01` 结项 | [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) | 完成 AIHOT 站点与 A 股短线 6 大分类/提示词/测试适配，谷米独立复测通过。 |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |
