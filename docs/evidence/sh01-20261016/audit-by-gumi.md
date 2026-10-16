# SH-01 阶段独立审计报告（谷米）

- **审计单号**：`AUDIT-SH01-20261016`
- **被审提交**：`965bbff2256595f2fb0fa2cb64568eb9f2d94192`（代码与证据） / `8c49fda2cb5df0788412f61bf2a3bf1f7ef202cf`（证据清单）
- **审计人**：谷米（规划与审查 Agent）
- **实施人**：稳米（实施 Agent）
- **审计时间**：2026-10-16 15:15 CST
- **审计结论**：✅ **PASS（一次通过，准予结项并放行 `SH-02`）**

---

## 一、 范围与红线审计（Scope & Boundary Check）

| 审计项 | 要求 | 实测结果 | 结论 |
| :--- | :--- | :--- | :--- |
| **工程物理隔离** | 严禁触碰 `/Users/yimu/Projects/YM_Capital/live-dashboard` 或其他子仓库 | `git diff 153b460..8c49fda --name-only` 共 67 个文件，100% 位于 `ym-short-term-hot` 内 | ✅ 通过 |
| **端口与安全阀** | 默认端口改 `3088`（避开 `8088`）；`COLLECT_ENABLED` / `MODEL_CALLS_ENABLED` 默认 `false` | `site/site.ts`、`.env.example`、`docker-compose.yml`、`Dockerfile`、`deploy/Caddyfile` 均已对齐 `3088`，两道安全阀均置 `false` | ✅ 通过 |
| **禁止跨阶段抢跑** | 本阶段不写 `bridge/`（`SH-02`）、不写 `modules/short-term-radar/`（`SH-03`）、不改 `packages/backend` 通用核心 | `packages/`、`apps/api`、`apps/worker`、`apps/web/app` 零改动，严格守住 `SH-01` 边界 | ✅ 通过 |

---

## 二、 S1 ~ S5 交付质量逐项核验

1. **S1 站点身份 (`site/site.ts`)**：
   - `EDITION_TIMES` 设为 `{ daily: "08:30", weekly: "10:00", monthly: "10:30" }`；
   - `SITE.name = "YM-HOT"`、`SITE.subject = "A股短线"`、`SITE.defaultUrl = "http://localhost:3088"`、`SITE.mcpPrefix = "ymhot"`、`ITEM_COPY.reasonLabel = "短线看点"`；
   - `ABOUT`、`REPORTS`、`CARDS`、`AGENT` 文案均已自然切换为 A 股短线题材与社区舆情语境。
2. **S2 分类与词表 (`industry/taxonomy.ts` & `industry/topics.json`)**：
   - 6 大分类 `theme-catalyst` / `dragon-move` / `company-signal` / `deep-logic` / `youzi-review` / `sentiment-pulse` 严格按开工单落盘，后三类标 `commentary: true`；
   - `ITEM_TYPES` 7 类、`CATEGORY_TAGS` 12 个、`TOPIC_TAGS` 16 个、`ENTITY_TAGS` 9 个、`ENTITIES` 9 个、`IDENTITY_LEXICON` 9 条正则守卫完整；
   - `industry/topics.json` 三组 28 个主题与 `taxonomy.ts` 完全对齐。
3. **S3 初始信源 (`industry/sources.json`)**：
   - 4 个 `external` 占位信源（`external-ym-pipeline` 为 `T1`/`editorial`、`external-eastmoney-guba` 为 `T2`/`hot_signal`、`external-taoguba-hot` 为 `T2`/`editorial`、`external-xueqiu-hot` 为 `T2`/`editorial`）；
   - 谷米独立在临时测试库实测 `node scripts/seed.ts`，输出 `sources: 4 added, 0 already there`，退出码 0。
4. **S4 提示词体系 (`industry/prompts/*.md`)**：
   - `prefilter.md`、`selection-score.md`、`content-understanding.md`、`structure.md`、`rules-domain.md` 五份主提示词及 6 份配套提示词完成短线化；
   - 7 类 `ITEM_TYPES` 五轴权重表每行和均为 10，输入占位符 `{{...}}` 与 JSON 输出契约未改动。
5. **S5 测试套件适配 (`tests/` & `apps/web/tests/`)**：
   - 35 个后端测试与 4 个前端测试仅替换旧示例行业的分类 key、标签、主体与 08:30 告警时间偏移（`10:35`），未删减测试条数、未弱化断言。

---

## 三、 谷米独立复测门禁结果

1. **TypeScript 类型检查**：
   - 谷米复跑 `PATH="/opt/homebrew/bin:$PATH" npm run typecheck` → **Exit 0**（7 个 tsconfig 工程全绿）。
2. **核心与架构测试复跑**：
   - 谷米重建干净模板库 `ymhot_test` 后独立运行：
     `node --test-global-setup=tests/databases.ts --import ./tests/databases.ts --test tests/architecture.test.ts tests/analyze.test.ts tests/category-corrections.test.ts tests/topics.test.ts tests/pool-relevance.test.ts tests/daily-report-alerts.test.ts tests/content-publication.test.ts tests/topics-withdrawal.test.ts tests/reading.test.ts`
   - 结果：**64 / 64 全部通过（fail 0）**，其中 `tests/architecture.test.ts` 8 项架构不变量全部通过。
   - 核查稳米全量跑分 `docs/evidence/sh01-20261016/test.txt`（731 通过）与 `baseline-failures.txt`（14 项沙箱环境失败与上游 `c8704e5` 1:1 一致，新增失败 0）。
3. **前端 SSR 构建与测试**：
   - 核验 `docs/evidence/sh01-20261016/web-build-test.txt`，56 / 56 通过（fail 0）。

---

## 四、 审计放行指令

- `SH-01` 正式标记为 **`done`**。
- 谷米同步将 Grok 完成的 `docs/aihot_research/` 调研资产（实测三社区 Endpoints、33 个淘股吧游资名录、23 个雪球深度作者、28 个短线题材与黑话字典、7401 贴校准的散户情绪与水贴正则词典、70 条 SelectBench 金标集）纳入版本库，并签发下一阶段开工单：
  👉 [`docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md`](../../开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md)。
