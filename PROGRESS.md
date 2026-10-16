# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 18:44（Asia/Shanghai）；状态依据：谷米完成 `SH-03` 第二次终审（`AUDIT-SH03-20261016-R2`）判定 **PASS 结项**，**第一期（Phase 1：`SH-01` → `SH-02` → `SH-03`）全链路圆满收官！**

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-01 审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) · [SH-02 审计报告](docs/evidence/sh02-20261016/audit-by-gumi.md) · [SH-03 终审收官报告](docs/evidence/sh03-20261016/audit-by-gumi.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：**第一期（Phase 1）三个顺序阶段（`SH-01` → `SH-02` → `SH-03`）已全部完工并通过谷米独立审计结项（`done`）！** 下一阶段为第二期扩展（`SH-04`，当前 Grok 正在并行深挖第四~第六波二期弹药库）。
- **第一期已完成范围**：
  1. **`SH-01`（`done`）**：基座环境与 A 股短线 6 大分类/提示词/测试适配（[`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md)）；
  2. **`SH-02`（`done`）**：`YM-data-pipeline` 焦点股池桥接、三大社区（东财股吧/淘股吧/雪球）采集器、System 1 反水贴与三色情绪引擎、四轨跨语言入库契约（[`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md)）；
  3. **`SH-03`（`done`）**：`@aihot/short-term-radar` 扩展模块（[`modules/short-term-radar/`](modules/short-term-radar/)）——四条雷达 API + Agent/MCP `get_radar` 能力 + 前端 **「🧩 题材主线梯队 ⇄ 🔥 人气共振 Top 30」** 双视图切换 + 三色情绪温度条 + 右侧 **「个股社区舆情与游资逻辑侧滑抽屉」**，经 R1 返工（`3bedb0d`）与谷米 R2 复审（[`audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md)）全绿通过。
- **下一步任务**：待 Grok 完成第四~第六波调研（龙虎榜量化席位 vs 主观游资图谱、韭研公社与财联社快讯接口、60 题材扩容与海外映射字典）后，由谷米验收并规划第二期 `SH-04` 工单。

## 有效边界与决定

- **协作模式（2026-10-16 弈沐拍板）**：**谷米**负责规划、写开工单与阶段审查；**稳米**负责按单实施；**Grok**负责并行搜索与词典/席位/样本整理。**完成一个阶段、审计一个阶段**。
- **独立工程边界（2026-10-16 弈沐拍板）**：作为 `YM_Capital` 下的独立项目建设，不与 `live-dashboard`（8088）混用代码、数据库或端口；本站默认端口为 `3088`。
- **数据源与社区范围（2026-10-16 弈沐拍板）**：
  - 第一期已打通 `YM-data-pipeline` + **① 东方财富股吧**、**② 淘股吧 TGB**、**③ 雪球**；
  - 第二期（`SH-04`）重点扩展：**龙虎榜量化基金席位识别 vs 主观游资图谱**、**韭研公社 + 财联社电报**、**60 题材扩容与隔夜海外催化映射**。

## 阶段队列

| ID | 状态 | 阶段成果 / 下一动作 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `done` | **【已结项】基座环境与 A 股短线 KnowHow 改造**：`site/`、`industry/` 与 39 个测试文件适配完成。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [谷米审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) |
| `SH-02` | `done` | **【已结项】`YM-data-pipeline` 桥接与三大社区靶向采集 (`bridge/`)**：56 项 Python 单测 + 四轨跨语言入库契约（41/41 入库，`backfill=0`）全部绿灯。 | [SH-02 开工单](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) · [谷米复审报告](docs/evidence/sh02-20261016/audit-by-gumi.md) |
| `SH-03` | `done` | **【已结项 · 第一期收官】`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：4 条架构红线、56 项 Python 单测、`typecheck`、`web build`、5 项模块 API 单测与 2 项真实 SSR 端到端测试全部绿灯，梯队矛盾清零（`27 → 0`）。 | [SH-03 开工单](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) · [谷米终审报告](docs/evidence/sh03-20261016/audit-by-gumi.md) |
| `SH-04` | `backlog` | **二期扩展**：吸收 Grok 第四~第六波成果（量化席位 vs 游资龙虎榜识别、韭研公社与快讯电报、60 题材与海外映射），并用 `.data/gold.jsonl` 校准精选门槛。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 18:44 CST | `SH-03` 二次终审通过（第一期全链路收官） | 谷米**
  - **结果**：独立复测稳米提交 `3bedb0d`。全量梯队一致性诊断 `{ missingThemeCount: 0, unqualCodeCount: 0, roleMismatch: 0 }`（27 处不一致全部清零）；Python 单测 56/56、`npm run typecheck`、`npm run build -w @aihot/web`、架构红线 + 入库契约 + 模块单测 + 真实 SSR 测试 18/18 全部绿灯（含 `/radar?q=易中天` 过滤掉 `宁德时代`、`/radar?theme=消费电子` 命中 `立讯精密` 且过滤掉 `光模块` 的正负向断言）。出具 [`audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md) R2 PASS 结论，第一期圆满收官。
- **2026-10-16 18:39 CST | `SH-03` R1 返工提交 | 稳米**
  - **结果**：提交 `3bedb0d`，修复 `contracts.ts` 尾部 20 只梯队股字段补齐与 `radar-route.tsx` SSR/客户端 `?q=`、`?theme=` 直链过滤，新增 `radar.test.ts` 与 `radar-page.test.ts` 回归锁。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / `SH-03` 结项（一期收官） | [`docs/evidence/sh03-20261016/`](docs/evidence/sh03-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md) | 完成 `@aihot/short-term-radar` 双视图模块、舆情侧滑抽屉、Agent/MCP 能力及全链路契约验证，谷米二次终审通过。 |
| 2026-10-16 / `SH-02` 结项 | [`docs/evidence/sh02-20261016/`](docs/evidence/sh02-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) | 完成 `bridge/` 焦点股池、三社区采集、System 1 情绪引擎及四轨跨语言契约对齐，谷米二次复审通过。 |
| 2026-10-16 / `SH-01` 结项 | [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) | 完成 AIHOT 站点与 A 股短线 6 大分类/提示词/测试适配，谷米独立复测通过。 |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |
