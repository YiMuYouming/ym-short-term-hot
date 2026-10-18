# YM-ShortTerm-Hot · 当前进度（V2 极简减法重构）

更新：2026-10-17 21:45（Asia/Shanghai）；状态依据：**旧版 V1（`SH-01`~`SH-03` 复杂 AIHOT 外壳）已全部封存归档至 [`docs/archive/v1-aihot-heavy/`](docs/archive/v1-aihot-heavy/)；V2「极简减法重构」全部四阶段（`LITE-01`、`LITE-02`、`LITE-03`、`LITE-04`）均已通过谷米审计 PASS（完整收官，证据：[`docs/evidence/lite04-20261017/`](docs/evidence/lite04-20261017/manifest.json)）**

[项目入口](README.md) · [Agent 规范](AGENTS.md) · [V2 极简实施与验收计划](docs/实施与验收计划.md) · [Grok 调研词典索引](docs/aihot_research/INDEX.md) · [旧版 V1 归档](docs/archive/v1-aihot-heavy/)

## 当前摘要

- **当前定位与方向（V2 减法重构已收官）**：
  - 停止并归档旧版 V1 照搬 AIHOT 大楼的繁琐规划，**做极致减法**，回归直观、克制、一打开就知道怎么用的看盘工具；
  - 保留 `bridge/` 已跑通的 `YM-data-pipeline` 桥接与三社区（东财股吧/淘股吧/雪球）采集底座，砍掉冗余概念，**第一版只聚焦两个事情**：
    1. **热门板块视角**：按当日真实热度/涨停家数排热门板块 → 点开板块看到里面的热门股 → 点开热门股看到**它为什么火（涨停/热榜原因、连板、硬数据）+ 各社区平台对它的真实评价**；
    2. **热门股视角**：展示同花顺/东财等平台前 30~50 的热门股榜单 → 点开任意股票同样看**它为什么火 + 各社区平台评论**。
- **真实数据源摸底（2026-10-17 已实测验证通过）**：
  - `query("legacy_hot_rank")`：直接返回同花顺热点股（含 `reason` 涨停原因串，如 `"卫星通信芯片+低空经济"`）及 `reason_stats`（当日热门板块涨停家数排行）；
  - `query("market_intraday_state")`：返回真实 `trade_date` 与涨停池 `limit_up`（含 `board` 连板数、`pct`、`industry`、`seal_time`）；
  - `query("market_hot_rank", source="ths", trade_date=..., limit=50)`：传入最近交易日即可拿到同花顺热榜 Top 50，且每只票自带 **`rank_reason`（完整的「行业原因 + 公司原因」文本，直接回答“为什么火”）** 与 `concept` 概念标签；
  - `query("market_hot_rank", source="dc", limit=50)`：实时返回东方财富人气榜 Top 50。
- **`LITE-01` 数据底座已完工并通过谷米审计（2026-10-17，稳米实施 / 谷米 AUDIT-LITE01-R1 PASS）**：`bridge/` 切换 `themes_v2.json`（60 题材 + 别名归一），四源融合（ths/dc 热榜 + `legacy_hot_rank` 涨停原因归因 + `market_intraday_state` 涨停池）产出 50 只真实热门股，每只带 `limitReason`/`whyHot`/`sealTime`；热门板块按真实热度排序（归一后涨停原因统计 → 上榜热股数 → 涨停数 → 共振分）。真实干跑（dry-run 零推送）：ths/dc 各 100 行、涨停池 61 行、legacy 59 项 + 154 条板块统计，共振榜 50 只、梯队 115 组、未归题材 0、whyHot 48/50、社区帖 50/50。证据：[`docs/evidence/lite01-20261017/`](docs/evidence/lite01-20261017/manifest.json)（含谷米审计报告 [`audit-by-gumi.md`](docs/evidence/lite01-20261017/audit-by-gumi.md)）。
- **`LITE-02` 前端极简减法已完工并通过谷米审计（2026-10-17，稳米实施 / 谷米 AUDIT-LITE02-R1 PASS）**：`radar-route.tsx` 重写为「[🔥 热门板块] ⇄ [📈 热门股 Top 50]」双视角 + 共用个股详情抽屉——板块按热度排列、点板块出板块内热门股、Top 50 干净表格（排名/股票/涨跌连板/所属板块/为什么火/社区热度）、点任意股票抽屉置顶展示 `whyHot`/`limitReason` 与连板封板硬信息、下方按平台（全部/淘股吧/雪球/东财股吧）切换三社区真实评价；五分身位桶/身位筛选/搜索框按开工单砍掉（API 过滤与 agent 视图保留）。门禁：typecheck、web build、node 三文件合跑 17/17、3088 端口四路径实测 4/4、Python 65/65 全绿。证据：[`docs/evidence/lite02-20261017/`](docs/evidence/lite02-20261017/manifest.json)（含谷米审计报告 [`audit-by-gumi.md`](docs/evidence/lite02-20261017/audit-by-gumi.md)）。
- **`LITE-03` 数据语义与板块社区精修已完工并通过谷米审计（2026-10-17，稳米实施 / 谷米 AUDIT-LITE03-R1 PASS）**：共振榜默认 50 与焦点池对齐；`StockMatcher.group` 归股结果直通 highlights 与梯队桶，按名/黑话命中的淘股吧/雪球帖不再丢失，单帖全量透传 `postId`/`publishedAt`/`content`/`likeCount`/`viewCount`/`qualityTier`/四值 `sentiment`/`sentimentTerms`；`score_post` 增加句否定前缀修正；`themes_v2.json` 同义板块归并（59 题材）+ 事件/公司/车型词只留 `whyHot` 不建板块 + 四级兜底实现 50 股 100% 板块归属；板块涨停数取 `max` 去重、领涨按涨幅口径；`contracts.ts` 梯队股统一 `mapStock`。干跑：梯队 115→102 组、themes 50/50、publishedAt 139/139。证据：[`docs/evidence/lite03-20261017/`](docs/evidence/lite03-20261017/manifest.json)（含谷米审计报告）。
- **`LITE-04` 前端密度与抽屉交互精修已完工并通过谷米审计（2026-10-17，稳米实施 / 谷米 AUDIT-LITE04-R1 PASS）**：`radar-route.tsx` 重写——缺失值诚实化（`boardCount===1` 显示「首板」、连板股缺封板时间显示「封板时间待补」消灭「4 连板+未封板」矛盾、0 板涨幅够显示「涨停/待核连板」、降级显示「连板待补」、页头「交易日 2026-10-16 · 更新」）；视角 1 主线板块默认展示（102 组中 79 个单股长尾折叠进「展开其余 N 个单股异动概念」）+ 板块/成分股筛选框 + 负涨幅领头羊改称「代表」+ 成分股双行紧凑行（移除全宽情绪条）；视角 2 `table-layout:fixed` + colgroup 固定列宽 + 股票名原生 button 可键盘聚焦 + 板块胶囊 2 个 +`+N` + 小样本情绪条（有帖即真实三色比例、0 帖才灰占位）；抽屉上一只/下一只 + 键盘左右切换 + 切股自动重置平台筛选/滚回顶部 + whyHot 超 110 字折叠 + 平台 Tab 带计数 + 单帖情绪徽章/发布时间/正文摘要；清理未定义的 `--page-max-board` 与 `fadeIn/fadeOut`；顺带修复 LITE-03 后高亮帖情绪全部退化为「中性」的陈旧映射。门禁：Python 77/77、typecheck、web build、node 21/21、3088 七项 7/7 全绿。证据：[`docs/evidence/lite04-20261017/`](docs/evidence/lite04-20261017/manifest.json)（含谷米审计报告 [`audit-by-gumi.md`](docs/evidence/lite04-20261017/audit-by-gumi.md)）。

## 阶段队列（PM 谷米 ⇄ 实施 稳米）

| ID | 状态 | 阶段成果 / 下一动作 | 依据 |
| --- | --- | --- | --- |
| `LITE-01` | `done` | **已通过谷米审计（AUDIT-LITE01-R1 PASS）**：四源融合 + 真实热度板块排序 + `whyHot`/`limitReason`/`sealTime` + `contracts.ts` 透传；Python 65/65、typecheck、node 13/13、真实管道干跑全过。证据：[docs/evidence/lite01-20261017/](docs/evidence/lite01-20261017/manifest.json) | [LITE-01 开工单](docs/开工单-LITE01-极简热门板块与热股数据底座-2026-10-17.md) · [谷米审计](docs/evidence/lite01-20261017/audit-by-gumi.md) |
| `LITE-02` | `done` | **已通过谷米审计（AUDIT-LITE02-R1 PASS）**：极简双视角（热门板块 ⇄ 热门股 Top 50）+ 共用个股详情抽屉；typecheck / web build / node 17/17 / 3088 实测 4/4 / Python 65/65 全过。证据：[docs/evidence/lite02-20261017/](docs/evidence/lite02-20261017/manifest.json) | [LITE-02 开工单](docs/开工单-LITE02-前端极简双视角与个股详情重构-2026-10-17.md) · [谷米审计](docs/evidence/lite02-20261017/audit-by-gumi.md) |
| `LITE-03` | `done` | **已通过谷米审计（AUDIT-LITE03-R1 PASS）**：共振榜默认 50 + 高亮纳管无代码帖与单帖全字段 + 分句否定前缀修正 + 同义板块归并/事件词剥离/50 股 100% 板块归属 + 涨停数去重与领涨按涨幅 + `contracts.ts` 梯队股统一 `mapStock`；Python 77/77、node 19/19、3088 4/4、干跑 115→102 组/themes 50/50/publishedAt 139/139 全过。证据：[docs/evidence/lite03-20261017/](docs/evidence/lite03-20261017/manifest.json) | [LITE-03 开工单](docs/开工单-LITE03-数据语义与板块社区精修-2026-10-17.md) · [谷米审计](docs/evidence/lite03-20261017/audit-by-gumi.md) |
| `LITE-04` | `done` | **已通过谷米审计（AUDIT-LITE04-R1 PASS）**：缺失值诚实化（首板术语/封板时间待补/涨停待核/连板待补 + 页头交易日）、视角 1 主线默认展示与单股长尾折叠 + 筛选框 + 代表股改称 + 双行紧凑行、视角 2 固定列宽 + 股票 button 可聚焦 + 板块胶囊 2+N + 小样本情绪条、抽屉上一只/下一只与键盘导航 + 切股状态重置 + whyHot 折叠 + 平台 Tab 计数 + 单帖卡片升级 + CSS 变量/动画清理；Python 77/77、typecheck、web build、node 21/21、3088 七项 7/7 全绿。证据：[docs/evidence/lite04-20261017/](docs/evidence/lite04-20261017/manifest.json) | [LITE-04 开工单](docs/开工单-LITE04-前端密度与抽屉交互精修-2026-10-17.md) · [谷米审计](docs/evidence/lite04-20261017/audit-by-gumi.md) |

## 历史归档索引

| 日期 / 阶段 | 归档位置 | 说明 |
| --- | --- | --- |
| 2026-10-16 / 旧版 V1（`SH-01`~`SH-03`） | [`docs/archive/v1-aihot-heavy/`](docs/archive/v1-aihot-heavy/) · [`docs/evidence/`](docs/evidence/) | 旧版重型 AIHOT 外壳与三阶段开工单、进度记录已整体封存归档，不再作为当前迭代依据。 |
| 2026-10-17 / V2 `LITE-01`（数据底座，AUDIT-LITE01-R1 PASS） | [`docs/evidence/lite01-20261017/`](docs/evidence/lite01-20261017/manifest.json) | 四源融合 + 真实热度板块排序 + whyHot/limitReason/sealTime；谷米 AUDIT-LITE01-R1 一次通过。 |
| 2026-10-17 / V2 `LITE-02`（前端极简双视角，AUDIT-LITE02-R1 PASS） | [`docs/evidence/lite02-20261017/`](docs/evidence/lite02-20261017/manifest.json) | 双视角 + 共用详情抽屉；typecheck/web build/node 17/17/3088 实测 4/4 全过，谷米 AUDIT-LITE02-R1 一次通过。 |
| 2026-10-17 / V2 `LITE-03`（数据语义与板块社区精修，AUDIT-LITE03-R1 PASS） | [`docs/evidence/lite03-20261017/`](docs/evidence/lite03-20261017/manifest.json) | 五改造 + 采集器必要最小修；Python 77/77、node 19/19、3088 4/4、干跑 115→102 组/themes 50/50/publishedAt 139/139，谷米审计一次通过。 |
| 2026-10-17 / V2 `LITE-04`（前端密度与抽屉交互精修，AUDIT-LITE04-R1 PASS） | [`docs/evidence/lite04-20261017/`](docs/evidence/lite04-20261017/manifest.json) | 缺失值诚实化 + 主线折叠/筛选 + 固定列宽表格 + 抽屉导航/折叠/平台计数 + CSS 清理；Python 77/77、node 21/21、3088 七项 7/7，谷米审计一次通过。 |
