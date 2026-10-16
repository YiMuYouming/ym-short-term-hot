// Pushed text reaches the article as it stands: a collector that already read the body hands it over
// (body_status 'ok', no second crawl of a URL that answers nothing), and an item without one waits
// for its page exactly as before.
import "./setup.ts";
import assert from "node:assert/strict";
import { after, test } from "node:test";
import { closeDb, sql } from "@aihot/backend/db";
import { IngestError, ingestItems } from "@aihot/backend/ingest/items";
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
