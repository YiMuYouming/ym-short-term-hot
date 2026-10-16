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
| `SH-03` | `in_review` | **【已交付，待谷米第一期终审】`@aihot/short-term-radar` 双视图模块 (`modules/short-term-radar/`)**：`module.ts` 声明 `/radar` 页面与 `/api/(site|v1)/radar`；`server.ts` 只读 `config.dataDir` 下的快照（**零新增数据库表**），提供四条 API + Agent/MCP `get_radar`，快照缺失或损坏降级为 `mode: "empty"`；`web/radar-route.tsx` 双视图 + 三色情绪条 + 身位/黑话徽章 + 个股舆情抽屉（仅走 HTTP）。门禁：bridge 56/56、typecheck、web build、模块单测 4/4、架构与引擎回归 19/19、页面 SSR 2/2，全量 `npm test` 737 通过且新增回归 0。 | [SH-03 开工单](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) · [验证记录](docs/evidence/sh03-20261016/verification.md) |
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

- **2026-10-16 19:20 CST | `SH-03` 实施交付（第一期收官）| 稳米**
  - **结果**：新增 `modules/short-term-radar/`（约 1200 行）并注册进 `site/modules/{index,server,web}.ts`。后端只读 `.data/short-term-radar-snapshot.json`（`config.dataDir`，**零新增数据库表**），提供 `GET /api/site/radar`、`/api/v1/radar`、`/api/site/radar/stock/:code`、`/api/v1/radar/stock/:code`，支持 `?theme= &role= &q=`（`q` 支持「易中天」「寒王」等社区黑话），以及 Agent/MCP 能力 `/api/v1/agent/radar` 与 `get_radar`。前端 `/radar` 提供「🧩 题材主线梯队 ⇄ 🔥 人气共振 Top 30」双视图（`?view=` 同步）、搜索与身位快筛、三色社区情绪温度条（红/琥珀/绿）、身位与黑话徽章，以及点击个股滑出的社区舆情与游资逻辑抽屉（游资复盘/雪球深度/股吧热评 + 原帖外链，Esc 与遮罩关闭）。
  - **契约处置**：工单 §二 的输入 schema 与 SH-02 实产快照有字段漂移（`roleLabel` vs `role`、占比 0~100 vs 0~1、梯队按身位分桶 vs 拍平列表，以及快照中不存在的 `turnoverRate`/`kplTag`/`limitReason`）。处置原则是不改 Python 产物，把漂移集中在 `modules/short-term-radar/contracts.ts` 一处映射，后端与前端只认映射后的契约；缺失字段置空并在页面优雅隐藏。
  - **验证范围**：bridge 单测 56/56；`npm run typecheck` 与 `npm run build -w @aihot/web` 均 exit 0（`/radar` 打包为独立 chunk）；架构四条红线逐条通过；模块单测 4/4；页面 SSR 测试 2/2（真 api + 生产 web server 渲染出题材、身位、黑话、情绪与抽屉）；干净模板库全量 `npm test` 737 通过 / 16 失败，失败集与 SH-01 上游基线完全一致（14 项环境类），**新增回归 0**。
  - **两个环境问题（非代码缺陷）已处置**：① `ymhot_test` 是全仓测试的模板库，SH-02 旧版契约脚本曾写入 20 条 `contract-*` 信源导致计数类测试连锁失败——脚本已改为自建一次性库，重建模板库后全量干净；② 并行使用同一模板库会触发 `source database is being accessed by other users`，门禁改为串行、SSR 测试用独立库。
  - **下一步**：交谷米做第一期终审（证据 `docs/evidence/sh03-20261016/verification.md`）。
