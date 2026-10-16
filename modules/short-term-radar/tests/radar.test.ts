// The radar module's own tests: it reads what the Python bridge wrote, answers both views over HTTP,
// filters by theme/role/nickname, serves one stock in three address forms, and degrades to an empty
// snapshot when the file is missing.
//
// The data file is the real one (the bridge's output), so a change in the bridge's schema shows up
// here rather than only on the page. Run `python3 -m bridge.run_bridge --offline-fixtures --sync-gold
// --dry-run` first if it is missing.
import "../../../tests/setup.ts";
import assert from "node:assert/strict";
import { copyFile, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";
import { config } from "@aihot/backend/config";
import { installModules } from "@aihot/backend/modules";
import { stopBoss } from "@aihot/backend/jobs/queue";
import { closeDb } from "@aihot/backend/db";
import { SERVER_MODULES } from "@aihot/site/modules/server";
import { buildApp } from "../../../apps/api/src/app.ts";
import { loadRadarSnapshot } from "../server.ts";
import type { RadarStockDetail, ShortTermRadarSnapshot } from "../contracts.ts";

const SNAPSHOT = "short-term-radar-snapshot.json";
const source = path.join(import.meta.dirname, "..", "..", "..", ".data", SNAPSHOT);

let app: Awaited<ReturnType<typeof buildApp>>;

before(async () => {
  await copyFile(source, path.join(config.dataDir, SNAPSHOT));
  installModules(SERVER_MODULES);
  app = await buildApp();
});

after(async () => {
  await app?.close();
  await stopBoss();
  await closeDb();
});

const get = async (url: string) => {
  const response = await app.inject({ method: "GET", url });
  return response;
};

/** A stock in every address form the detail route accepts. */
const STOCK_CODE = "300308";

test("both views answer 200 with ladders, the board, sentiment and highlights", async () => {
  const site = await get("/api/site/radar");
  assert.equal(site.statusCode, 200, site.body);
  const snapshot = JSON.parse(site.body) as ShortTermRadarSnapshot;
  assert.ok(snapshot.themeLadders.length >= 10, `题材梯队过少：${snapshot.themeLadders.length}`);
  assert.ok(snapshot.topResonanceStocks.length >= 20, `共振榜过短：${snapshot.topResonanceStocks.length}`);
  assert.equal(snapshot.mode, "offline_fixtures");
  assert.ok(snapshot.generatedAt);
  assert.ok(snapshot.focusPoolSize > 0);

  const stock = snapshot.topResonanceStocks[0]!;
  assert.ok(stock.name && stock.code);
  assert.ok(stock.sentiment);
  const total = stock.sentiment.bullRatio + stock.sentiment.divergenceRatio + stock.sentiment.bearRatio;
  assert.ok(Math.abs(total - 1) < 0.02, `三色占比应合计为 1（0~1 口径），实得 ${total}`);
  assert.ok(Array.isArray(stock.highlights));

  const v1 = await get("/api/v1/radar");
  assert.equal(v1.statusCode, 200);
  const wrapped = JSON.parse(v1.body) as { ok: boolean; data: ShortTermRadarSnapshot };
  assert.equal(wrapped.ok, true);
  assert.equal(wrapped.data.topResonanceStocks.length, snapshot.topResonanceStocks.length);
});

test("theme, role and nickname queries filter both views", async () => {
  const all = JSON.parse((await get("/api/site/radar")).body) as ShortTermRadarSnapshot;
  const first = all.topResonanceStocks[0]!;
  const theme = first.themes[0];
  assert.ok(theme, "焦点股应至少属于一个题材");

  const byTheme = JSON.parse((await get(`/api/site/radar?theme=${encodeURIComponent(theme)}`)).body) as ShortTermRadarSnapshot;
  assert.ok(byTheme.themeLadders.length >= 1);
  assert.ok(byTheme.topResonanceStocks.every((stock) => stock.themes.some((name) => name.includes(theme))));

  const byRole = JSON.parse((await get(`/api/site/radar?role=${encodeURIComponent(first.role)}`)).body) as ShortTermRadarSnapshot;
  assert.ok(byRole.topResonanceStocks.length > 0);
  assert.ok(byRole.topResonanceStocks.every((stock) => stock.role === first.role));

  // 黑话外号搜索：社区里没人写全称，「易中天」要能找到那三只光模块票
  const nickname = JSON.parse((await get(`/api/site/radar?q=${encodeURIComponent("易中天")}`)).body) as ShortTermRadarSnapshot;
  assert.ok(nickname.topResonanceStocks.length > 0, "外号搜索应有结果");
  assert.ok(
    nickname.topResonanceStocks.every((stock) => stock.nicknames.some((nick) => nick.includes("易中天")) || stock.name.includes("易中天") || stock.themes.some((t) => t.includes("易中天"))),
    "外号搜索的结果都应命中该外号",
  );

  const byCode = JSON.parse((await get(`/api/site/radar?q=${STOCK_CODE}`)).body) as ShortTermRadarSnapshot;
  assert.ok(byCode.topResonanceStocks.some((stock) => stock.bareCode === STOCK_CODE));
});

test("every ladder stock carries its own theme, a qualified code and the role its summary promises", async () => {
  // The resonance board holds 30 of the 50 focus-pool stocks; the ladders reach the other 20, which
  // arrive with nothing but their bucket. Without the role, the themes and the exchange carried
  // through, a ladder's summary said "容量中军 1 只" while its card read 人气热股, `?theme=` dropped
  // the stock, and `/stock/601127.SH` was a 404 (audit R1, P1-1).
  const snapshot = JSON.parse((await get("/api/site/radar")).body) as ShortTermRadarSnapshot;
  const outsideBoard = snapshot.themeLadders.flatMap((ladder) =>
    ladder.stocks.filter((stock) => !snapshot.topResonanceStocks.some((board) => board.code === stock.code)));
  assert.ok(outsideBoard.length >= 5, `样本应包含未进共振榜的梯队股，实得 ${outsideBoard.length}`);

  for (const ladder of snapshot.themeLadders) {
    for (const stock of ladder.stocks) {
      assert.ok(stock.themes.includes(ladder.theme), `${stock.name} 缺题材 ${ladder.theme}：${JSON.stringify(stock.themes)}`);
      assert.ok(stock.code.includes("."), `${stock.name} 的 code 缺交易所后缀：${stock.code}`);
    }
    if (ladder.summary.includes("容量中军")) {
      assert.ok(ladder.stocks.some((stock) => stock.role === "容量中军"), `${ladder.theme} 摘要写容量中军却没有该身位的股票：${ladder.summary}`);
    }
  }

  // A stock that only exists as a bucket entry is still addressable in all three forms.
  const tail = outsideBoard[0]!;
  const detail = JSON.parse((await get(`/api/site/radar/stock/${tail.code}`)).body) as RadarStockDetail;
  assert.equal(detail.stock.code, tail.code);
  assert.equal(detail.stock.role, tail.role);
  assert.ok(detail.stock.themes.length > 0);

  // And a ladder-level theme filter keeps it.
  const filtered = JSON.parse((await get(`/api/site/radar?theme=${encodeURIComponent(tail.themes[0]!)}`)).body) as ShortTermRadarSnapshot;
  assert.ok(
    filtered.themeLadders.some((ladder) => ladder.stocks.some((stock) => stock.code === tail.code)),
    `${tail.name} 应在 ?theme=${tail.themes[0]} 的结果里`,
  );
});

test("one stock answers by bare code, dotted code and symbol; an unknown code is a 404", async () => {
  const byCode = await get(`/api/site/radar/stock/${STOCK_CODE}`);
  assert.equal(byCode.statusCode, 200, byCode.body);
  const detail = JSON.parse(byCode.body) as RadarStockDetail;
  assert.equal(detail.stock.bareCode, STOCK_CODE);
  assert.equal(detail.stock.code, `${STOCK_CODE}.SZ`);
  assert.ok(detail.stock.symbol.startsWith("SZ") || detail.stock.symbol.startsWith("SH"));
  assert.ok(Array.isArray(detail.themes));

  const bySymbol = await get(`/api/site/radar/stock/${detail.stock.symbol}`);
  assert.equal(bySymbol.statusCode, 200);
  assert.equal((JSON.parse(bySymbol.body) as RadarStockDetail).stock.bareCode, STOCK_CODE);

  const byDotted = await get(`/api/site/radar/stock/${detail.stock.code}`);
  assert.equal(byDotted.statusCode, 200, "带交易所后缀的代码也应命中");

  const v1 = await get(`/api/v1/radar/stock/${detail.stock.symbol.toLowerCase()}`);
  assert.equal(v1.statusCode, 200, "v1 路由同样接受小写 symbol");
  assert.equal(((JSON.parse(v1.body) as { ok: boolean; data: RadarStockDetail }).data).stock.bareCode, STOCK_CODE);

  const missing = await get("/api/site/radar/stock/999999");
  assert.equal(missing.statusCode, 404);
  assert.match(missing.body, /Stock not found/);
});

test("a missing or unreadable snapshot degrades to an empty snapshot instead of failing", async () => {
  const empty = await mkdtemp(path.join(tmpdir(), "radar-empty-"));
  const missing = await loadRadarSnapshot(empty);
  assert.equal(missing.mode, "empty");
  assert.equal(missing.generatedAt, null);
  assert.deepEqual(missing.themeLadders, []);
  assert.deepEqual(missing.topResonanceStocks, []);
  assert.equal(missing.focusPoolSize, 0);

  const broken = await mkdtemp(path.join(tmpdir(), "radar-broken-"));
  await copyFile(path.join(import.meta.dirname, "fixtures", "not-json.json"), path.join(broken, SNAPSHOT));
  const unreadable = await loadRadarSnapshot(broken);
  assert.equal(unreadable.mode, "empty", "损坏的 JSON 也要降级，而不是 500");
  assert.deepEqual(unreadable.topResonanceStocks, []);
});