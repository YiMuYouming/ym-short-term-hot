// Pushed text reaches the article as it stands: a collector that already read the body hands it over
// (body_status 'ok', no second crawl of a URL that answers nothing), and an item without one waits
// for its page exactly as before.
// Plus the cross-language contract with the Python bridge (audit R1): what `bridge/push_to_aihot.py`
// actually sends must survive normalizeUrl() and keep its publication time, or the whole push is
// silently lost (created 0) or degraded to history (every item a backfill that joins no event).
import "./setup.ts";
import assert from "node:assert/strict";
import { after, test } from "node:test";
import { closeDb, sql } from "@aihot/backend/db";
import { IngestError, ingestItems } from "@aihot/backend/ingest/items";
import { settleNonEditorial } from "@aihot/backend/jobs/content";
import { QUEUES, stopBoss } from "@aihot/backend/jobs/queue";
import { tag } from "./setup.ts";

after(async () => {
  await stopBoss();
  await closeDb();
});

test("a paused external source rejects pushed items without recording a successful fetch", async () => {
  const sourceId = `test-paused-ingest-${tag()}`;
  const lastOkAt = new Date("2026-09-01T00:00:00Z");
  await sql`
    INSERT INTO sources (id, name, kind, config, tier, participation_mode, enabled, health, last_ok_at)
    VALUES (${sourceId}, 'Paused external source', 'external', '{}'::jsonb, 'T2', 'editorial', false, 'paused', ${lastOkAt})`;

  await assert.rejects(
    ingestItems({ sourceId, items: [{ title: "New report", url: `https://example.org/${sourceId}` }] }),
    (error: unknown) => error instanceof IngestError && error.status === 409,
  );

  const [source] = await sql<{ last_ok_at: Date }[]>`SELECT last_ok_at FROM sources WHERE id = ${sourceId}`;
  const [articles] = await sql<{ count: number }[]>`SELECT count(*)::int AS count FROM articles WHERE source_id = ${sourceId}`;
  assert.equal(source!.last_ok_at.toISOString(), lastOkAt.toISOString());
  assert.equal(articles!.count, 0);

  await sql`UPDATE sources SET enabled = true WHERE id = ${sourceId}`;
  assert.deepEqual(await ingestItems({ sourceId, items: [{ title: "New report", url: `https://example.org/${sourceId}` }] }), { ok: true, created: 1 });
});

test("pushed bodyText lands as read content; an item without one still waits for its page", async () => {
  const t = tag();
  const editorial = `test-ingest-body-${t}`;
  const signal = `test-ingest-body-signal-${t}`;
  await sql`
    INSERT INTO sources (id, name, kind, config, tier, participation_mode, enabled, health)
    VALUES (${editorial}, 'Ingest body', 'external', '{}'::jsonb, 'T2', 'editorial', true, 'ok'),
           (${signal}, 'Ingest signal', 'external', '{}'::jsonb, 'T2', 'hot_signal', true, 'ok')`;
  const body = "主线题材催化：算力龙头三连板，封板时间提前至早盘。".repeat(3);

  assert.deepEqual(await ingestItems({ sourceId: editorial, items: [
    { title: `透传正文的战报 ${t}`, url: `https://pipeline.local/editorial/${t}`, bodyText: ` ${body} `, excerpt: "  算力龙头三连板  " },
  ] }), { ok: true, created: 1 });
  assert.deepEqual(await ingestItems({ sourceId: signal, items: [
    { title: `只有标题的脉冲 ${t}`, url: `https://pipeline.local/signal/${t}` },
  ] }), { ok: true, created: 1 });

  const [passed] = await sql<{ body_status: string; body_text: string | null; excerpt: string | null }[]>`
    SELECT body_status, body_text, excerpt FROM articles WHERE source_id = ${editorial}`;
  assert.deepEqual(passed, { body_status: "ok", body_text: body, excerpt: "算力龙头三连板" }, "the pushed text is trimmed and stored as read");
  const [waiting] = await sql<{ body_status: string; body_text: string | null }[]>`
    SELECT body_status, body_text FROM articles WHERE source_id = ${signal}`;
  assert.deepEqual(waiting, { body_status: "pending", body_text: null }, "without pushed text the item still waits for its page");

  // The pushed item is judged as it stands; the worker never crawls a URL whose body is known.
  const [job] = await sql<{ name: string }[]>`SELECT name FROM pgboss.job WHERE data->>'articleId' = (SELECT id FROM articles WHERE source_id = ${editorial})`;
  assert.equal(job?.name, QUEUES.analyze);
});

test("the bridge's four-track payload is accepted as today's news and joins event heat", async () => {
  const t = tag();
  const editorial = `test-bridge-track-${t}`;
  const signal = `test-bridge-signal-${t}`;
  await sql`
    INSERT INTO sources (id, name, kind, config, tier, participation_mode, enabled, health)
    VALUES (${editorial}, 'YM pipeline bridge', 'external', '{}'::jsonb, 'T2', 'editorial', true, 'ok'),
           (${signal}, 'Eastmoney guba pulse', 'external', '{}'::jsonb, 'T2', 'hot_signal', true, 'ok')`;

  // The exact shapes bridge/push_to_aihot.py emits: a pipeline report with pushed bodyText, and a
  // guba pulse with title+excerpt only. publishedAt is the batch time; the URL is a real page with a
  // trade-date parameter (normalizeUrl rejects any non-http scheme and drops tracking params).
  const publishedAt = new Date().toISOString();
  // The trade-date parameter is what bridge sends in production; `t` keeps each run's identity unique,
  // otherwise a rerun would revise the row left by the previous run instead of creating one.
  assert.deepEqual(await ingestItems({ sourceId: editorial, items: [{
    title: "中际旭创(300308) 空间板｜一致亢奋｜共振 60.2",
    url: `https://quote.eastmoney.com/sz300308.html?date=2026-10-16&t=${t}`,
    publishedAt,
    author: "YM-data-pipeline",
    excerpt: "光模块/CPO；空间板；社区情绪一致亢奋，15 分钟 3 条新帖",
    bodyText: "# 中际旭创（SZ300308）空间板\n\n- 题材归属：光模块/CPO\n- 社区黑话：易中天、旭创\n- 跨平台共振分：60.2（命中：同花顺热榜#1、东财热榜#1）\n",
    raw: { _aihot: { backfill: false, baseline: false }, ymhot: { kind: "radar_stock", code: "300308" } },
  }] }), { ok: true, created: 1 });
  assert.deepEqual(await ingestItems({ sourceId: signal, items: [{
    title: "易中天集体大长腿，明天继续看反包",
    url: `https://guba.eastmoney.com/news,300308,900000001.html?t=${t}`,
    publishedAt,
    author: "追涨打板",
    excerpt: "今天光模块主线继续强势，易中天三兄弟集体大长腿，明天重点看反包强度。",
    raw: { _aihot: { backfill: false, baseline: false }, ymhot: { kind: "community_post", platform: "eastmoney_guba", code: "300308" } },
  }] }), { ok: true, created: 1 });

  // Not dropped by normalizeUrl, dated as today rather than a backfill, and read as-is.
  const [report] = await sql<{ backfill: boolean; backfill_reason: string | null; published_at: Date | null; body_status: string; body_text: string | null }[]>`
    SELECT backfill, backfill_reason, published_at, body_status, body_text FROM articles WHERE source_id = ${editorial}`;
  assert.equal(report!.backfill, false, `an undated push would be backfill (${report!.backfill_reason})`);
  assert.equal(report!.backfill_reason, null);
  assert.ok(report!.published_at, "the publication time the bridge sent must survive");
  assert.equal(report!.body_status, "ok");

  const [pulse] = await sql<{ id: string; backfill: boolean; published_at: Date | null }[]>`
    SELECT id, backfill, published_at FROM articles WHERE source_id = ${signal}`;
  assert.equal(pulse!.backfill, false);
  assert.ok(pulse!.published_at);

  // A hot_signal pulse is only event heat evidence while it is today's; a backfill returns { group: false }.
  assert.deepEqual(await settleNonEditorial(pulse!.id), { group: true });
});
