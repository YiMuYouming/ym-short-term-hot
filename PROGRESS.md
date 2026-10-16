# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 15:05（Asia/Shanghai）；状态依据：`SH-01` 已实施交付，等待谷米阶段审计

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：第一期（Phase 1）拆分为三个顺序审计阶段（`SH-01` → `SH-02` → `SH-03`）；`SH-01`（基座环境打通与 `site/` + `industry/` A 股短线 KnowHow 改造）已由稳米实施完毕并交付证据，当前停在**等待谷米阶段审计**。
- **已完成范围**：
  1. 独立仓库 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 已从 `KKKKhazix/AIHOT`（commit `c8704e5313e6b051560365226b3919d7e0ada5ea`）克隆落盘，上游原版 `README.md` 与 `AGENTS.md` 已备份至 [`docs/upstream/`](docs/upstream/)；
  2. 完成交接级 [`README.md`](README.md)、[`AGENTS.md`](AGENTS.md)、[`docs/实施与验收计划.md`](docs/实施与验收计划.md) 及第一阶段开工单 [`docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md`](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) 落盘；
  3. **`SH-01` 已实施**：`site/site.ts`（站名 `YM-HOT`、行业词「A股短线」、`http://localhost:3088`、早刊 `08:30`、MCP 前缀 `ymhot`、`ITEM_COPY.reasonLabel=短线看点`）、`.env.example` 与 `docker-compose.yml`/`Dockerfile`/`deploy/Caddyfile` 端口默认改 `3088`（与 `live-dashboard` 的 `8088` 不冲突）、安全阀 `COLLECT_ENABLED`/`MODEL_CALLS_ENABLED` 置 `false`；
     `industry/taxonomy.ts` 落成 6 大短线分类（`theme-catalyst`/`dragon-move`/`company-signal`/`deep-logic`/`youzi-review`/`sentiment-pulse`）+ 12 个分类标签 + 16 个题材/战法标签 + 9 个平台与监管主体、`industry/topics.json` 三组共 28 个主题、`industry/sources.json` 四个 `external` 占位信源、`industry/prompts/*.md` 短线化改造，并同步适配 `tests/` 与 `apps/web/tests/` 的旧示例断言。
- **尚未完成**：`SH-01` 审计、`SH-02`、`SH-03` 的代码开发与测试验证。
- **下一步唯一任务**：**谷米**执行 [`SH-01`](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) 阶段审计（证据目录 [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/)，差集说明见其中 `baseline-failures.txt` 与 `environment.txt`）；审计通过前稳米不跨阶段施工。

## 有效边界与决定

- **协作模式（2026-10-16 弈沐拍板）**：**谷米**负责规划、写开工单与阶段审查；**稳米**负责按单实施。**完成一个阶段、审计一个阶段**，未获上一阶段审计通过前不跨阶段施工。
- **独立工程边界（2026-10-16 弈沐拍板）**：作为 `YM_Capital` 下的独立项目建设，不与 `live-dashboard`（8088）混用代码、数据库或端口；本站默认端口为 `3088`。
- **数据源与第一批社区范围（2026-10-16 弈沐拍板）**：
  - 结构化热榜（同花顺 `ths_hot`、东财 `dc_hot`）、涨跌停池 (`market_intraday_state`)、开盘啦题材 (`kpl_list`/`kpl_concept`)、同花顺涨停原因 (`limit_list_ths`) 统一在 `SH-02` 通过 `/Users/yimu/Projects/YM_Capital/YM-data-pipeline` 公共入口读取；
  - 第一批社区评论范围固定为：**① 东方财富股吧**（实时评论流、盖楼流速、散户多空情绪）、**② 淘股吧 TGB**（24h 热帖榜、实盘复盘贴、焦点股接力跟帖）、**③ 雪球**（热股讨论榜、个股高赞深度逻辑拆解）。
- **产品视图与运行频率（2026-10-16 弈沐拍板）**：
  - 在 `SH-03` 通过 `modules/short-term-radar/` 实现双视图切换：默认 **「🧩 题材主线梯队视图」**，一键切换 **「🔥 跨平台人气共振 Top 30 榜」** + 个股社区舆情侧滑抽屉；
  - 交易时段每 10~15 分钟滚动刷新热榜与评论流速，盘前（08:30）与盘后（15:35）生成深度汇总。
- **站点与分类口径（2026-10-16 SH-01 实施落地）**：站点身份 `YM-HOT`、默认端口 `3088`、早刊 `08:30`；行业分类固定为 6 个（题材/龙头/实锤/逻辑/复盘/舆情），其中后三类为评论类（`commentary`）；未归类资料按框架规则落到最后一个分节（当前为「游资复盘与博弈」），后续如需调整应在下一阶段以迁移方式改，不改已上线 `key`。
- **本地开发环境事实（2026-10-16 SH-01 核对）**：Node 用 Homebrew `v26.11.0`（engines 要求 ≥ 24.11）；本地 PostgreSQL 由 `@embedded-postgres/darwin-arm64` 提供（数据目录在仓库外的 `AgentScratch`，launchd plist 已写好但当前登录会话内 `launchctl bootstrap` 报 EIO，常驻化待用户在自有终端执行一次，详见 `docs/evidence/sh01-20261016/environment.txt`）。

## 未完成队列

| ID | 状态 | 下一动作 / 退出条件 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `delivered_pending_audit` | **【已交付，待谷米审计】基座环境与 A 股短线 KnowHow 改造**：`site/`（`YM-HOT`/`3088`/早刊 `08:30`）、`industry/`（6 大分类、标签、主体、主题、信源、提示词）与 `tests/`、`apps/web/tests/` 旧示例断言适配完成；`npm run typecheck` 通过；后端 `_test` 全量与上游基线 `c8704e5` 做差集后新增失败为 0（既有 14 项为沙箱环境类，见 `baseline-failures.txt`）；`tests/architecture.test.ts` 6 项全过。审计通过前不得开 `SH-02`。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [证据](docs/evidence/sh01-20261016/manifest.json) |
| `SH-02` | `queued` | **`YM-data-pipeline` 桥接与三大社区靶向采集器 (`bridge/`)**：待 `SH-01` 审计通过后由谷米签发细化单。实现焦点股池圈定、东财股吧/淘股吧/雪球评论抓取、15m 盖楼流速与分歧度合成、`/api/ingest/items` 双轨推送（`editorial` vs `hot_signal`）及离线 fixture 测试。 | [实施与验收计划 §SH-02](docs/实施与验收计划.md) |
| `SH-03` | `queued` | **`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：待 `SH-02` 审计通过后由谷米签发细化单。实现模块数据库迁移、API、题材主线梯队 ⇄ Top 30 人气共振双视图、个股舆情抽屉及盘中 15m 调度，完成 `smoke.ts` 端到端验收。 | [实施与验收计划 §SH-03](docs/实施与验收计划.md) |
| `SH-04` | `backlog` | **二期扩展**：接入韭研公社题材逻辑帖、建立 `.data/gold.jsonl` 短线金标集跑 `eval-selection.ts` 校准门槛、联动游资龙虎榜 (`hm_detail`) 与互动易 (`irm_qa`)。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 15:05 CST | `SH-01` 实施交付 | 稳米**
  - **结果**：按 `SH-01` 开工单完成 S1~S5——`site/site.ts`（站名 `YM-HOT`、行业词「A股短线」、`http://localhost:3088`、早刊 `08:30`、MCP 前缀 `ymhot`、`reasonLabel=短线看点`、ABOUT/REPORTS/CARDS 文案短线化）；`.env.example` 与 `docker-compose.yml`/`Dockerfile`/`deploy/Caddyfile` 端口默认改 `3088`，安全阀 `COLLECT_ENABLED`/`MODEL_CALLS_ENABLED` 由 `true` 置 `false`；`industry/taxonomy.ts` 换成 6 大短线分类、12 分类标签、16 题材/战法标签、9 个平台与监管主体（`IDENTITY_LEXICON` 保留 9 条实体守卫）；`industry/topics.json` 重建为 3 组 28 个主题；`industry/sources.json` 换成 4 个 `external` 占位信源（供 `SH-02` 桥接推送）；`industry/prompts/` 中 `prefilter`、`selection-score`、`structure`、`content-understanding`、`rules-domain` 五份主线提示词完成短线化（契约与占位符不变），并同步 `summarize-*`、`rules-self-contained-title`、`translate-body`、`report-period`、`identity-context` 的行业举例；`tests/` 与 `apps/web/tests/` 共 34 个测试文件的旧分类/标签/实体断言完成适配（`daily-report-alerts` 的临界时间随 08:30 出刊后移到 10:35 起）。
  - **验证范围**：`npm run typecheck` exit 0；`DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test npm test` 731 项通过、14 项失败与上游基线 `c8704e5` 同环境跑分完全一致（新增失败 0，归因见 `docs/evidence/sh01-20261016/baseline-failures.txt`）；`tests/architecture.test.ts` 6 项全过；前端 `node --test apps/web/tests/*.test.ts` 需先有 `apps/web/build`（该文件经 web-server 启动 SSR 服务），串行跑分结果见 `docs/evidence/sh01-20261016/web-build-test.txt`。
  - **环境例外（需知悉）**：本机无 PostgreSQL，改用 `@embedded-postgres/darwin-arm64` 自带二进制提供 `127.0.0.1:5432`；launchd 常驻 plist 已写好但当前登录会话 `launchctl bootstrap` 报 EIO，需在自有终端执行一次（见 `docs/evidence/sh01-20261016/environment.txt`）。另有仓库内他人产生的未跟踪目录 `docs/aihot_research/`，本次未纳入提交、未改动。
  - **下一步**：交谷米执行 `SH-01` 阶段审计（证据索引 `docs/evidence/sh01-20261016/manifest.json`）；审计通过前稳米不跨阶段施工。

- **2026-10-16 13:05 CST | `SH-01` 开单与框架落盘 | 谷米**
  - **结果**：从 `KKKKhazix/AIHOT` 克隆独立仓库至 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot`（基线 `c8704e5313e6b051560365226b3919d7e0ada5ea`）；保全上游文档至 `docs/upstream/`；落盘 `README.md`、`AGENTS.md`、`PROGRESS.md`、`docs/实施与验收计划.md` 与 `docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md`。
  - **验证范围**：文档与基线核对完成；尚未修改业务源码。
  - **下一步**：交稳米执行 `SH-01` 开工单，完成后由谷米执行 Stage 1 审计。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |
