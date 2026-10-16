# SH-03 阶段独立审计报告（谷米 · 第一次终审）

- **审计单号**：`AUDIT-SH03-20261016-R1`
- **被审提交**：`387686a`（`feat(sh03): add short-term-radar module with dual views and stock drawer`）
- **审计人**：谷米（规划与审查 Agent）
- **实施人**：稳米（实施 Agent）
- **审计时间**：2026-10-16 18:30 CST
- **审计结论**：🟠 **需小幅返工修补（主体架构与 4 条红线 100% 达标，但抓出 2 个 P1 数据映射/URL寻址缺陷 + 1 处假阳性测试断言，预计 25 行代码内可修完结项）**

---

## 一、 亮点肯定（保留，无需重写）

1. **AIHOT 四条架构门禁红线 100% 绿灯**：
   - `tests/architecture.test.ts` 7 项测试全部通过：`modules/short-term-radar/web/**` 严格只走 `apiGet` HTTP 边界、零新增数据库表/列、零未登记 `process.env`、双 `tsconfig.json` 编译边界干净对齐。
2. **模块三件套注册、API 与 Agent/MCP 能力完整**：
   - `site/modules/{index,server,web}.ts` 注册完整；
   - `GET /api/site/radar`、`GET /api/v1/radar`、`GET /api/site/radar/stock/:code`、`GET /api/v1/radar/stock/:code` 及 `AgentAbility`（`/api/v1/agent/radar` + MCP `get_radar`）全部跑通，空目录与损坏 JSON 降级为 `mode: "empty"`（200）。
3. **双视图与个股舆情侧滑抽屉完成度高**：
   - `modules/short-term-radar/web/radar-route.tsx` 实现了「🧩 题材主线梯队 ⇄ 🔥 人气共振 Top 30」、三色社区情绪温度条、黑话外号与身位徽章，以及支持按社区过滤高价值帖的侧滑抽屉。

---

## 二、 必须返工修补的 2 个缺陷（根因与定位）

谷米在对 [`modules/short-term-radar/contracts.ts`](../../../modules/short-term-radar/contracts.ts) 与 [`modules/short-term-radar/web/radar-route.tsx`](../../../modules/short-term-radar/web/radar-route.tsx) 做全量快照数据对账和 SSR URL 寻址实测时，抓出以下 2 个真实缺陷：

### 🟠 [P1 缺陷 1] `contracts.ts` 的 `mapSnapshot()` 对未进 Top 30 的 20 只梯队焦点股丢失了 `roleLabel`（身位）、`themes`（题材）与 `exchange`（交易所后缀），导致 6 个题材梯队身位自相矛盾
- **问题位置**：[`modules/short-term-radar/contracts.ts`](../../../modules/short-term-radar/contracts.ts#L255-L270) 第 255–270 行：
  ```ts
  const byCode = new Map<string, FileStock>();
  for (const stock of file.topResonanceStocks ?? []) {
    if (stock?.code) byCode.set(stock.code, stock);
  }
  ...
  for (const role of ROLE_ORDER) {
    for (const entry of buckets[role] ?? []) {
      if (entry?.code) ordered.push(byCode.get(entry.code) ?? { code: entry.code, name: entry.name, symbol: entry.symbol, boardCount: entry.boardCount, resonanceScore: entry.resonanceScore });
    }
  }
  ```
- **根因与实测证据**：
  焦点股池共 50 只（`focusPoolSize: 50`），而 `file.topResonanceStocks` 只包含前 30 只。因此梯队里的第 31~50 名焦点股（共 20 只，如赛力斯、立讯精密、阳光电源、英维克、完美世界、芒果超媒、兆易创新等）在 `byCode.get(entry.code)` 中返回 `undefined`，走到后面的 fallback 对象，而该 fallback 对象漏填了 3 个关键字段：
  1. **漏填 `roleLabel: role`**：明明该股是从 `buckets[role]`（例如 `buckets["容量中军"]`）里遍历出来的，却因 fallback 未传 `roleLabel: role` 被 `mapStock()` 默认打成 `"人气热股"`！
     - **谷米实测抓包**：导致 **6 个题材梯队出现“梯队抬头摘要写着『容量中军 1 只』，下方卡片却显示『人气热股』，且点击『容量中军』筛选时这 6 只中军全被过滤消失”** 的自相矛盾：
       - `华为/鸿蒙`：摘要写 `容量中军 1 只`，但 `赛力斯` 被标成 `人气热股`；
       - `消费电子/苹果链`：摘要写 `容量中军 1 只`，但 `立讯精密` 被标成 `人气热股`；
       - `储能`：摘要写 `容量中军 1 只`，但 `阳光电源` 被标成 `人气热股`；
       - `液冷/散热`：摘要写 `容量中军 1 只`，但 `英维克` 被标成 `人气热股`；
       - `传媒/AI短剧/影视`：摘要写 `容量中军 2 只`，但 `完美世界`、`芒果超媒` 均被标成 `人气热股`；
       - `存储芯片/HBM`：摘要写 `容量中军 1 只`，但 `兆易创新` 被标成 `人气热股`。
  2. **漏填 `themes`（共 21 处缺失）**：这 20 只股票的 `stock.themes` 变成了空数组 `[]`。当调用 `GET /api/site/radar?theme=消费电子` 时，`keeps()` 检查 `stock.themes.some(...)` 为 `false`，导致 `消费电子/苹果链` 梯队下的 `stocks` 被过滤成空数组 `[]`！
  3. **漏填 `exchange`（共 20 处未带后缀）**：`entry.symbol` 带有 `"SH601127"` / `"SZ002475"` 前缀，但 fallback 未提取 `exchange`，导致这 20 只股票的 `stock.code` 变成裸代码 `"601127"` 而非 `"601127.SH"`，请求 `/api/site/radar/stock/601127.SH` 直接返回 404！
- **修复要求**：
  在 `mapSnapshot()` 中：
  1. 先遍历一次 `file.themeLadders` 汇总每只 `entry.code` 所属的全部题材列表 `themesByCode: Map<string, string[]>`；
  2. 在遍历 `buckets[role]` 构造 `FileStock` 时，将桶的 `role`、合并后的 `themes`、以及从 `entry.symbol` 前缀提取的 `exchange`（如 `entry.symbol?.match(/^(SH|SZ|BJ)/i)?.[1]?.toUpperCase()`）一并补齐：
     ```ts
     const base = byCode.get(entry.code);
     const mergedThemes = Array.from(new Set([...(base?.themes ?? []), ...(themesByCode.get(entry.code) ?? [])]));
     const inferredExchange = base?.exchange || entry.symbol?.match(/^(SH|SZ|BJ)/i)?.[1]?.toUpperCase();
     ordered.push({
       ...base,
       code: entry.code,
       name: base?.name ?? entry.name,
       symbol: base?.symbol ?? entry.symbol,
       exchange: inferredExchange,
       themes: mergedThemes,
       roleLabel: base?.roleLabel ?? role,
       boardCount: base?.boardCount ?? entry.boardCount,
       resonanceScore: base?.resonanceScore ?? entry.resonanceScore,
     });
     ```
  3. 在 [`modules/short-term-radar/tests/radar.test.ts`](../../../modules/short-term-radar/tests/radar.test.ts) 中新增断言：遍历 `snapshot.themeLadders` 的所有 `ladder` 与 `stock`，断言：
     - `stock.themes.includes(ladder.theme)` 恒为 `true`；
     - `stock.code` 均包含 `.`（如 `.SZ` / `.SH`）；
     - 当 `ladder.summary` 包含 `"容量中军"` 时，`ladder.stocks.some((s) => s.role === "容量中军")` 恒为 `true`。

---

### 🟠 [P1 缺陷 2] `radar-route.tsx` 未响应 URL 查询参数 `?q=` 与 `?theme=`，且 `radar-page.test.ts` 第 75 行存在假阳性测试断言
- **问题位置**：
  - [`modules/short-term-radar/web/radar-route.tsx`](../../../modules/short-term-radar/web/radar-route.tsx#L341-L370) 第 341–370 行：
    ```tsx
    const [params, setParams] = useSearchParams();
    const [query, setQuery] = useState("");
    const view = (params.get("view") === "resonance" ? "resonance" : "ladders") as ViewKey;
    const role = params.get("role");
    const openCode = params.get("stock");
    ```
  - [`modules/short-term-radar/scripts/radar-page.test.ts`](../../../modules/short-term-radar/scripts/radar-page.test.ts#L75-L76) 第 75–76 行：
    ```ts
    const nickname = await (await fetch(`${web.origin}/radar?q=${encodeURIComponent("易中天")}`)).text();
    assert.ok(nickname.includes("易中天"), "黑话外号未命中");
    ```
- **根因**：
  1. `RadarRoute` 的 `query` 状态硬编码初始值为 `""`，完全没有读取 `params.get("q")`，也没有读取 `params.get("theme")`！
  2. 因此当访问 `/radar?q=易中天` 或 `/radar?theme=光模块` 时，SSR 与首屏渲染**根本没有执行过滤**，页面上照样渲染了 `宁德时代`、`寒武纪` 等全部 18 个题材的股票！
  3. 之所以 `radar-page.test.ts` 第 75 行的 `nickname.includes("易中天")` 能通过，是因为未过滤的全量页面本来就在搜索框 `placeholder="搜代码 / 名称 / 黑话外号（易中天、寒王）"` 和全量列表里含有 `"易中天"` 字样（假阳性通过）。
- **修复要求**：
  1. 在 `radar-route.tsx` 中支持 URL `?q=` 与 `?theme=` 寻址过滤：
     - 将搜索词与 URL `?q=` 打通（例如 `const qParam = params.get("q") ?? "";` 或以 `params.get("q") ?? ""` 初始化/派生有效查询词 `effectiveQuery = query || qParam`，且输入框变化时同步 `setQuery` / `setParam("q", ...)`）；
     - 读取 `const theme = params.get("theme");`，在渲染 `themeLadders` 和 `boards` 时同时应用 `theme` 过滤；
  2. 在 [`modules/short-term-radar/scripts/radar-page.test.ts`](../../../modules/short-term-radar/scripts/radar-page.test.ts#L75-L76) 第 75–76 行补上负向断言，彻底消除假阳性：
     - 访问 `/radar?q=易中天` 时，断言 `nickname.includes("中际旭创")` 为 `true`，且**不包含**未命中股票 `assert.ok(!nickname.includes("宁德时代"), "?q=易中天 应过滤掉无关股票宁德时代")`！
