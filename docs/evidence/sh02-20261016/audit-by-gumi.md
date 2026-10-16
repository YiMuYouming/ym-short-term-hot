# SH-02 阶段独立审计报告（谷米 · 第一次审计）

- **审计单号**：`AUDIT-SH02-20261016-R1`
- **被审提交**：`411d694`（代码） / `57c44ad`（证据清单）
- **审计人**：谷米（规划与审查 Agent）
- **实施人**：稳米（实施 Agent）
- **审计时间**：2026-10-16 16:03 CST
- **审计结论**：❌ **REJECT / 需返工修补（发现 2 个跨语言契约阻断级 P0 缺陷 + 2 个 P1 缺陷，修完再放行 `SH-03`）**

---

## 一、 亮点肯定（保留，无需重写）

1. **Python 架构与算法质量高**：
   - `bridge/pipeline_loader.py`（焦点股池合成、28 题材与“易中天/寒王/宁王”黑话双向索引、`StockMatcher`）、`bridge/sentiment_engine.py`（14 条反水贴正则、最长匹配去重、绝对强度判主类、`GATED_TERMS` 防止雪球长文“出货”误判、`CONTEXT_RULES` 语境修正）、三大社区采集器及 `.data/short-term-radar-snapshot.json` 生成逻辑非常扎实；
   - 51 项 Python 离线单测全部通过（0.117s），`packages/backend/src/ingest/items.ts` 的 `bodyText`/`excerpt` 透传也已实现。

---

## 二、 必须返工修补的 4 个缺陷（根因与定位）

谷米在将 `bridge/push_to_aihot.py` 产出的真实 Payload 与 TypeScript 后端 `packages/backend/src/ingest/items.ts`、`packages/backend/src/lib/url.ts`、`packages/backend/src/content/materials.ts` 做跨语言契约对账时，抓出以下 **静默丢数/变质** 缺陷：

### 🔴 [P0 阻断缺陷 1] `pipeline_report_item` 使用 `ymhot://` 协议，被后端 `normalizeUrl()` 100% 静默丢弃（`created: 0`）
- **问题位置**：[`bridge/push_to_aihot.py`](../../../bridge/push_to_aihot.py#L77) 第 77 行：
  ```python
  url=f"ymhot://radar/stock/{stock.symbol}",
  ```
- **后端契约冲突**：
  - 后端 [`packages/backend/src/ingest/items.ts`](../../../packages/backend/src/ingest/items.ts#L56-L57) 第 56–57 行执行：
    `const url = normalizeUrl(rawUrl); if (!url || seen.has(url)) continue;`
  - 而 [`packages/backend/src/lib/url.ts`](../../../packages/backend/src/lib/url.ts#L15) 第 15 行强制校验：
    `if (u.protocol !== "http:" && u.protocol !== "https:") return null;`
  - 谷米实测：`normalizeUrl("ymhot://radar/stock/SZ300308")` 返回 **`null`**！这意味着 `external-ym-pipeline` 轨计划推送的 30 条焦点股战报在真实推送时会 **100% 被静默跳过（`created: 0`），一条都进不了数据库**！
- **修复要求**：
  - 将 `pipeline_report_item` 的 `url` 改为合法的 `https://` 地址，并带上交易日或批次日期参数（注意：参数名不能用 `from`/`source`/`ref` 等会被 `TRACKING_PARAMS` 剥除的词，可用 `date=YYYY-MM-DD`），例如：
    `https://quote.eastmoney.com/{stock.symbol.lower()}.html?date={trade_date}`
    这样既 100% 通过 `normalizeUrl()`，读者在前端点击战报卡片原文链接时还能直接打开该股行情页。

---

### 🔴 [P0 阻断缺陷 2] `pipeline_report_item` 与 `community_item` 均漏传 `published_at`，导致 100% 推送条目沦为 `backfill=true`（历史回填），不建事件、不计热度
- **问题位置**：[`bridge/push_to_aihot.py`](../../../bridge/push_to_aihot.py#L74-L123) 第 74–93 行及第 104–123 行：
  - `pipeline_report_item(...)` 返回 `IngestItem` 时未传 `published_at`（为 `None`）；
  - `community_item(...)` 返回 `IngestItem` 时**也漏传了 `published_at=post.published_at`**（尽管 `CommunityPost.published_at` 已被采集器解析出来！）。
- **后端契约冲突**：
  - 后端 [`packages/backend/src/content/materials.ts`](../../../packages/backend/src/content/materials.ts#L80-L118) 的 `decideTimeline()` 规定：只要 `publishedAt` 为 `null`，一律标为 `backfillReason = "unknown-publication-time"`、`backfill = true`，且 `isHistorical()` 返回 `true`！
  - 后果：
    1. `external-eastmoney-guba`（`hot_signal` 轨）在 `settleNonEditorial()`（`packages/backend/src/jobs/content.ts` 第 99 行 `row.participation_mode === "hot_signal" && !isHistorical(row)`）中全部返回 `{ group: false }`，**所有股吧脉冲帖全部被丢弃，无法为事件贡献任何热度**！
    2. 三条 `editorial` 轨（管道战报、淘股吧、雪球）全部被当成历史旧闻（`backfill = true`），**不创立新事件、不进今日热榜、不进盘前内参日报**！
- **修复要求**：
  - `pipeline_report_item(stock, summary, published_at=...)` 必须传入当前采集时间 ISO 字符串（如 `now_beijing().isoformat()` 或样本基准时间）；
  - `community_item(post, source_id, with_body, fallback_published_at=...)` 必须传入 `published_at=post.published_at or fallback_published_at`，确保送到 `/api/ingest/items` 的每一条 item 都带有合法的 `publishedAt`。

---

### 🟠 [P1 缺陷 3] `bridge/collectors/taoguba.py` 的 `_normalize_time()` 解析 `"%m-%d %H:%M"` 时年份变成 `1900` 年
- **问题位置**：[`bridge/collectors/taoguba.py`](../../../bridge/collectors/taoguba.py#L272-L275) 第 272–275 行：
  ```python
  for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m-%d %H:%M", "%Y/%m/%d %H:%M"):
      parsed = datetime.strptime(text, fmt)
  ```
- **根因**：Python 的 `datetime.strptime("10-16 10:05", "%m-%d %H:%M")` 默认 `year = 1900`（产出 `1900-10-16T10:05:00+08:00`）。送到后端后因距今超过 48 小时（`STALE_ON_DISCOVERY_MS`）会被直接打成 `stale-on-discovery` 历史回填。
- **修复要求**：当 `fmt == "%m-%d %H:%M"` 时，使用基准年份（默认 `now_beijing().year`，若拼出时间比当前晚超过 1 天则 `year - 1`）替换 `1900` 年，并在 `bridge/tests/test_bridge.py` 中补 1 条针对 `"10-16 10:05"` 的单测断言。

---

### 🟠 [P1 缺陷 4] 补齐 Python → TypeScript `ingestItems()` 真实契约联调测试
- **修复要求**：
  1. 在 `bridge/tests/test_bridge.py` 中断言：`build_push_plan` 产出的四条轨道所有 `IngestItem.to_payload()`，其 `url` 必须以 `https://` 开头，且 `publishedAt` 必须非空、年份 $\ge 2026$；
  2. 在 `tests/ingest.test.ts` 中补 1 条契约测试：用与 `bridge` 四轨一致的 payload（含 `https://quote.eastmoney.com/sz300308.html?date=2026-10-16`、`publishedAt: new Date().toISOString()`、`bodyText` 等）调用 `ingestItems()`，断言：
     - `created === 1`；
     - 入库行 `backfill === false` 且 `published_at IS NOT NULL`；
     - `hot_signal` 信源入库后调用 `settleNonEditorial()` 返回 `{ group: true }`（证明真正能进事件热度归组）。
