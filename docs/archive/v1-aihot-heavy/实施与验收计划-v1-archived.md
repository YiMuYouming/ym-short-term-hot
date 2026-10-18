# YM-ShortTerm-Hot · 实施与验收计划

[项目入口](../README.md) · [当前进度](../PROGRESS.md) · [Agent 规范](../AGENTS.md)

## 1. 总体路线与分期边界

本项目以开源框架 [`KKKKhazix/AIHOT`](https://github.com/KKKKhazix/AIHOT)（基线 `c8704e5313e6b051560365226b3919d7e0ada5ea`）为底座，结合 [`YM-data-pipeline`](../../YM-data-pipeline/README.md) 的 A 股统一行情/热榜/开盘啦/涨停池能力，构建独立的**弈沐 A 股短线热点与社区舆情聚合分类平台**。

遵循**「谷米规划开单与阶段审计 + 稳米按单实施」**机制，第一期（Phase 1）拆分为三个严格顺序推进、逐阶段审计的阶段（`SH-01` → `SH-02` → `SH-03`），二期（`SH-04`）作为后续演进储备。

---

## 2. 第一期（Phase 1）三阶段拆解与验收矩阵

| 阶段单号 | 阶段名称 | 核心交付范围 | 退出门禁（稳米自检 + 谷米审计） |
| :--- | :--- | :--- | :--- |
| **`SH-01`** | **基座打通与 A 股短线 KnowHow 改造** | 1. 跑通 AIHOT 本地依赖与 `_test` 数据库基线；<br>2. 完成 `site/site.ts`（站名 `YM-HOT`、端口 `3088`、早刊 `08:30`、安全阀默认关闭）；<br>3. 完成 `industry/taxonomy.ts`（6 大短线分类、连板/题材标签词表、平台与机构实体）、`industry/topics.json`、`industry/sources.json`；<br>4. 完成 `industry/prompts/*.md` A 股短线五维评分与结构化提示词改造；<br>5. 同步更新 `tests/` 中引用旧示例分类/标签/实体的断言。 | 1. `npm run typecheck` 零错误；<br>2. `DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test npm test` 全绿（含 `tests/architecture.test.ts`）；<br>3. `npm run build -w @aihot/web && node --test apps/web/tests/*.test.ts` 全绿；<br>4. 交付 `docs/evidence/sh01-20261016/manifest.json` 并停待谷米审计。 |
| **`SH-02`** | **`YM-data-pipeline` 桥接与三大社区采集器 (`bridge/`)** | 1. 建立 `bridge/` Python 包，只读调用 `YM-data-pipeline`（`market_hot_rank` 同花顺/东财热榜、`market_intraday_state`、`stocktoday_data` 的 `kpl_list`/`limit_list_ths`/`limit_step`），合并产出当日 Top 25~40 核心焦点股池与题材身位骨架；<br>2. 实现 **东方财富股吧**（实时评论流 + 15m/60m 盖楼流速计算）、**淘股吧 TGB**（24h 热帖榜 + 焦点股跟帖）、**雪球**（热股讨论榜 + 高赞长评）三大靶向采集器；<br>3. 实现水帖过滤、分歧度/多空观点提炼（带 SHA-256 缓存）及向 AIHOT `/api/ingest/items` 的双轨推送（长文 `editorial` vs 短评脉冲 `hot_signal`）。 | 1. `cd bridge && uv run python -m unittest discover -s tests -v` 全绿（纯离线 fixture，0 外部网络请求）；<br>2. StockToday 预算单轮查询 $\le 5$ 次，单源超时/限流显式记录 `source_gap`，不补零、不中断；<br>3. 对本地测试实例验证 `/api/ingest/items` 推送与 `editorial`/`hot_signal` 入库幂等性；<br>4. 交付 `docs/evidence/sh02-*/manifest.json` 停待谷米审计。 |
| **`SH-03`** | **`@aihot/short-term-radar` 双视图模块与端到端联调** | 1. 在 `modules/short-term-radar/` 实现模块路由 (`module.ts`)、专属表迁移 (`migrations/0001_radar_tables.sql`)、后端 API 与定时任务 (`server.ts`)；<br>2. 在 `web.tsx` 实现双视图切换：默认 **「🧩 题材主线梯队视图」**（空间龙/弹性龙/中军/跟风 + 分歧状态胶囊） ⇄ 一键切换 **「🔥 跨平台人气共振 Top 30 榜」** + **个股社区舆情侧滑抽屉**；<br>3. 配置交易时段每 15 分钟增量轮询与 08:30/15:35 汇总机制。 | 1. 模块单测、后端全量测试、前端 SSR 构建测试全绿；<br>2. 本地 `3088` 端口运行 `node scripts/smoke.ts --base http://localhost:3088` 及 `/radar` 双视图渲染回读通过；<br>3. 交付 `docs/evidence/sh03-*/manifest.json` 停待谷米终审。 |

---

## 3. 二期（Phase 2 / `SH-04`）演进储备（不在一期施工）

1. **韭研公社与选股宝扩展**：接入带持久化 Cookie 会话的韭研公社题材异动逻辑贴采集；
2. **SelectBench 金标校准**：采集 100~200 条真实短线热帖与评论构造 `.data/gold.jsonl`，运行 `scripts/eval-selection.ts` 校准 `industry/selection.ts` 入选门槛；
3. **龙虎榜游资与互动易深度联动**：在个股舆情抽屉内联动展示 `hm_detail`（知名游资席位买卖）与 `irm_qa_sh`/`irm_qa_sz`（董秘互动易最新实锤回答）。
