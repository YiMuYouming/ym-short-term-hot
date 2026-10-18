# LITE-03 阶段独立审计报告（谷米 · 一次通过）

- **审计结论**：✅ **PASS（一次通过，批准推进 `LITE-04` 前端密度、缺失值诚实化与抽屉交互精修）**
- **审计单号**：`AUDIT-LITE03-20261017-R1`
- **审计时间**：2026-10-17 20:33 CST
- **审计人**：谷米（PM / 规划与审查 Agent）
- **实施人**：稳米（CodeBuddy · `step-5-preview`）

---

## 一、 核心交付核验（对照 `LITE-03` 开工单 5 项要求）

1. **`top_resonance_limit` 与 CLI 默认对齐 50**：
   - `bridge/config.py` 将 `top_resonance_limit` 默认值从 `30` 改为 `50`；
   - `bridge/run_bridge.py` 额外修复了 CLI `--top` 默认值 `30` 静默覆盖 `config` 默认值的问题（改为 `default=None`），使得无参干跑直接产出完整的 `50` 只共振股。
2. **社区高亮复用 `StockMatcher.group` + 单帖字段全量透传 + 采集器时间兼容**：
   - `bridge/run_bridge.py` 将 `StockMatcher.group` 的归股结果 `posts_by_code` 直接传入 `build_snapshot` 与 `build_theme_ladders`，淘股吧/雪球中只提股票名或黑话别名而无显式 6 位代码的帖子已进入个股 `highlights`；
   - `bridge/push_to_aihot.py` 新增 `serialize_highlights`，完整输出 `postId`、`source`、`platform`、`title`、`content`、`url`、`author`、`publishedAt`、`commentCount`、`likeCount`、`viewCount`、`isKol`、`qualityTier`、`sentiment`、`sentimentScore`、`sentimentTerms`；
   - `bridge/collectors/eastmoney_guba.py` 修复了股吧接口 `post_publish_time` 由毫秒整数变为 `"YYYY-MM-DD HH:MM:SS"` 字符串导致 `publishedAt` 丢失的问题，真实快照 139 条热帖 `publishedAt` 覆盖率达 **139/139（100%）**，单帖情绪分布为 `bull: 25, bear: 10, divergence: 2, neutral: 102`（彻底告别全员 `neutral`）。
3. **情绪打分分句否定前缀修正（`bridge/sentiment_engine.py`）**：
   - 新增 `NEGATION_PREFIXES` / `NEGATION_CHARS` / `CLAUSE_BREAKS` 与 `_negated_before` 检测，当正向词前方同一分句内出现否定修饰时不再计入看多正分、改记负分；
   - 实测 `"我认为周一冰山无法继续涨停，原因如下"` 从原先误判 `bull` 修正为 `bear`，且 `"未来"` 等词不会误触发单字 `"未"` 否定。
4. **板块同义词归并、事件词剥离与梯队统计修正**：
   - `docs/aihot_research/dict/themes_v2.json` 与 `bridge/pipeline_loader.py` 完成了同义板块合并（`共封装光学(CPO)`、`飞行汽车(eVTOL)`、`PCB概念`、`黄金概念`、`铜缆高速连接` 全部归并），移除泛词 `"机器人"` 误绑；
   - 新增 `is_event_or_company_tag` 剥离个股公告/事件/股权/车型词（`三部门联合调查`、`复牌`、`尊界V800`、`界面财联社重组`、`参股锴威特半导体` 已全部从板块名消失，仅保留在个股 `limitReason`/`whyHot`）；
   - 四级兜底链确保 50 只焦点股板块归属率 **50/50（100%）**，板块梯队从 `115` 收敛至 `102`；
   - `bridge/run_bridge.py` 修正 `limitUpCount`（同义子标签取 `max` 不重复累加）与 `_leader_stock`（有正涨幅时优先按涨跌幅选真领涨股，消除“领涨 芒果超媒 -3.67%”）。
5. **前端契约全字段无损映射（`modules/short-term-radar/contracts.ts`）**：
   - `mapSnapshot` 对 `themeLadders[].stocks` 统一走 `mapStock` 完整映射，第 31~50 名梯队股完整保留 `changePct`、`amountYi`、`hotRankThs`、`hotRankDc`、`sentiment`、`highlights`；
   - `mapHighlight` 支持 camelCase 与 snake_case 双读。

---

## 二、 门禁与真实快照核验结果

- `python3 -m unittest discover -s bridge/tests -p "test_*.py" -v` → **77/77 PASS（纯离线）**
- `npm run typecheck` & `npm run build -w @aihot/web` → **Exit 0（零报错）**
- `node --test tests/architecture.test.ts modules/short-term-radar/tests/radar.test.ts modules/short-term-radar/scripts/radar-page.test.ts` → **19/19 PASS**
- 真实干跑快照 `.data/short-term-radar-snapshot.json` 与 `docs/evidence/lite03-20261017/live-snapshot-sample.json` → **50 只热门股 / 102 个板块梯队 / 139 条热帖 100% 带时间戳与单帖情绪**。
