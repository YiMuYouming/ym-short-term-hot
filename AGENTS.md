# YM-ShortTerm-Hot · Agent 规范与协作边界

本文件是 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 的权威 Agent 入口。任何 Agent 进入本仓库后，按以下顺序读取上下文：
1. 先读 [`PROGRESS.md`](PROGRESS.md)（按 `当前摘要 → 有效边界与决定 → 未完成队列 → 最近记录` 顺序读，不要只读文件末尾）；
2. 再读当前处于激活状态的开工单（见 `PROGRESS.md` 的“下一步唯一任务”，首期第一阶段为 [`docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md`](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md)）；
3. 需要了解全局蓝图时读 [`docs/实施与验收计划.md`](docs/实施与验收计划.md)；需要查阅 AIHOT 底层机制时读 [`docs/architecture.md`](docs/architecture.md)、[`docs/customize.md`](docs/customize.md) 与 [`docs/upstream/AIHOT-AGENTS.md`](docs/upstream/AIHOT-AGENTS.md)。

---

## 1. 协作分工铁律（谷米 × 稳米）

- **谷米（规划、开单与审查）**：
  - 负责制定分阶段实施方案、签发具体开工单（`SH-01`、`SH-02`、`SH-03`……）；
  - 在稳米完成一个阶段后，独立核验 git diff、测试回执、架构边界与契约一致性，出具审计结论（通过后才签发下一阶段开工单）。
- **稳米（分阶段工程实施）**：
  - 严格在当前开工单划定的文件与功能边界内施工；
  - **完成一个阶段即停**：跑通本阶段全部门禁测试、生成 `docs/evidence/<单号>/` 证据与 `manifest.json`、按 [`../shared/progress-workflow.md`](../shared/progress-workflow.md) 更新 `PROGRESS.md` 后立即停止，等待弈沐转交谷米审计，**不得自行跨阶段继续开发下一阶段**。

---

## 2. 必须守住的架构与安全边界

1. **完全独立于 `live-dashboard`**：
   - 本项目是独立仓库，严禁修改 `/Users/yimu/Projects/YM_Capital/live-dashboard` 的任何文件或占用 `8088`/`18088`/`18089` 端口；本项目默认端口统一使用 `3088`。
2. **结构化行情与热榜 100% 走 `YM-data-pipeline`**：
   - 同花顺热榜 (`ths_hot`)、东方财富人气榜 (`dc_hot`)、涨跌停池 (`market_intraday_state`)、开盘啦题材 (`kpl_list`/`kpl_concept`)、同花顺涨停原因 (`limit_list_ths`)、连板天梯 (`limit_step`) 必须通过 `/Users/yimu/Projects/YM_Capital/YM-data-pipeline` 的公共契约（`from ym_stock_data import query` 或 `./ym-data`）读取；
   - 严禁在 `bridge/` 中绕过数据管道私自编写同花顺热榜、涨停池或行情爬虫。
3. **严守 AIHOT 框架分层规则（确保 `tests/architecture.test.ts` 通过）**：
   - 站点身份、端口与出刊时间改 `site/`；
   - A 股短线分类、标签词表、实体与提示词改 `industry/`；
   - 短线专属「题材主线梯队 ⇄ 跨平台人气共振 Top 30」双视图看板与雷达表放在 `modules/short-term-radar/`，并在 `site/modules/` 注册；
   - **禁止**把短线特定业务逻辑硬塞进 `packages/backend/`，除非是框架级通用插口扩展。
4. **安全阀与凭据零泄漏**：
   - 开发与测试期间，`.env` 中的 `COLLECT_ENABLED`、`MODEL_CALLS_ENABLED`、`FEISHU_CONTENT_PUSH_ENABLED`、`FEISHU_INTERNAL_ENABLED`、`INDEXNOW_SUBMIT_ENABLED` 默认保持 `false`；
   - 单元测试必须 100% 离线运行（连接本地 fake 服务与 `_test` 数据库），不得在测试中请求真实外部社区或消耗真实大模型/StockToday 额度；
   - 任何 API Key、Token、Cookie 严禁写入代码、测试夹具、日志、Git 提交或 `docs/evidence/`。
