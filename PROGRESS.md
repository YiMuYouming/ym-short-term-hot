# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 15:45（Asia/Shanghai）；状态依据：`SH-01` 已结项（谷米审计通过）；`SH-02` 已由稳米实施交付，等待谷米阶段审计

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-02 开工单](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：第一期（Phase 1）拆分为三个顺序审计阶段（`SH-01` → `SH-02` → `SH-03`）；`SH-01` 已通过**谷米**独立审计并结项（`done`），Grok 的三波社区接口与词典调研资产 [`docs/aihot_research/`](docs/aihot_research/INDEX.md) 已验收入库；**`SH-02`（`YM-data-pipeline` 桥接与三大短线社区靶向采集）已由稳米按单实施完毕并交付证据**，当前停在等待谷米阶段审计。
- **已完成范围**：
  1. 独立仓库 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 已从 `KKKKhazix/AIHOT`（commit `c8704e5313e6b051560365226b3919d7e0ada5ea`）克隆落盘，上游原版 `README.md` 与 `AGENTS.md` 已备份至 [`docs/upstream/`](docs/upstream/)；
  2. 完成交接级 [`README.md`](README.md)、[`AGENTS.md`](AGENTS.md)、[`docs/实施与验收计划.md`](docs/实施与验收计划.md)；
  3. **`SH-01` 已完工并通过谷米审计（[`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md)）**：`site/site.ts`（站名 `YM-HOT`、行业词「A股短线」、`http://localhost:3088`、早刊 `08:30`、MCP 前缀 `ymhot`、`reasonLabel=短线看点`）、`.env.example` 与 `docker-compose.yml`/`Dockerfile`/`deploy/Caddyfile` 端口默认改 `3088`、安全阀置 `false`；`industry/taxonomy.ts` 6 大分类 + 12 分类标签 + 16 题材/战法标签 + 9 主体、`industry/topics.json` 28 主题、`industry/sources.json` 4 个 `external` 占位信源、`industry/prompts/*.md` 短线化改造，以及 39 个前后端测试文件适配全部通过；
  4. **Grok 三波调研弹药库已验收入库（[`docs/aihot_research/`](docs/aihot_research/INDEX.md)）**：包含实测东财/淘股吧/雪球 Endpoints（[`endpoints.json`](docs/aihot_research/endpoints.json)）、33 个淘股吧游资名录（[`tgb.json`](docs/aihot_research/tgb.json)）、23 个雪球深度作者（[`xueqiu.json`](docs/aihot_research/xueqiu.json)）、28 个核心短线题材与股票黑话字典（[`dict/themes.json`](docs/aihot_research/dict/themes.json)）、7401 贴回测的情绪与反水贴正则词典（[`dict/sentiment_dict.json`](docs/aihot_research/dict/sentiment_dict.json)）及 70 条 SelectBench 金标集（[`gold/gold.jsonl`](docs/aihot_research/gold/gold.jsonl)）。
  5. **`SH-02` 已实施交付（待审计）**：`packages/backend/src/ingest/items.ts` 增加可选 `bodyText`/`excerpt` 透传（非空即落 `body_status='ok'`，不再对 WAF/合成 URL 二次抓取）；新增 `bridge/` 包（`pipeline_loader` 焦点股池与题材身位、`sentiment_engine` 反水贴与三态情绪/15m 盖楼/跨平台共振、`collectors/` 东财+淘股吧+雪球靶向采集、`push_to_aihot` 双轨推送与快照、`run_bridge` CLI）；离线 fixtures 与 51 项单测全绿，`.data/short-term-radar-snapshot.json`（梯队 + 共振 Top 30）与 `.data/gold.jsonl`（70 条）已生成。
- **尚未完成**：`SH-02` 阶段审计；`SH-03` 的代码开发、测试验证与阶段审计。
- **下一步唯一任务**：**谷米**执行 [`docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md`](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) 的阶段审计（证据索引 `docs/evidence/sh02-20261016/manifest.json`）；审计通过前稳米不跨阶段施工。

## 有效边界与决定

- **协作模式（2026-10-16 弈沐拍板）**：**谷米**负责规划、写开工单与阶段审查；**稳米**负责按单实施。**完成一个阶段、审计一个阶段**，未获上一阶段审计通过前不跨阶段施工。
- **独立工程边界（2026-10-16 弈沐拍板）**：作为 `YM_Capital` 下的独立项目建设，不与 `live-dashboard`（8088）混用代码、数据库或端口；本站默认端口为 `3088`。
- **数据源与第一批社区范围（2026-10-16 弈沐拍板）**：
  - 结构化热榜（同花顺 `ths_hot`、东财 `dc_hot`）、涨跌停池 (`market_intraday_state`)、开盘啦题材 (`kpl_list`/`kpl_concept`)、同花顺涨停原因 (`limit_list_ths`) 统一在 `SH-02` 通过 `/Users/yimu/Projects/YM_Capital/YM-data-pipeline` 公共入口读取；
  - 第一批社区评论范围固定为：**① 东方财富股吧**（免 Cookie `gbapi` 接口 + 本地按阅读/评论热度重排）、**② 淘股吧 TGB**（移动端 `m.tgb.cn/getMZh` + `/jinghua/1-1` + `/ticai/ranking` + `tgb.json` 实盘游资提权）、**③ 雪球**（匿名 Cookie 预热 + `hot_stock` + `symbol/search/status` + `xueqiu.json` 深度作者提权）。
- **产品视图与运行频率（2026-10-16 弈沐拍板）**：
  - 在 `SH-03` 通过 `modules/short-term-radar/` 实现双视图切换：默认 **「🧩 题材主线梯队视图」**，一键切换 **「🔥 跨平台人气共振 Top 30 榜」** + 个股社区舆情侧滑抽屉；
  - 交易时段每 10~15 分钟滚动刷新热榜与评论流速，盘前（08:30）与盘后（15:35）生成深度汇总。
- **站点与分类口径（2026-10-16 SH-01 实施落地）**：站点身份 `YM-HOT`、默认端口 `3088`、早刊 `08:30`；行业分类固定为 6 个（题材/龙头/实锤/逻辑/复盘/舆情），其中后三类为评论类（`commentary`）。
- **本地开发环境事实（2026-10-16 SH-01 核对）**：Node 用 Homebrew `v26.11.0`（`/opt/homebrew/bin/node`）；本地 PostgreSQL 由 `@embedded-postgres/darwin-arm64` 提供（监听 `127.0.0.1:5432`）。
- **桥接口径（2026-10-16 SH-02 实施落地）**：`bridge/` 只做「取数 → 判情绪 → 推送」，不调付费模型、不写前端页面；采集器一律「解析为纯函数 + HTTP 可注入」，因此自动化测试 100% 走 `bridge/tests/fixtures/`（在线冒烟另有 `--live-smoke --max-stocks 3` 手动开关）；`YM-data-pipeline` 在线取不到数是常态（实测 `market_hot_rank` 返回 `status=empty`），桥接如实记进快照 `dataQuality` 并用 28 题材代表股兜底，绝不静默产出空榜；`docs/aihot_research/dict/sentiment_dict.json` 的单字/泛词（「核」「面」「出货」「一字」等）在本仓额外加了语境门控，否则雪球深度长文里的「出货节奏」会被误判成恐慌出逃。

## 未完成队列

| ID | 状态 | 下一动作 / 退出条件 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `done` | **【已通过谷米审计】基座环境与 A 股短线 KnowHow 改造**：`site/`、`industry/` 与 39 个测试文件适配完成，`npm run typecheck`、架构门禁、种子导入及前端构建测试全部通过。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [谷米审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) |
| `SH-02` | `delivered_pending_audit` | **【已交付，待谷米审计】`YM-data-pipeline` 桥接与三大社区靶向采集 (`bridge/`)**：S1~S5 全做完——ingest 正文透传 + 单测、焦点股池与黑话映射、System 1 情绪与反水贴引擎、三社区采集器、双轨推送与雷达快照、70 条金标同步；51 项离线单测、端到端演练、`npm run typecheck` 与 `ingest/provenance/architecture` 测试全部 exit 0。 | [SH-02 开工单](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) · [证据](docs/evidence/sh02-20261016/manifest.json) |
| `SH-03` | `queued` | **`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：待 `SH-02` 审计通过后由谷米签发细化单。实现模块数据库迁移、API、题材主线梯队 ⇄ Top 30 人气共振双视图、个股舆情抽屉及盘中 15m 调度，完成 `smoke.ts` 端到端验收。 | [实施与验收计划 §SH-03](docs/实施与验收计划.md) |
| `SH-04` | `backlog` | **二期扩展**：接入韭研公社题材逻辑帖、用 `.data/gold.jsonl`（70 条已就位）跑 `eval-selection.ts` 校准门槛、联动游资龙虎榜 (`hm_detail`) 与互动易 (`irm_qa`)。 | [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 最近记录

- **2026-10-16 15:18 CST | `SH-01` 审计通过 & `SH-02` 开工单签发 | 谷米**
  - **结果**：独立复核稳米交付的 `965bbff`/`8c49fda`，复跑 `npm run typecheck`、重建干净 `ymhot_test` 模板库跑核心与架构测试（64/64 全过）、验证 `scripts/seed.ts`（4 个 `external` 信源成功入库），出具 [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) 判定 `SH-01` 一次通过；同时验收纳管 Grok 交付的 [`docs/aihot_research/`](docs/aihot_research/INDEX.md)，签发 [`docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md`](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md)。
  - **下一步**：交稳米执行 `SH-02` 开工单。

- **2026-10-16 15:05 CST | `SH-01` 实施交付 | 稳米**
  - **结果**：按 `SH-01` 开工单完成 S1~S5——`site/site.ts`、`.env.example` 与 `docker-compose.yml`/`Dockerfile`/`deploy/Caddyfile` 端口默认改 `3088`，安全阀置 `false`；`industry/taxonomy.ts`、`industry/topics.json`、`industry/sources.json`、`industry/prompts/` 短线化改造，并完成 34 个测试文件适配。
  - **验证范围**：`npm run typecheck` exit 0；`npm test` 731 项通过、新增失败 0；前端 `apps/web/tests/*.test.ts` 56/56 通过。

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / `SH-01` 结项 | [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) | 完成 AIHOT 站点与 A 股短线 6 大分类/提示词/测试适配，谷米独立复测通过。 |
| 2026-10-16 / 基线建立 | [`docs/upstream/`](docs/upstream/) · [`docs/实施与验收计划.md`](docs/实施与验收计划.md) | 克隆 AIHOT 上游 `c8704e5`，确立三阶段（`SH-01`~`SH-03`）滚动开发与谷米审计机制。 |

- **2026-10-16 15:45 CST | `SH-02` 实施交付 | 稳米**
  - **结果**：按 `SH-02` 开工单完成 S1~S5。S1 在 `ingest/items.ts` 增加可选 `bodyText`/`excerpt`（非空才生效，不传保持 `body_status='pending'`），`tests/ingest.test.ts` 补一条单测验证「透传即 `ok` 且排 `analyze` 队列、无正文仍 `pending`」；S2~S5 新增 `bridge/` 包：焦点股池合成（热榜 + 盘中池 + 28 题材词典，算身位与黑话映射）、System 1 情绪引擎（14 条水贴正则 + 三态情绪 + 语境修正 + 15m 盖楼 + 跨平台共振分）、东财/淘股吧/雪球三采集器（游资与深度作者提权）、双轨推送（editorial 三轨带正文、`hot_signal` 只带摘要）与雷达快照 CLI。
  - **验证范围**：bridge 离线单测 51/51；`--offline-fixtures --sync-gold --dry-run` exit 0，产出 18 个题材梯队 + 共振 Top 30 + 70 条金标；`npm run typecheck` exit 0；`ingest/provenance/architecture` 21/21 通过；`git diff --check` 干净、无硬编码密钥。证据见 `docs/evidence/sh02-20261016/`。
  - **实施中发现并修正的三个真问题**：① 同一 `post_id` 会被多只票重复采集，热度虚高 → 采集器与离线样本都按票过滤/去重；② 情绪主类原按「带符号和」比较，导致「跌停+核按钮+被埋」的帖被蹭到的「板上」翻成看多 → 改按强度绝对值比较并做最长匹配去重；③ 词典把「出货」标为无条件生效，实测误伤雪球深度长文 → 增加语境门控并留痕。
  - **下一步**：交谷米执行 `SH-02` 阶段审计；审计通过前不跨阶段开 `SH-03`。
