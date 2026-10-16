# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 13:05（Asia/Shanghai）；状态依据：AIHOT 基座落盘（上游基线 `c8704e5`）与第一阶段开工单 `SH-01` 签发

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：第一期（Phase 1）拆分为三个顺序审计阶段（`SH-01` → `SH-02` → `SH-03`），当前进入 **`SH-01`（基座环境打通与 `site/` + `industry/` A 股短线 KnowHow 改造）**。
- **已完成范围**：
  1. 独立仓库 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 已从 `KKKKhazix/AIHOT`（commit `c8704e5313e6b051560365226b3919d7e0ada5ea`）克隆落盘，上游原版 `README.md` 与 `AGENTS.md` 已备份至 [`docs/upstream/`](docs/upstream/)；
  2. 完成交接级 [`README.md`](README.md)、[`AGENTS.md`](AGENTS.md)、[`docs/实施与验收计划.md`](docs/实施与验收计划.md) 及第一阶段开工单 [`docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md`](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) 落盘。
- **尚未完成**：`SH-01`、`SH-02`、`SH-03` 的代码开发与测试验证。
- **下一步唯一任务**：由 **稳米** 按 [`docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md`](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) 执行 `SH-01`（完成 `site/`、`industry/` A 股短线化改造与对应测试适配，跑通 `typecheck`、后端 `_test` 单测与前端 build），交付证据并更新本文件后停下，交 **谷米** 审计。

## 有效边界与决定

- **协作模式（2026-10-16 弈沐拍板）**：**谷米**负责规划、写开工单与阶段审查；**稳米**负责按单实施。**完成一个阶段、审计一个阶段**，未获上一阶段审计通过前不跨阶段施工。
- **独立工程边界（2026-10-16 弈沐拍板）**：作为 `YM_Capital` 下的独立项目建设，不与 `live-dashboard`（8088）混用代码、数据库或端口；本站默认端口为 `3088`。
- **数据源与第一批社区范围（2026-10-16 弈沐拍板）**：
  - 结构化热榜（同花顺 `ths_hot`、东财 `dc_hot`）、涨跌停池 (`market_intraday_state`)、开盘啦题材 (`kpl_list`/`kpl_concept`)、同花顺涨停原因 (`limit_list_ths`) 统一在 `SH-02` 通过 `/Users/yimu/Projects/YM_Capital/YM-data-pipeline` 公共入口读取；
  - 第一批社区评论范围固定为：**① 东方财富股吧**（实时评论流、盖楼流速、散户多空情绪）、**② 淘股吧 TGB**（24h 热帖榜、实盘复盘贴、焦点股接力跟帖）、**③ 雪球**（热股讨论榜、个股高赞深度逻辑拆解）。
- **产品视图与运行频率（2026-10-16 弈沐拍板）**：
  - 在 `SH-03` 通过 `modules/short-term-radar/` 实现双视图切换：默认 **「🧩 题材主线梯队视图」**，一键切换 **「🔥 跨平台人气共振 Top 30 榜」** + 个股社区舆情侧滑抽屉；
  - 交易时段每 10~15 分钟滚动刷新热榜与评论流速，盘前（08:30）与盘后（15:35）生成深度汇总。

## 未完成队列

| ID | 状态 | 下一动作 / 退出条件 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `ready` | **【当前执行】基座环境与 A 股短线 KnowHow 改造**：稳米按 `SH-01` 开工单完成依赖安装、`site/site.ts`（站名 `YM-HOT`、端口 `3088`、早刊 `08:30`）、`industry/taxonomy.ts`（6 大短线分类与题材/连板标签）、`industry/topics.json`、`industry/sources.json`、`industry/prompts/*.md` 改造及测试适配；`npm run typecheck`、`npm test`、`npm run build -w @aihot/web` 全绿后交谷米审计。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) |
| `SH-02` | `queued` | **`YM-data-pipeline` 桥接与三大社区靶向采集器 (`bridge/`)**：待 `SH-01` 审计通过后由谷米签发细化单。实现焦点股池圈定、东财股吧/淘股吧/雪球评论抓取、15m 盖楼流速与分歧度合成、`/api/ingest/items` 双轨推送（`editorial` vs `hot_signal`）及离线 fixture 测试。 | [实施与验收计划 §SH-02](docs/实施与验收计划.md) |
| `SH-03` | `queued` | **`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：待 `SH-02` 审计通过后由谷米签发细化单。实现模块数据库迁移、API、题材主线梯队 ⇄ Top 30 人气共振双视图、个股舆情抽屉及盘中 15m 调度，完成 `smoke.ts` 端到端验收。 | [实施与验收计划 §SH-03](docs/实施与验收计划.md) |
| `SH-04` | `backlog` | **二期扩展**：接入韭研公社题材逻辑帖、建立 `.data/gold.jsonl` 短线金标集跑 `eval-selection.ts` 校准门槛、联动游资龙虎榜 (`hm_detail`) 与互动易 (`irm_qa`)。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 13:05 CST | `SH-01` 开单与框架落盘 | 谷米**
  - **结果**：从 `KKKKhazix/AIHOT` 克隆独立仓库至 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot`（基线 `c8704e5313e6b051560365226b3919d7e0ada5ea`）；保全上游文档至 `docs/upstream/`；落盘 `README.md`、`AGENTS.md`、`PROGRESS.md`、`docs/实施与验收计划.md` 与 `docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md`。
  - **验证范围**：文档与基线核对完成；尚未修改业务源码。
  - **下一步**：交稳米执行 `SH-01` 开工单，完成后由谷米执行 Stage 1 审计。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |
