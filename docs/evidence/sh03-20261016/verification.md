# SH-03 验证记录（稳米）

- 工单：`WO-SH03-20261016`（双视图短线雷达模块与端到端联调）
- 基线提交：`e40875c`（SH-02 R2 复审通过）
- 交付提交：见 `git log -1`（提交信息 `feat(sh03): add short-term-radar module with dual views and stock drawer`）
- 验证时间：2026-10-16 17:30~19:10（Asia/Shanghai）
- 环境：Node v26.11.0（Homebrew）、CPython 3.14.5、PostgreSQL `@embedded-postgres/darwin-arm64` @127.0.0.1:5432

## 0. 结论速览

| 门禁 | 命令 | 结果 |
| --- | --- | --- |
| 1 | `python3 -m unittest discover -s bridge/tests -p "test_*.py"` | **56/56 通过**，exit 0（`bridge-tests.txt`） |
| 2 | `npm run typecheck` | **exit 0**，七个工程（contracts/backend/api/worker/tests/modules/web）零报错（`typecheck.txt`） |
| 3 | `npm run build -w @aihot/web` | **exit 0**，`/radar` 打包为 `radar-route-*.js`（`web-build.txt`） |
| 4a | 模块单测 `modules/short-term-radar/tests/radar.test.ts` | **4/4 通过**，exit 0（`radar-tests.txt`） |
| 4b | 架构红线 + 引擎回归 + 页面 SSR | **19/19 + 2/2 通过**，exit 0（`node-tests.txt`） |
| 5 | 全量 `npm test`（干净模板库） | **737 通过 / 16 失败**；失败集与 SH-01 上游基线**完全一致**（14 项环境类），**新增回归 0**（`full-test.log`） |

架构四条红线逐条通过：`the web reaches the backend only over HTTP`、`every environment variable the code reads is listed in a template`、`every table and column is used by the code that reads and writes the database`、`modules do not import other modules`。

## 1. 交付物

```
modules/short-term-radar/
├── package.json                       # @aihot/short-term-radar（workspace 软链）
├── module.ts                          # defineModule：pages → /radar，apiPaths → /api/(site|v1)/radar
├── contracts.ts                       # 快照文件形状 → API/前端契约的映射 + 过滤 + 单股查找（纯函数）
├── server.ts                          # 读快照、四条 HTTP 路由、AgentAbility（/api/v1/agent/radar + MCP get_radar）
├── web.tsx                            # 桌面侧栏「短线雷达」+ 移动底栏「雷达」
├── web/radar-route.tsx                # 双视图看板 + 个股舆情抽屉（只走 apiGet HTTP）
├── tests/radar.test.ts                # 4 项模块单测
├── tests/fixtures/not-json.json       # 损坏快照样本
└── scripts/radar-page.test.ts         # 页面 SSR 测试（需 build，单跑，见 §4）
site/modules/{index,server,web}.ts     # 三处注册
package-lock.json                      # 仅新增该 workspace 的两处条目（8 行）
```

## 2. 关键实现决定

### 2.1 快照 → 契约的映射层（`contracts.ts`）

工单 §二 给的输入 schema 与 `SH-02` 实产快照**存在字段漂移**，逐条核对如下：

| 工单 §二 | 实产快照 | 处置 |
| --- | --- | --- |
| `code: "300308.SZ"` | `code: "300308"` | API 输出 `code=300308.SZ`，另给 `bareCode`/`symbol`；三种写法都能查单股 |
| `role` | `roleLabel` | 映射为 `role` |
| `bullRatio` 0~1 | `bullRatio` 0~100 | 归一化到 0~1（三色和恒为 1，测试断言） |
| `themeLadders[].stocks[]`（拍平） | `ladders{ 身位: [...] }` | 按 `ROLE_ORDER` 拍平，并从共振榜补全每只票的完整字段 |
| `heatScore` / `stockCount` / `topBoardCount` | 无 | 计算得出（成员共振分之和 / 成员数 / 最高连板） |
| `thsRank` / `dcRank` | `hotRankThs` / `hotRankDc` | 映射（另保留 `hotRankXq`） |
| `turnoverRate` / `kplTag` / `limitReason` | **快照中没有** | 置 0 / 空串，前端按「—」或隐藏；已在 manifest 记录 |
| `highlights[].source/postId/excerpt/readCount/likeCount/sentimentLabel/matchedTerms/publishedAt` | `platform/title/authorName/commentCount/isVipYouzi/isDeepLogic` | 能映射的映射，计数类缺失项置 0，标题同时作为 `excerpt` |
| `dataQuality.thsHotSource` 等 | `dataQuality.sources.ths_hot.status` | 映射成扁平徽章（`sourceBadges()`） |

处置原则：**不改 Python 侧产物**（红线 C：只读），漂移集中在 `contracts.ts` 一处映射，两端（后端与前端）都只认映射后的契约。

### 2.2 四条路由与降级

- `GET /api/site/radar`、`GET /api/v1/radar`（后者包 `{ ok, data }`），支持 `?theme= &role= &q=`；
- `GET /api/site/radar/stock/:code`、`GET /api/v1/radar/stock/:code`：接受 `300308` / `300308.SZ` / `SZ300308`（大小写不敏感），未命中 404 `Stock not found in radar snapshot`；
- 快照缺失或 JSON 损坏 → 返回 `mode: "empty"` 的空结构，**200 而不是 500**（测试覆盖两种情形）；
- `q` 命中代码、名称、**社区黑话外号**（易中天/寒王/宁王）与题材名。

### 2.3 Agent / MCP 能力

`AgentAbility`：`path: "/radar"`（即 `/api/v1/agent/radar`）+ `mcp.tool: "get_radar"`，输入 `view(ladders|resonance|all)`、`theme`、`role`、`query`、`limit`，返回 Markdown 摘要与结构化快照。

### 2.4 前端

双视图（`?view=ladders|resonance` 与 URL 同步）、搜索与身位快筛、**A股红涨绿跌**配色、三色社区情绪温度条（看多红 / 分歧琥珀 / 看空绿）、身位徽章（空间板金→人气热股中性灰）、黑话外号徽章，右侧抽屉含个股战报摘要、跨平台热度、社区情绪仪表盘与三社区高价值帖（游资/深度逻辑/情绪/黑话词徽章 + 原帖外链，Esc 与遮罩关闭）。无快照时显示空状态并给出生成命令。

## 3. 工单与仓库实况的三处偏差（已按实况实现并记录）

1. **工单 §二 的输入 schema 与实产快照不一致**（见 §2.1），已在映射层对齐；`turnoverRate`/`kplTag`/`limitReason` 当前无数据来源。
2. **工单 S1 的 `navItems` 字段不存在**：真实 `WebModule` 是 `sidebar: { section, items }` + `tabs`，按真实类型实现。
3. **工单 S4 门禁里的 `tests/site-contract.test.ts` 在本仓不存在**（上游无此文件）：改用实际存在的等价集合 `tests/architecture.test.ts` + `tests/ingest.test.ts` + `tests/topics.test.ts` + 模块单测，另加全量 `npm test` 差集。

此外工单示例中的 `apiGet("/api/site/radar", { request })` 与真实签名（`{ signal, headers, responseHeaders }`）不同，已按真实签名写 `{ signal: request.signal }`。

## 4. 页面 SSR 测试为何放在 `scripts/`

`npm test` 的 glob 是 `tests/*.test.ts` + `modules/*/tests/*.test.ts`。页面测试需要生产构建产物，并会 spawn 一个 web server；其 15s 启动预算在整套测试六文件并发时会被挤爆（单跑 3.3s 通过，全量并发下超时）。因此把它放在 `modules/short-term-radar/scripts/radar-page.test.ts`：**常规单测不依赖 build**，需要时显式运行（命令写在文件头注释里），本记录的 `node-tests.txt` 即其输出。

## 5. 全量回归差集

干净模板库（重建 `ymhot_test` 后）全量：**737 通过 / 16 失败**。与 SH-01 阶段在上游基线 `c8704e5` 同环境建立的失败集逐条比对：

- 14 项完全相同（backup 8、api-error-logging 2、mcp-host 1、oauth 1、outbound-protocol 1、analyze-kill SIGKILL 1），均为沙箱环境类（`spawnSync ETIMEDOUT`、外部 fetch 被拦、备份目录权限语义、进程计时），与本阶段改动无关；
- **新增失败 0**。

## 6. 过程中发现并处置的两个环境问题（非代码缺陷）

1. **测试模板库被污染**：`ymhot_test` 是所有测试文件的模板库。SH-02 阶段旧版 `scripts/verify-bridge-contract.ts` 曾直接往它写 `contract-*` 信源（20 条），导致 `source-health`、`grouping-reliability` 等按数量断言的测试连锁失败（`external: 20` vs 期望 `2`）。处置：脚本改为自建一次性库并 drop（已随 SH-02 提交），本阶段重建模板库后全量回归干净。
2. **并发跑分互相踩踏**：全量测试运行时并行使用同一模板库会出现 `source database "ymhot_test" is being accessed by other users`，导致 8 个测试文件级崩溃。处置：门禁串行执行，SSR 测试使用独立库。

## 7. 复现命令

```bash
# 数据快照（若 .data/short-term-radar-snapshot.json 已存在可跳过）
python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run

python3 -m unittest discover -s bridge/tests -p "test_*.py" -v
npm run typecheck
npm run build -w @aihot/web
DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test node --test-concurrency=1 \
  --test-global-setup=tests/databases.ts --import ./tests/databases.ts --test \
  tests/architecture.test.ts tests/ingest.test.ts tests/topics.test.ts \
  modules/short-term-radar/tests/radar.test.ts
DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test node \
  --test-global-setup=tests/databases.ts --import ./tests/databases.ts --test \
  modules/short-term-radar/scripts/radar-page.test.ts
```

本地访问：`npm run dev:api`（3001）+ `npm run dev:web`（3000）后打开 <http://localhost:3000/radar>。
