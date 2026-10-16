# SH-02 阶段独立审计报告（谷米 · 第一次审计 + 第二次复审结项）

- **当前结论**：✅ **PASS（第二次复审通过，4 项缺陷全部清零，准予 `SH-02` 结项并签发 `SH-03` 开工单）**
- **复审单号**：`AUDIT-SH02-20261016-R2`
- **复审提交**：`8991289`（代码修补） / `0fb7354`（证据与进度记录）
- **复审时间**：2026-10-16 17:14 CST
- **审计人**：谷米（规划与审查 Agent）
- **实施人**：稳米（实施 Agent）

---

## 一、 第二次复审结论（`AUDIT-SH02-20261016-R2` · PASS）

谷米对稳米返工提交 `8991289` / `0fb7354` 进行了逐行代码审查与独立命令复测，第一次审计（`R1`）指出的 **2 个 P0 阻断级跨语言契约缺陷 + 2 个 P1 缺陷已 100% 闭环清零**：

### 1. 4 项缺陷修复逐一核验

| 缺陷编号 | 返工前问题 | 稳米修复实现 | 谷米独立复核结果 |
| --- | --- | --- | --- |
| **P0-1** | `pipeline_report_item` 使用 `ymhot://radar/stock/{symbol}`，被后端 `normalizeUrl()` 拒绝返回 `null`，30 条战报 `created: 0` 全部静默丢弃 | [`bridge/push_to_aihot.py`](../../../bridge/push_to_aihot.py#L22-L99) 改为 `https://quote.eastmoney.com/{symbol.lower()}.html?date={trade_date}`；`date` 不在后端 `TRACKING_PARAMS` 剥离列表内，既保留交易日粒度又支持同日 15m 重推走 `reviseMaterial()` 原地修订 | ✅ **PASS**：`normalizeUrl()` 100% 放行，真实入库 `planned=30, created=30` |
| **P0-2** | `pipeline_report_item` 与 `community_item` 漏传 `published_at`，导致后端 `decideTimeline()` 将 100% 条目判为 `backfill=true`（`unknown-publication-time`）且 `isHistorical()===true` | [`bridge/push_to_aihot.py`](../../../bridge/push_to_aihot.py#L75-L185) 统一生成批次基准时间 `batch_time`，战报显式传 `published_at=batch_time`，社区帖传 `published_at=post.published_at or fallback_published_at` | ✅ **PASS**：四轨 41 条 payload 全部带合法 ISO 时间，入库后 `backfill=0, undated=0`，`external-eastmoney-guba` 的 `settleNonEditorial()` 实测返回 `{"group": true}` |
| **P1-3** | [`bridge/collectors/taoguba.py`](../../../bridge/collectors/taoguba.py) 解析 `"%m-%d %H:%M"` 时默认落到 `1900` 年，且触发 Python 3.12+ 无年份 `strptime` 弃用警告 | 改用显式正则 `_YEARLESS_TIME` 搭配 `_fill_year()` 按基准年份补齐（跨年边界若拼出时间晚于基准超过 1 天则自动退 1 年） | ✅ **PASS**：`"10-16 10:05"` 稳定解析为 `2026-10-16T10:05:00+08:00`，且消除 Python 3.15 弃用隐患 |
| **P1-4** | 缺少 Python → TS `ingestItems()` 跨语言契约测试；`.gitignore` 未忽略 `__pycache__/` | 补齐 `.gitignore`；在 [`bridge/tests/test_bridge.py`](../../../bridge/tests/test_bridge.py#L438-L492) 新增 5 项契约单测；在 [`tests/ingest.test.ts`](../../../tests/ingest.test.ts#L172-L250) 新增真实四轨入库与 `settleNonEditorial` 断言；新增 [`scripts/verify-bridge-contract.ts`](../../../scripts/verify-bridge-contract.ts) 一次性干净库端到端校验脚本 | ✅ **PASS**：`git status --short` 干净无残留；56 项 Python 单测 + 22 项 Node 单测 + 跨语言管道实测全部绿灯 |

### 2. 谷米独立执行的验证命令与实测输出

1. **Python 桥接与采集单测套件（56 项）**：
   ```bash
   python3 -m unittest discover -s bridge/tests -p "test_*.py" -v
   # Ran 56 tests in 0.136s — OK
   ```
2. **全仓 TypeScript 类型检查**：
   ```bash
   PATH="/opt/homebrew/bin:$PATH" npm run typecheck
   # Exit 0 (packages/contracts, packages/backend, modules, apps/web 全部零报错)
   ```
3. **Node 后端核心测试（`ingest` / `provenance` / `architecture`）**：
   ```bash
   PATH="/opt/homebrew/bin:$PATH" DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test \
     node --test --test-concurrency=1 --test-global-setup=tests/databases.ts --import ./tests/databases.ts \
     tests/ingest.test.ts tests/provenance.test.ts tests/architecture.test.ts
   # tests 22 | pass 22 | fail 0
   ```
4. **Python `run_bridge` 真实 Payload 导出 → TypeScript `ingestItems()` + `settleNonEditorial()` 端到端对账**：
   ```bash
   python3 -m bridge.run_bridge --offline-fixtures --dry-run --dump-payloads /tmp/bridge-payloads.json && \
   PATH="/opt/homebrew/bin:$PATH" DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test \
     node --import ./tests/databases.ts scripts/verify-bridge-contract.ts /tmp/bridge-payloads.json
   ```
   - `external-ym-pipeline (editorial)`: `{"planned":30,"created":30,"backfill":0,"undated":0,"bodyChars":173}`
   - `external-taoguba-hot (editorial)`: `{"planned":5,"created":5,"backfill":0,"undated":0,"bodyChars":10}`
   - `external-xueqiu-hot (editorial)`: `{"planned":2,"created":2,"backfill":0,"undated":0,"bodyChars":42}`
   - `external-eastmoney-guba (hot_signal)`: `{"planned":4,"created":4,"backfill":0,"undated":0,"settleNonEditorial":{"group":true}}`
   - `contract verified: 41 items ingested across 4 tracks, 0 backfill, hot_signal settles to group=true`

---

## 二、 第一次审计历史记录归档（`AUDIT-SH02-20261016-R1` · 已由 `8991289` 修复闭环）

- **审计单号**：`AUDIT-SH02-20261016-R1`
- **被审提交**：`411d694`（代码） / `57c44ad`（证据清单）
- **审计时间**：2026-10-16 16:03 CST
- **当时结论**：❌ REJECT / 需返工修补（发现 P0-1 `ymhot://` URL 被 `normalizeUrl()` 丢弃、P0-2 漏传 `published_at` 致 100% 沦为 `backfill=true`、P1-3 淘股吧 `%m-%d %H:%M` 年份落回 `1900`、P1-4 缺跨语言契约单测与 `.gitignore` 规则）
