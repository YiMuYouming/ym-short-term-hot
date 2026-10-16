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

test("the radar page renders the ladders view with themes, roles, nicknames and sentiment", async () => {
  const response = await fetch(`${web.origin}/radar`);
  const html = await response.text();
  assert.equal(response.status, 200, web.logs().slice(-1500));
  for (const [what, needle] of [
    ["站点的雷达标题", "短线雷达"],
    ["梯队视图切换", "题材主线梯队"],
    ["共振榜切换", "人气共振"],
    ["黑话外号搜索框", "黑话外号"],
    ["快照时间", "快照"],
  ] as const) {
    assert.ok(html.includes(needle), `${what}未出现在页面：缺少「${needle}」`);
  }
  // The data really came through: the snapshot's own themes, a role badge and a community nickname.
  assert.ok(/光模块|人形机器人|算力/.test(html), "页面没有渲染任何题材名");
  assert.ok(/空间板|容量中军|首板发酵/.test(html), "页面没有渲染身位标签");
  assert.ok(/易中天|寒王|宁王/.test(html), "页面没有渲染社区黑话外号");
  assert.ok(/一致亢奋|分歧博弈|恐慌核按钮|讨论平淡/.test(html), "页面没有渲染社区情绪标签");
  assert.ok(!html.includes("暂无短线雷达快照"), "有快照时不应显示空状态");
});

test("the view, the nickname query and the drawer are all addressable by URL", async () => {
  const resonance = await (await fetch(`${web.origin}/radar?view=resonance`)).text();
  assert.ok(resonance.includes("人气共振"), "共振榜视图未按 ?view= 切换");

  const nickname = await (await fetch(`${web.origin}/radar?q=${encodeURIComponent("易中天")}`)).text();
  assert.ok(nickname.includes("易中天"), "黑话外号未命中");

  const drawer = await (await fetch(`${web.origin}/radar?stock=300308`)).text();
  assert.ok(drawer.includes("社区舆情"), "?stock= 未打开个股舆情抽屉");
  assert.ok(drawer.includes("跨平台热度") || drawer.includes("有效帖"), "抽屉缺少情绪与热度信息");
});