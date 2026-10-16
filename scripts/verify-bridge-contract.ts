// Cross-language contract check: the payloads `bridge/push_to_aihot.py` really produces, pushed
// through the real `ingestItems()` and the real timeline rules. A Python unit test cannot see
// `normalizeUrl()` dropping a non-http scheme or `decideTimeline()` turning an undated item into a
// backfill — those are the two ways a "successful" push silently delivers nothing (audit R1).
//
//   python3 -m bridge.run_bridge --offline-fixtures --dry-run --dump-payloads /tmp/bridge-payloads.json
//   DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test node --import ./tests/databases.ts scripts/verify-bridge-contract.ts
//
// It works on a database of its own (created on the same server, migrated, dropped afterwards).
// Material identity is the normalized URL, so pushing the same payload twice into a shared database
// reports `created: 0` the second time and hides whether the first run really created rows. A clean
// database makes the verdict unambiguous: every item created, dated as today's news.
//
// Not part of `node --test tests/`: it needs a payload file produced by the Python side.
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import postgres from "postgres";

// The four tracks bridge writes to, and the participation mode each one needs to do its job.
const TRACKS: Record<string, "editorial" | "hot_signal"> = {
  "external-ym-pipeline": "editorial",
  "external-taoguba-hot": "editorial",
  "external-xueqiu-hot": "editorial",
  "external-eastmoney-guba": "hot_signal",
};

const { values } = parseArgs({ options: { payloads: { type: "string", default: "/tmp/bridge-payloads.json" } } });
const payload = JSON.parse(readFileSync(values.payloads!, "utf8")) as Record<string, { items: Array<Record<string, unknown>> }>;

const adminUrl = new URL(process.env.DATABASE_URL ?? "postgres://127.0.0.1:5432/ymhot_test");
const database = `bridge_contract_${process.pid}`;
const urlOf = (name: string) => {
  const url = new URL(adminUrl);
  url.pathname = `/${name}`;
  return url.toString();
};

const admin = postgres(urlOf("postgres"), { max: 1 });
try {
  await admin`CREATE DATABASE ${admin(database)}`;
} catch (error) {
  console.error("无法创建一次性校验库：", error instanceof Error ? error.message : error);
  await admin.end();
  process.exit(1);
}
process.env.DATABASE_URL = urlOf(database);

let failures = 0;
try {
  execFileSync(process.execPath, [fileURLToPath(new URL("./migrate.ts", import.meta.url))], { stdio: ["ignore", "ignore", "inherit"] });

  const { sql, closeDb } = await import("@aihot/backend/db");
  const { ingestItems } = await import("@aihot/backend/ingest/items");
  const { settleNonEditorial } = await import("@aihot/backend/jobs/content");
  const { stopBoss } = await import("@aihot/backend/jobs/queue");

  for (const [sourceId, mode] of Object.entries(TRACKS)) {
    const body = payload[sourceId];
    if (!body?.items.length) {
      console.log(`跳过 ${sourceId}：payload 里没有条目`);
      continue;
    }
    await sql`INSERT INTO sources (id, name, kind, config, tier, participation_mode, enabled, health)
      VALUES (${sourceId}, ${sourceId}, 'external', '{}'::jsonb, 'T2', ${mode}, true, 'ok')`;

    const out = await ingestItems({ sourceId, items: body.items });
    const rows = await sql<{ id: string; backfill: boolean; published_at: Date | null; body_status: string; body_text: string | null }[]>`
      SELECT id, backfill, published_at, body_status, body_text FROM articles WHERE source_id = ${sourceId}`;
    const backfill = rows.filter((row) => row.backfill).length;
    const undated = rows.filter((row) => !row.published_at).length;

    // The two failure modes this script exists to catch.
    assert.equal(out.created, body.items.length, `${sourceId}: 只入库 ${out.created}/${body.items.length} 条（URL 或标题被丢弃）`);
    assert.equal(backfill, 0, `${sourceId}: ${backfill} 条被判历史回填（缺 publishedAt 或过期）`);
    assert.equal(undated, 0, `${sourceId}: ${undated} 条没有发布时间`);

    const verdict: Record<string, unknown> = { planned: body.items.length, created: out.created, backfill, undated };
    if (mode === "hot_signal") {
      const [pulse] = rows;
      assert.ok(pulse, "股吧轨应有入库行");
      const settled = await settleNonEditorial(pulse!.id);
      assert.deepEqual(settled, { group: true }, "hot_signal 脉冲必须能进事件热度归组");
      verdict.settleNonEditorial = settled;
    } else {
      const [report] = rows;
      assert.equal(report!.body_status, "ok", "editorial 轨应带着推送的正文入库，不再等二次抓取");
      verdict.bodyChars = report!.body_text?.length ?? 0;
    }
    console.log(`${sourceId}（${mode}）`, JSON.stringify(verdict));
  }
  console.log("\n跨语言契约校验通过：四轨 payload 全部被后端接受，且都是当日新闻而非历史回填。");
} catch (error) {
  failures = 1;
  console.error("跨语言契约校验失败：", error instanceof Error ? error.message : error);
} finally {
  try {
    const { closeDb } = await import("@aihot/backend/db");
    const { stopBoss } = await import("@aihot/backend/jobs/queue");
    await stopBoss();
    await closeDb();
  } catch {
    // the backend may never have loaded if migrate failed
  }
  await admin`DROP DATABASE IF EXISTS ${admin(database)} WITH (FORCE)`;
  await admin.end();
}

process.exit(failures);