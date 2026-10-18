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
import { leaderStock, mapSnapshot, ROLE_ORDER, sealedCount } from "../contracts.ts";
import type { RadarSnapshotFile, RadarStockDetail, RadarThemeLadder, ShortTermRadarSnapshot } from "../contracts.ts";

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

test("every ladder stock carries its own theme, a qualified code and a summary that matches the data", async () => {
  // LITE-03: top_resonance_limit 默认 50，与焦点池同宽，离线样本里没有「只在梯队」的股票；
  // 尾股字段完整性由下面 mapSnapshot 的合成夹具测试锁定（audit P0-4）。
  const snapshot = JSON.parse((await get("/api/site/radar")).body) as ShortTermRadarSnapshot;
  assert.equal(snapshot.topResonanceStocks.length, 50, "共振榜默认应为 50 只（LITE-03 2.1）");

  for (const ladder of snapshot.themeLadders) {
    for (const stock of ladder.stocks) {
      assert.ok(stock.themes.includes(ladder.theme), `${stock.name} 缺题材 ${ladder.theme}：${JSON.stringify(stock.themes)}`);
      assert.ok(stock.code.includes("."), `${stock.name} 的 code 缺交易所后缀：${stock.code}`);
    }
    // LITE-03：摘要只讲内部结构——写了「最高N板(名称)」就有那只 N 板股
    const topMatch = /最高(\d+)板\(([^)]+)\)/.exec(ladder.summary);
    if (topMatch) {
      const named = ladder.stocks.find((stock) => stock.name === topMatch[2]);
      assert.ok(named, `${ladder.theme} 摘要点了 ${topMatch[2]} 但板块内没有这只股票`);
      assert.equal(named!.boardCount, Number(topMatch[1]), `${topMatch[2]} 的连板数与摘要不符`);
    }
    // 写了「领涨 名称 +x%」那只票就是涨幅最高的（不能把绿股写成领涨）
    const leadMatch = /领涨 ([^ ]+) \+([\d.]+)%/.exec(ladder.summary);
    if (leadMatch) {
      const named = ladder.stocks.find((stock) => stock.name === leadMatch[1]);
      assert.ok(named, `${ladder.theme} 摘要点了领涨 ${leadMatch[1]} 但板块内没有这只股票`);
      assert.ok(named!.changePct > 0, "领涨股必须涨幅为正");
      for (const stock of ladder.stocks.filter((item) => item.changePct > 0)) {
        assert.ok(named!.changePct >= stock.changePct, `${stock.name} 涨幅更高却不是领涨`);
      }
    }
  }

  // 板块内任一股都以三种地址形式可开，且 ?theme= 保留它
  const entry = snapshot.themeLadders[0]!.stocks[0]!;
  const detail = JSON.parse((await get(`/api/site/radar/stock/${entry.code}`)).body) as RadarStockDetail;
  assert.equal(detail.stock.code, entry.code);
  assert.equal(detail.stock.role, entry.role);
  assert.ok(detail.stock.themes.length > 0);
  const filtered = JSON.parse((await get(`/api/site/radar?theme=${encodeURIComponent(entry.themes[0]!)}`)).body) as ShortTermRadarSnapshot;
  assert.ok(
    filtered.themeLadders.some((ladder) => ladder.stocks.some((stock) => stock.code === entry.code)),
    `${entry.name} 应在 ?theme=${entry.themes[0]} 的结果里`,
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

test("the api answers the why-hot facts the minimal page renders (LITE-02)", async () => {
  const snapshot = JSON.parse((await get("/api/site/radar")).body) as ShortTermRadarSnapshot;
  const board = snapshot.topResonanceStocks;
  for (const stock of board) {
    assert.equal(typeof stock.limitReason, "string", `${stock.name} 的 limitReason 应是字符串`);
    assert.equal(typeof stock.whyHot, "string", `${stock.name} 的 whyHot 应是字符串`);
    assert.equal(typeof stock.sealTime, "string", `${stock.name} 的 sealTime 应是字符串`);
  }
  const withWhyHot = board.filter((stock) => stock.whyHot);
  assert.ok(withWhyHot.length > 0, "共振榜应有带 whyHot 的股票");
  assert.ok(withWhyHot.some((stock) => stock.limitReason), "带 whyHot 的股票应同时带一句话 limitReason");
  // 板块视角渲染的梯队股同样带为什么火（LITE-01 起桶内就是完整股票字典）
  const ladderStock = snapshot.themeLadders
    .flatMap((ladder) => ladder.stocks)
    .find((stock) => stock.whyHot && stock.limitReason);
  assert.ok(ladderStock, "梯队股应带 limitReason/whyHot，板块视角才讲得清为什么火");
  // LITE-03：高亮帖带单帖情绪与发布时间——不再七字段假中性
  const posts = board.flatMap((stock) => stock.highlights);
  assert.ok(posts.length > 0, "共振榜应带社区高亮帖");
  assert.ok(
    posts.some((post) => post.sentimentLabel !== "neutral"),
    "高亮帖应带非中性的单帖情绪标签（bull/bear/divergence）",
  );
  assert.ok(posts.some((post) => post.publishedAt), "高亮帖应带发布时间");
});

test("sealedCount and leaderStock describe a ladder for the theme list (LITE-03)", async () => {
  const snapshot = JSON.parse((await get("/api/site/radar")).body) as ShortTermRadarSnapshot;
  const ladder: RadarThemeLadder =
    snapshot.themeLadders.find((item) => item.theme === "低空经济/eVTOL") ?? snapshot.themeLadders[0]!;
  assert.ok(ladder, "快照应有题材梯队");
  assert.ok(sealedCount(ladder) >= 1, "样本第一板块应有涨停股");
  assert.ok(sealedCount(ladder) <= ladder.stockCount, "涨停家数不应超过板块股票数");

  // 领涨按涨幅口径（LITE-03）：有涨幅的股票里 (涨跌幅, 连板, 共振分) 最高，绝不选绿股
  const leader = leaderStock(ladder)!;
  assert.ok(leader, "领涨股不应为空");
  const rising = ladder.stocks.filter((stock) => stock.changePct > 0);
  if (rising.length) {
    assert.ok(leader.changePct > 0, "有涨幅股票时领涨不能是绿股");
    for (const stock of rising) {
      const better =
        stock.changePct > leader.changePct ||
        (stock.changePct === leader.changePct && stock.boardCount > leader.boardCount) ||
        (stock.changePct === leader.changePct && stock.boardCount === leader.boardCount && stock.resonanceScore > leader.resonanceScore);
      assert.ok(!better, `${stock.name} 比领涨 ${leader.name} 更强`);
    }
  } else {
    for (const stock of ladder.stocks) {
      const better =
        stock.resonanceScore > leader.resonanceScore ||
        (stock.resonanceScore === leader.resonanceScore && stock.changePct > leader.changePct);
      assert.ok(!better, `全绿板块里 ${stock.name} 比代表股 ${leader.name} 更该出线`);
    }
  }
});

test("mapSnapshot keeps a ladder-only stock's full facts (LITE-03)", () => {
  // audit P0-4：未进共振榜的梯队股（第 31~50 名场景）曾把 changePct/amountYi/sentiment/
  // highlights 全部归零。合成一份「只有梯队、空共振榜」的快照锁住完整映射。
  const file: RadarSnapshotFile = {
    generatedAt: "2026-10-17T12:00:00+08:00",
    mode: "live",
    themeLadders: [
      {
        theme: "光模块/CPO",
        summary: "最高3板(中际旭创)，领涨 中际旭创 +20.01%",
        stockCount: 1,
        limitUpCount: 3,
        ladders: {
          空间板: [
            {
              code: "300308",
              name: "中际旭创",
              symbol: "SZ300308",
              exchange: "sz",
              themes: ["光模块/CPO"],
              nicknames: ["易中天"],
              roleLabel: "空间板",
              boardCount: 3,
              changePct: 20.01,
              amountYi: 82.6,
              hotRankThs: 2,
              hotRankDc: 1,
              limitReason: "光模块+CPO+算力硬件",
              whyHot: "行业原因：\n1.6T光模块需求持续超预期。",
              sealTime: "09:32:11",
              sentiment: {
                bullCount: 3, divergenceCount: 0, bearCount: 1,
                bullRatio: 75, divergenceRatio: 0, bearRatio: 25,
                validPosts: 4, spamPosts: 1, label: "一致亢奋", posts15m: 0, platforms: ["eastmoney_guba"],
              },
              highlights: [
                {
                  postId: "p1", source: "eastmoney_guba", platform: "eastmoney_guba",
                  title: "易中天集体大长腿", content: "明天继续看反包",
                  publishedAt: "2026-10-16T10:05:00+08:00",
                  commentCount: 260, likeCount: 12, viewCount: 3200,
                  sentiment: "bull", sentimentTerms: ["反包"], author: "韭菜王",
                },
              ],
            },
          ],
        },
      },
    ],
    topResonanceStocks: [],
  };
  const snapshot = mapSnapshot(file);
  const stock = snapshot.themeLadders[0]!.stocks[0]!;
  assert.equal(stock.changePct, 20.01);
  assert.equal(stock.amountYi, 82.6);
  assert.equal(stock.thsRank, 2);
  assert.equal(stock.dcRank, 1);
  assert.equal(stock.limitReason, "光模块+CPO+算力硬件");
  assert.ok(stock.whyHot.includes("行业原因"));
  assert.equal(stock.sealTime, "09:32:11");
  assert.deepEqual(stock.nicknames, ["易中天"]);
  assert.equal(stock.sentiment.validPosts, 4);
  assert.equal(snapshot.themeLadders[0]!.limitUpCount, 3);
  assert.equal(stock.highlights.length, 1);
  assert.equal(stock.highlights[0]!.sentimentLabel, "bull");
  assert.equal(stock.highlights[0]!.publishedAt, "2026-10-16T10:05:00+08:00");
  assert.equal(stock.highlights[0]!.likeCount, 12);
  assert.equal(stock.highlights[0]!.readCount, 3200);
  assert.equal(stock.highlights[0]!.author, "韭菜王");
  assert.deepEqual(stock.highlights[0]!.matchedTerms, ["反包"]);
});

test("mapHighlight reads both camelCase and snake_case post fields (LITE-03)", () => {
  const camel = mapSnapshot({
    topResonanceStocks: [{
      code: "300308", name: "中际旭创", symbol: "SZ300308", exchange: "sz",
      highlights: [{
        postId: "p1", source: "taoguba", title: "T", content: "C",
        publishedAt: "2026-10-16T10:05:00+08:00",
        commentCount: 5, likeCount: 6, viewCount: 7,
        sentiment: "bear", sentimentTerms: ["一字跌停"], author: "A", isKol: true,
      }],
    }],
  });
  const snake = mapSnapshot({
    topResonanceStocks: [{
      code: "300308", name: "中际旭创", symbol: "SZ300308", exchange: "sz",
      highlights: [{
        post_id: "p2", source: "xueqiu", title: "T2", content: "C2",
        published_at: "2026-10-16T09:00:00+08:00",
        comment_count: 8, like_count: 9, view_count: 10,
        sentiment_label: "divergence", sentiment_terms: ["分歧"], author_name: "B",
      }],
    }],
  });
  const camelPost = camel.topResonanceStocks[0]!.highlights[0]!;
  assert.equal(camelPost.postId, "p1");
  assert.equal(camelPost.source, "taoguba");
  assert.equal(camelPost.excerpt, "C");
  assert.equal(camelPost.publishedAt, "2026-10-16T10:05:00+08:00");
  assert.equal(camelPost.replyCount, 5);
  assert.equal(camelPost.likeCount, 6);
  assert.equal(camelPost.readCount, 7);
  assert.equal(camelPost.sentimentLabel, "bear");
  assert.deepEqual(camelPost.matchedTerms, ["一字跌停"]);
  assert.equal(camelPost.isVipYouzi, true);
  const snakePost = snake.topResonanceStocks[0]!.highlights[0]!;
  assert.equal(snakePost.postId, "p2");
  assert.equal(snakePost.publishedAt, "2026-10-16T09:00:00+08:00");
  assert.equal(snakePost.replyCount, 8);
  assert.equal(snakePost.likeCount, 9);
  assert.equal(snakePost.readCount, 10);
  assert.equal(snakePost.sentimentLabel, "divergence");
  assert.equal(snakePost.author, "B");
});

test("the api answers the trade date and four-value post sentiments the header and cards read (LITE-04)", async () => {
  const snapshot = JSON.parse((await get("/api/site/radar")).body) as ShortTermRadarSnapshot;
  assert.equal(typeof snapshot.dataQuality.tradeDate, "string", "页头交易日取自 dataQuality.tradeDate");
  const posts = snapshot.topResonanceStocks.flatMap((stock) => stock.highlights);
  assert.ok(posts.length > 0, "样本应带高亮帖");
  for (const post of posts) {
    assert.ok(
      ["bull", "bear", "divergence", "neutral"].includes(post.sentimentLabel),
      `高亮帖情绪应是 LITE-03 四值之一，实得 ${post.sentimentLabel}`,
    );
  }
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