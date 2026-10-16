# YM-ShortTerm-Hot · 当前进度

更新：2026-10-16 18:54（Asia/Shanghai）；状态依据：**第一期（Phase 1：`SH-01` → `SH-02` → `SH-03`）全链路开发与谷米终审已 100% 收官结项**；**Grok 第四~第六波二期调研弹药库已全部落盘入库（[`docs/aihot_research/INDEX.md`](docs/aihot_research/INDEX.md)）**；当前暂停休整，待额度恢复后直接启动第二期 `SH-04`

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-01 审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) · [SH-02 审计报告](docs/evidence/sh02-20261016/audit-by-gumi.md) · [SH-03 终审收官报告](docs/evidence/sh03-20261016/audit-by-gumi.md) · [Grok 六波调研总索引](docs/aihot_research/INDEX.md) · [进度维护规则](../shared/progress-workflow.md)

## 当前摘要

- **当前阶段**：**第一期（Phase 1：`SH-01` ~ `SH-03`）已全部完工并通过谷米独立审计收官（`done`）！Grok 第一~第六波全量调研数据已全部提交入库！** 当前停机保额度，下次恢复后直接由谷米签发 **`SH-04`（第二期：真实盘中字段对齐 + 60 题材 v2 切换 + 龙虎榜量化/游资席位识别 + 韭研公社/快讯 + 海外映射）**。
- **已完成范围**：
  1. **`SH-01`（`done`）**：基座环境与 A 股短线 6 大分类/提示词/39 个测试文件适配（[`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md)）；
  2. **`SH-02`（`done`）**：`YM-data-pipeline` 焦点股池桥接、三社区（东财股吧/淘股吧/雪球）靶向采集、System 1 反水贴与三色情绪引擎、四轨跨语言入库契约（[`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md)）；
  3. **`SH-03`（`done`）**：`@aihot/short-term-radar` 扩展模块（[`modules/short-term-radar/`](modules/short-term-radar/)）——四条雷达 API + Agent/MCP `get_radar` 能力 + 前端 **「🧩 题材主线梯队 ⇄ 🔥 人气共振 Top 30」** 双视图看板 + 三色情绪温度条 + 右侧 **「个股社区舆情与游资逻辑侧滑抽屉」**（[`audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md)）；
  4. **Grok 六波调研弹药库全部就位（[`docs/aihot_research/INDEX.md`](docs/aihot_research/INDEX.md)）**：
     - 第一~三波：淘股吧 33 人 / 雪球 23 人 / X 28 账号、28 题材 `themes.json` + 169 词 `sentiment_dict.json`、70 条 `gold.jsonl`；
     - **第四波（`docs/aihot_research/seats/`）**：`quant_seats.json`（27 个量化/外资/PB 席位 + 假机构识别模式，基于近 1 年东财龙虎榜实测统计）+ `youzi_seats.json`（37 条主观游资/一日游/散户大本营）+ 算法判据指南；
     - **第五波（`docs/aihot_research/jiuyan_cls/`）**：韭研公社与财联社/选股宝/同花顺 7×24 快讯 27 条实测接口 `fast_news_endpoints.json` + 韭研公社高赞作者库 `jiuyan_authors.json`；
     - **第六波（`docs/aihot_research/global_mapping/` & `dict/themes_v2.json`）**：跨市场「海外催化 → A股题材与龙头」传导字典 `overseas_to_ashare.json` + 扩充并经东财接口核验的 60 大高频题材库 `dict/themes_v2.json`。
- **尚未完成（下次恢复后 `SH-04` 直接做）**：
  1. **真实盘中数据 3 处字段对齐（18:50 Live Smoke 实测发现）**：
     - `YM-data-pipeline` 的 `market_intraday_state` 返回的 `data.limit_up` 行字段名为 `board`（连板数）、`pct`（涨跌幅）、`industry`（所属行业）、`seal_time`（封板时间），需在 [`bridge/pipeline_loader.py`](bridge/pipeline_loader.py#L373-L409) 的 `_first()` 中把 `"board"`、`"pct"` 加进候选键，并在词典未命中时用 `row.get("industry")` 兜底题材（避免新涨停股落入“未归题材”）；
     - 将 [`bridge/config.py`](bridge/config.py) 的题材词典路径从 `dict/themes.json`（28 题材 74 股）切换升级为 Grok 第六波刚交付的 `dict/themes_v2.json`（60 题材 200+ 股）；
     - 雪球 `status.json` 实时抓取补齐首页预热 Cookie（或走浏览器/移动端免 WAF 端点），以及当 `market_hot_rank` 当日为空时用东财股吧人气榜/涨停池热度兜底。
  2. **接入龙虎榜量化席位 vs 游资识别（`seats/quant_seats.json` + `youzi_seats.json`）、韭研公社/快讯（`jiuyan_cls/`）与海外映射（`global_mapping/`）**。

## 阶段队列

| ID | 状态 | 阶段成果 / 下一动作 | 依据 |
| --- | --- | --- | --- |
| `SH-01` | `done` | **【已结项】基座环境与 A 股短线 KnowHow 改造**：`site/`、`industry/` 与 39 个测试文件适配完成。 | [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [谷米审计报告](docs/evidence/sh01-20261016/audit-by-gumi.md) |
| `SH-02` | `done` | **【已结项】`YM-data-pipeline` 桥接与三大社区靶向采集 (`bridge/`)**：56 项 Python 单测 + 四轨跨语言入库契约（41/41 入库，`backfill=0`）全部绿灯。 | [SH-02 开工单](docs/开工单-SH02-数据管道桥接与三社区采集-2026-10-16.md) · [谷米复审报告](docs/evidence/sh02-20261016/audit-by-gumi.md) |
| `SH-03` | `done` | **【已结项 · 第一期收官】`@aihot/short-term-radar` 双视图模块与端到端联调 (`modules/short-term-radar/`)**：4 条架构红线、56 项 Python 单测、`typecheck`、`web build`、5 项模块 API 单测与 2 项真实 SSR 端到端测试全部绿灯，梯队矛盾清零（`27 → 0`）。 | [SH-03 开工单](docs/开工单-SH03-双视图短线雷达模块与端到端联调-2026-10-16.md) · [谷米终审报告](docs/evidence/sh03-20261016/audit-by-gumi.md) |
| `SH-04` | `ready_next` | **【待额度恢复后启动】第二期扩展与真实盘中深度对齐**：① 对齐 `market_intraday_state` 的 `board`/`pct`/`industry` 字段并切换 `dict/themes_v2.json`；② 接入 `seats/quant_seats.json` + `youzi_seats.json` 实现个股「🤖 量化席位浓度 vs 🦁 顶级游资主封」标签；③ 接入 `jiuyan_cls/` 快讯与 `global_mapping/overseas_to_ashare.json` 海外映射。 | [Grok 六波调研总索引](docs/aihot_research/INDEX.md) · [实施与验收计划 §二期](docs/实施与验收计划.md) |

## 本地快速启动看板命令（随开随看）

```bash
# 1. 在项目根目录生成快照（离线样本或 --live-smoke）
cd /Users/yimu/Projects/YM_Capital/ym-short-term-hot
python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run

# 2. 启动 API (3089) + Web (3088)
PATH="/opt/homebrew/bin:$PATH" DATABASE_URL=postgres://127.0.0.1:5432/ymhot_dev \
  API_PORT=3089 WEB_PORT=3088 API_BASE_URL=http://127.0.0.1:3089 INGEST_TOKEN=ymhot-local-dev-token \
  sh -c 'node apps/api/src/main.ts & node apps/web/server.ts'

# 3. 浏览器打开
open http://127.0.0.1:3088/radar
```

## 历史索引

| 日期 / 阶段 | 归档与证据 | 该批结论 |
| --- | --- | --- |
| 2026-10-16 / Grok 第四~六波入库 | [`docs/aihot_research/INDEX.md`](docs/aihot_research/INDEX.md) | 完成 27 量化席位 + 37 游资席位（含 1 年龙虎榜统计）、韭研公社与快讯 27 端点、海外映射与 60 题材 `themes_v2.json`。 |
| 2026-10-16 / `SH-03` 结项（一期收官） | [`docs/evidence/sh03-20261016/`](docs/evidence/sh03-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh03-20261016/audit-by-gumi.md) | 完成 `@aihot/short-term-radar` 双视图模块、舆情侧滑抽屉、Agent/MCP 能力及全链路契约验证，谷米二次终审通过。 |
| 2026-10-16 / `SH-02` 结项 | [`docs/evidence/sh02-20261016/`](docs/evidence/sh02-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh02-20261016/audit-by-gumi.md) | 完成 `bridge/` 焦点股池、三社区采集、System 1 情绪引擎及四轨跨语言契约对齐，谷米二次复审通过。 |
| 2026-10-16 / `SH-01` 结项 | [`docs/evidence/sh01-20261016/`](docs/evidence/sh01-20261016/) · [`audit-by-gumi.md`](docs/evidence/sh01-20261016/audit-by-gumi.md) | 完成 AIHOT 站点与 A 股短线 6 大分类/提示词/测试适配，谷米独立复测通过。 |
