# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 16:04（Asia/Shanghai）；状态依据：谷米完成 `SH-02` 第一次阶段审计（`AUDIT-SH02-20261016-R1`），抓出 2 个 P0 + 2 个 P1 跨语言契约缺陷，退回稳米定点返工修补

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-02 开工单](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) · [SH-02 审计报告（需返工）](docs/evidence/sh02-20261016/audit-by-gumi.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：第一期（Phase 1）拆分为三个顺序审计阶段（`SH-01` → `SH-02` → `SH-03`）；`SH-01` 已通过谷米审计结项（`done`）；**`SH-02` 经谷米第一次独立审计发现 2 个跨语言阻断级 P0 缺陷与 2 个 P1 缺陷（状态：`rework_required`），退回稳米定点修补**，修完复审通过后再开 `SH-03`。
- **已完成范围**：
  1. 独立仓库 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 基线与交接文档落盘；
  2. **`SH-01` 已完工并通过谷米审计（[`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md)）**；
  3. **Grok 三波调研弹药库已验收入库（[`docs/aihot_research/`](docs/aihot_research/INDEX.md)）**；
  4. **`SH-02` 主体代码已落地（待返工修补 4 项契约缺陷）**：`bridge/` 的焦点股池、System 1 情绪与反水贴引擎、三社区采集器、快照与金标同步主体质量优秀，但 `bridge/push_to_aihot.py` 与 `bridge/collectors/taoguba.py` 存在 4 项与 TS 后端 `ingestItems` / `decideTimeline` 冲突的缺陷（详见 [`docs/evidence/sh02-20261016/audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md)）。
- **尚未完成**：`SH-02` 4 项缺陷返工与二次审计；`SH-03` 的代码开发、测试验证与阶段审计。
- **下一步唯一任务**：**稳米**按 [`docs/evidence/sh02-20261016/audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) 定点修补 `SH-02` 的 4 项缺陷并补齐跨语言契约单测，更新证据后交谷米二次审计。

## 有效边界与决定

- **协作模式（2026-10-16 弈沐拍板）**：**谷米**负责规划、写开工单与阶段审查；**稳米**负责按单实施。**完成一个阶段、审计一个阶段**，未获上一阶段审计通过前不跨阶段施工。
- **独立工程边界（2026-10-16 弈沐拍板）**：作为 `YM_Capital` 下的独立项目建设，不与 `live-dashboard`（8088）混用代码、数据库或端口；本站默认端口为 `3088`。
- **数据源与第一批社区范围（2026-10-16 弈沐拍板）**：
  - 结构化热榜（同花顺 `ths_hot`、东财 `dc_hot`）、涨跌停池 (`market_intraday_state`)、开盘啦题材 (`kpl_list`/`kpl_concept`)、同花顺涨停原因 (`limit_list_ths`) 统一在 `SH-02` 通过 `/Users/yimu/Projects/YM_Capital/YM-data-pipeline` 公共入口读取；
  - 第一批社区评论范围固定为：**① 东方财富股吧**、**② 淘股吧 TGB**、**③ 雪球**。
- **产品视图与运行频率（2026-10-16 弈沐拍板）**：
  - 在 `SH-03` 通过 `modules/short-term-radar/` 实现双视图切换：默认 **「🧩 题材主线梯队视图」**，一键切换 **「🔥 跨平台人气共振 Top 30 榜」** + 个股社区舆情侧滑抽屉；
  - 交易时段每 10~15 分钟滚动刷新热榜与评论流速，盘前（08:30）与盘后（15:35）生成深度汇总。

## 未完成队列

| ID | 状态 | 下一动作 / 退出条件 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `done` | **【已通过谷米审计】基座环境与 A 股短线 KnowHow 改造**：`site/`、`industry/` 与 39 个测试文件适配完成。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [谷米审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) |
| `SH-02` | `rework_required` | **【需返工修补】`YM-data-pipeline` 桥接与三大社区靶向采集 (`bridge/`)**：稳米按 [`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) 修复：① `pipeline_report_item` 的 `ymhot://` 协议被后端 `normalizeUrl()` 静默丢弃（改用合法 `https://` 地址）；② `pipeline_report_item` 与 `community_item` 漏传 `published_at` 导致 100% 沦为 `backfill=true` 历史回填；③ `taoguba.py` 解析 `%m-%d %H:%M` 缺少年份变为 1900 年；④ 补齐 Python → TS `ingestItems` 契约测试。 | [SH-02 审计报告（需返工）](docs/evidence/sh02-20261016/audit-by-gumi.md) |
| `SH-03` | `queued` | **`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：待 `SH-02` 复审通过后由谷米签发细化单。 | [实施与验收计划 §SH-03](docs/实施与验收计划.md) |
| `SH-04` | `backlog` | **二期扩展**：接入韭研公社题材逻辑帖、用 `.data/gold.jsonl`（70 条已就位）跑 `eval-selection.ts` 校准门槛、联动游资龙虎榜 (`hm_detail`) 与互动易 (`irm_qa`)。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 16:04 CST | `SH-02` 第一次阶段审计（退回返工） | 谷米**
  - **结果**：审查稳米提交 `411d694`/`57c44ad`。Python 侧焦点股池、情绪引擎与三社区解析质量优秀，但在与 TS 后端 `ingestItems` / `normalizeUrl` / `decideTimeline` 做跨语言对账时发现 2 个 P0 阻断缺陷与 2 个 P1 缺陷：① `pipeline_report_item` 用了 `ymhot://radar/stock/...`，被后端 `normalizeUrl()`（只认 `http:/https:`）100% 静默丢弃（`created: 0`）；② `pipeline_report_item` 与 `community_item` 均未传 `published_at`，导致后端 `decideTimeline()` 将 100% 推送条目标为 `backfill=true`（`unknown-publication-time`）且 `isHistorical()===true`，使股吧 `hot_signal` 完全无法进入事件归组计热度、三条 `editorial` 轨无法建事件与进热榜/日报；③ `taoguba.py` 解析 `%m-%d %H:%M` 年份落为 `1900` 年；④ 缺少四轨 payload 到 TS `ingestItems` 的契约单测。
  - **下一步**：出具 [`docs/evidence/sh02-20261016/audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md)，交稳米定点返工修补。

- **2026-10-16 15:45 CST | `SH-02` 实施交付 | 稳米**
  - **结果**：按 `SH-02` 开工单完成 S1~S5，51 项离线单测与快照演练通过，提交 `411d694` / `57c44ad`。

- **2026-10-16 15:18 CST | `SH-01` 审计通过 & `SH-02` 开工单签发 | 谷米**
  - **结果**：出具 [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) 判定 `SH-01` 一次通过；签发 `SH-02` 开工单。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / `SH-01` 结项 | [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) | 完成 AIHOT 站点与 A 股短线 6 大分类/提示词/测试适配，谷米独立复测通过。 |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |
