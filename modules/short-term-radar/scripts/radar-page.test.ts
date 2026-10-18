// The radar page, rendered for real: the api the module installs in front of the production web
// server, read over HTTP. This is what the module tests cannot see — the loader, the two views and
// the drawer's data as the browser first receives them.
//
// It lives under scripts/ rather than tests/ on purpose. It needs a production build (`npm run build
// -w @aihot/web`) and spawns a web server, whose 15s start-up budget is tight when the whole suite
// runs six files at once; the unit suite must not depend on either. Run it explicitly:
//
//   npm run build -w @aihot/web
//   node --test-global-setup=tests/databases.ts --import ./tests/databases.ts --test \
//     modules/short-term-radar/scripts/radar-page.test.ts
//
// It also needs a snapshot: `python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run`;
// the test copies the repository's own file into the data directory the runner points at.
import "../../../tests/setup.ts";
import assert from "node:assert/strict";
import { copyFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { after, before, test } from "node:test";
import { config } from "@aihot/backend/config";
import { closeDb } from "@aihot/backend/db";
import { installModules } from "@aihot/backend/modules";
import { stopBoss } from "@aihot/backend/jobs/queue";
import { SERVER_MODULES } from "@aihot/site/modules/server";
import { buildApp } from "../../../apps/api/src/app.ts";
import { startWebServer, type WebServer } from "../../../apps/web/tests/web-server.ts";

const REPO_SNAPSHOT = path.join(import.meta.dirname, "..", "..", "..", ".data", "short-term-radar-snapshot.json");

let api: Awaited<ReturnType<typeof buildApp>>;
let web: WebServer;

before(async () => {
  // tests/databases.ts points AIHOT_DATA_DIR at a scratch folder per test file; put the snapshot there.
  await mkdir(config.dataDir, { recursive: true });
  await copyFile(REPO_SNAPSHOT, path.join(config.dataDir, "short-term-radar-snapshot.json"));
  installModules(SERVER_MODULES);
  api = await buildApp();
  await api.ready(); // the helper listens on the raw server, so fastify must be ready before it does
  web = await startWebServer(api.server);
});

after(async () => {
  await web?.stop();
  await api?.close();
  await stopBoss();
  await closeDb();
});

test("the radar page renders the two minimal views over one snapshot (LITE-02)", async () => {
  const response = await fetch(`${web.origin}/radar`);
  const html = await response.text();
  assert.equal(response.status, 200, web.logs().slice(-1500));
  for (const [what, needle] of [
    ["站点的雷达标题", "雷达"],
    ["视角一切换", "热门板块"],
    ["视角二切换", "热门股 Top 50"],
    ["板块列表标题", "按热度排序"],
    ["交易日页头", "交易日"],
    ["板块/成分股筛选框", "筛选板块或成分股"],
    ["长尾折叠按钮", "展开其余"],
  ] as const) {
    assert.ok(html.includes(needle), `${what}未出现在页面：缺少「${needle}」`);
  }
  // The data really came through: a theme name, a role badge, a nickname, why-hot copy and a sentiment label.
  assert.ok(/光模块|人形机器人|低空经济/.test(html), "页面没有渲染任何题材名");
  assert.ok(/空间板|容量中军|首板发酵/.test(html), "页面没有渲染身位标签");
  assert.ok(/易中天|寒王|宁王/.test(html), "页面没有渲染社区黑话外号");
  assert.ok(/为什么火|涨停原因|行业原因|热门概念|题材归属/.test(html), "页面没有渲染为什么火");
  assert.ok(/一致亢奋|分歧博弈|恐慌核按钮|讨论平淡/.test(html), "页面没有渲染社区情绪标签");
  // LITE-04：首板术语、负涨幅领涨改称代表、单股长尾折叠后主线仍可见
  assert.ok(html.includes("首板"), "boardCount===1 应显示「首板」而不是「1 连板」");
  assert.ok(html.includes("代表 "), "全绿板块的领头羊应改称「代表」");
  assert.ok(!html.includes("1 连板"), "不应再出现「1 连板」这种反术语写法");
  assert.ok(!html.includes("暂无短线雷达快照"), "有快照时不应显示空状态");
});

test("view, theme and stock are addressable by URL; the drawer shows why-hot and the communities", async () => {
  // 视角二：干净表格，表头列名即开工单要求的核心硬信息
  const stocks = await (await fetch(`${web.origin}/radar?view=stocks`)).text();
  for (const needle of ["排名", "股票", "涨跌幅", "所属板块", "为什么火", "社区热度"]) {
    assert.ok(stocks.includes(needle), `Top 50 表格缺列「${needle}」`);
  }
  assert.ok(stocks.includes("中际旭创"), "表格应渲染共振榜股票");
  // LITE-04：固定列宽（colgroup）、小样本标注、板块胶囊 2+N
  assert.ok(stocks.includes("<colgroup"), "Top 50 表格应启用 table-fixed 的 colgroup");
  assert.ok(stocks.includes("小样本"), "样本不足 5 帖应标注「小样本」");
  assert.ok(stocks.includes("+2"), "超过 2 个板块应折叠成 +N（拓维信息 4 个板块）");

  // 视角一：?theme= 选中板块（默认热度第一），渲染该板块内热门股
  const themed = await (await fetch(`${web.origin}/radar?theme=${encodeURIComponent("低空经济/eVTOL")}`)).text();
  assert.ok(themed.includes("低空经济/eVTOL"), "?theme= 未选中对应板块");
  assert.ok(themed.includes("华力创通"), "选中板块应展示板块内热门股");

  // 抽屉：为什么火置顶 + 连板封板硬信息 + 三平台切换 + 社区情绪简况
  const drawer = await (await fetch(`${web.origin}/radar?stock=300308`)).text();
  assert.ok(drawer.includes("为什么火"), "抽屉未置顶展示为什么火");
  assert.ok(drawer.includes("行业原因"), "抽屉未展示同花顺 rank_reason 详情");
  assert.ok(/封板|连板/.test(drawer), "抽屉缺少连板封板硬信息");
  for (const platform of ["淘股吧", "雪球", "东财股吧"]) {
    assert.ok(drawer.includes(platform), `抽屉缺少平台切换「${platform}」`);
  }
  assert.ok(drawer.includes("有效帖"), "抽屉缺少社区情绪简况");
  // LITE-03：按名称/黑话命中的淘股吧复盘帖也进抽屉高亮（归股与精选同一链路）
  assert.ok(drawer.includes("算力主线复盘"), "抽屉应展示按名称/黑话命中的淘股吧复盘帖");
  // LITE-04：上一只/下一只导航、平台 Tab 计数、长文本折叠
  assert.ok(drawer.includes("上一只") && drawer.includes("下一只"), "抽屉应支持上一只/下一只切换");
  assert.ok(/\(\d+\)/.test(drawer), "平台 Tab 应带帖子计数");
  assert.ok(drawer.includes("展开完整逻辑"), "长 whyHot 应默认折叠并提供展开按钮");
});

test("the drawer never shows a 4-board stock as 未封板 (LITE-04 honesty)", async () => {
  // 冰山冷热：样本里 4 连板但盘中池未返回封板时间——必须写「封板时间待补」，
  // 不能再出现「4 连板」旁边写着「未封板/非涨停」的自相矛盾（截图 3 回归锁）。
  const drawer = await (await fetch(`${web.origin}/radar?stock=000530`)).text();
  assert.ok(drawer.includes("4 连板"), "冰山冷热应显示 4 连板");
  assert.ok(drawer.includes("封板时间待补"), "缺封板时间应显示「封板时间待补」");
  assert.ok(!drawer.includes("未封板"), "不应再出现「未封板」这种把缺失写成否定的文案");
  assert.ok(!drawer.includes("未封板/非涨停"), "不应再出现「未封板/非涨停」矛盾文案");
});