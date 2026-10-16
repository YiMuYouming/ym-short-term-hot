// The radar's backend: read the snapshot the Python bridge writes, answer the page's loader and the
// public API from it, and give agents and MCP clients the same two views in Markdown.
//
// Two boundaries shape this file:
// - the data directory comes from `config.dataDir` (never a raw `process.env`), so nothing here
//   invents an environment variable the deployment would have to know about;
// - there is no database behind the radar. A missing or unreadable snapshot is not an error: the
//   answers degrade to an empty snapshot with `mode: "empty"`, and the page shows what to run.
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { FastifyInstance, FastifyReply, FastifyRequest } from "fastify";
import { z } from "zod";
import { config } from "@aihot/backend/config";
import { defineServerModule, type AgentAbility } from "@aihot/backend/modules";
import {
  emptyRadarSnapshot,
  filterSnapshot,
  findStock,
  mapSnapshot,
  type RadarFilter,
  type RadarSnapshotFile,
  type ShortTermRadarSnapshot,
} from "./contracts.ts";

const SNAPSHOT_FILE = "short-term-radar-snapshot.json";

/** 页面与 API 的缓存：快照每 15 分钟重算一次，60 秒足够新鲜又不至于让盘中看不到变化。 */
const CACHE = "public, max-age=60, s-maxage=60";
const AGENT_CACHE = "public, max-age=60, s-maxage=60, must-revalidate";

function snapshotPath(dataDir?: string): string {
  return path.join(dataDir ?? config.dataDir, SNAPSHOT_FILE);
}

/**
 * The snapshot, read and mapped. A missing file, an unreadable one or malformed JSON yields the
 * empty snapshot: the page answers 200 with `mode: "empty"` rather than failing the whole site.
 */
export async function loadRadarSnapshot(dataDir?: string): Promise<ShortTermRadarSnapshot> {
  let text: string;
  try {
    text = await readFile(snapshotPath(dataDir), "utf8");
  } catch {
    return emptyRadarSnapshot();
  }
  try {
    const parsed = JSON.parse(text) as RadarSnapshotFile;
    return mapSnapshot(parsed);
  } catch {
    return emptyRadarSnapshot();
  }
}

function filtersOf(req: FastifyRequest): RadarFilter {
  const query = (req.query ?? {}) as Record<string, string | undefined>;
  const pick = (value: unknown): string | null => (typeof value === "string" && value.trim() ? value.trim() : null);
  return { theme: pick(query.theme), role: pick(query.role), q: pick(query.q ?? query.query) };
}

function send(reply: FastifyReply, payload: unknown, etagPrefix: string, cache = CACHE) {
  // A weak validator over the payload: cheap, and a radar refresh must not be cached for ever.
  const body = JSON.stringify(payload ?? null);
  const etag = `W/"${etagPrefix}-${body.length}"`;
  reply.header("etag", etag).header("cache-control", cache).header("content-type", "application/json; charset=utf-8");
  if (reply.request.headers["if-none-match"] === etag) return reply.code(304).send();
  return reply.code(200).send(body);
}

function notFound(reply: FastifyReply, detail: string) {
  return reply
    .code(404)
    .header("cache-control", "public, max-age=30")
    .header("content-type", "application/json; charset=utf-8")
    .send(JSON.stringify({ error: detail }));
}

function fmt(value: number | undefined, suffix = ""): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value}${suffix}` : "—";
}

function stockLine(stock: ShortTermRadarSnapshot["topResonanceStocks"][number]): string {
  const nicknames = stock.nicknames.length ? `（社区黑话：${stock.nicknames.map((n) => `「${n}」`).join("")}）` : "";
  const themes = stock.themes.length ? `${stock.themes.join("、")}｜` : "";
  const hits = stock.platformsHit.length ? `${stock.platformsHit.join("、")}｜` : "";
  return `- **${stock.name}**（${stock.symbol}）${nicknames}｜${stock.role}｜${themes}共振分 ${fmt(stock.resonanceScore)}｜${hits}情绪：${stock.sentiment.label}（看多 ${Math.round(stock.sentiment.bullRatio * 100)}% / 分歧 ${Math.round(stock.sentiment.divergenceRatio * 100)}% / 看空 ${Math.round(stock.sentiment.bearRatio * 100)}%）｜15 分钟 ${stock.sentiment.posts15m} 帖`;
}

function renderMarkdown(snapshot: ShortTermRadarSnapshot, filter: RadarFilter, view: string, limit: number): string {
  const when = snapshot.generatedAt ? `快照时间 ${snapshot.generatedAt}` : "暂无快照";
  const where = [
    filter.theme ? `题材=${filter.theme}` : null,
    filter.role ? `身位=${filter.role}` : null,
    filter.q ? `关键词=${filter.q}` : null,
  ].filter(Boolean).join("，");

  if (snapshot.mode === "empty" || (snapshot.themeLadders.length === 0 && snapshot.topResonanceStocks.length === 0)) {
    return [
      `# 短线情绪雷达：暂无数据`,
      ``,
      `${when}${where ? `（${where}）` : ""}。`,
      ``,
      `快照尚未生成。在项目根目录运行 \`python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run\` 后刷新。`,
    ].join("\n");
  }

  const lines: string[] = [`# 短线情绪雷达`, ``, `${when}｜焦点股池 ${snapshot.focusPoolSize} 只${where ? `｜${where}` : ""}｜模式 ${snapshot.mode}`, ``];

  if (view === "resonance") {
    const top = snapshot.topResonanceStocks.slice(0, limit);
    lines.push(`## 跨平台人气共振 Top ${top.length}`, ``, ...top.map((stock) => stockLine(stock)), ``);
  } else if (view === "ladders") {
    lines.push(`## 题材主线梯队`, ``);
    for (const ladder of snapshot.themeLadders.slice(0, limit)) {
      lines.push(`### ${ladder.theme}｜${ladder.stockCount} 只｜最高 ${ladder.topBoardCount} 板`, ``, ...ladder.stocks.map((stock) => stockLine(stock)), ``);
    }
  } else {
    lines.push(`## 题材主线梯队`, ``);
    for (const ladder of snapshot.themeLadders.slice(0, Math.max(1, Math.floor(limit / 3)))) {
      lines.push(`### ${ladder.theme}｜${ladder.stockCount} 只｜最高 ${ladder.topBoardCount} 板`, ``, ...ladder.stocks.map((stock) => stockLine(stock)), ``);
    }
    lines.push(`## 跨平台人气共振 Top ${Math.min(limit, snapshot.topResonanceStocks.length)}`, ``, ...snapshot.topResonanceStocks.slice(0, limit).map((stock) => stockLine(stock)), ``);
  }

  const youzi = snapshot.topResonanceStocks.flatMap((stock) => stock.highlights.filter((h) => h.isVipYouzi).map((h) => `${stock.name}：${h.title}`));
  if (youzi.length) lines.push(`## 游资复盘摘录`, ``, ...youzi.slice(0, limit).map((line) => `- ${line}`), ``);
  return lines.join("\n");
}

const abilityInput = z.strictObject({
  view: z.enum(["ladders", "resonance", "all"]).optional(),
  theme: z.string().optional(),
  role: z.string().optional(),
  query: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional(),
});

const radarAbility: AgentAbility = {
  path: "/radar",
  title: "短线情绪雷达",
  ask: "当前 A 股短线题材梯队与人气共振榜（支持题材、身位、股票或黑话外号过滤）",
  etagPrefix: "radar",
  cacheControl: AGENT_CACHE,
  answer: async () => renderMarkdown(await loadRadarSnapshot(), {}, "all", 15),
  mcp: {
    tool: "get_radar",
    use: "for the A-share short-term theme ladders and the cross-platform resonance board",
    description: "短线情绪雷达：题材主线梯队、跨平台人气共振榜、社区三色情绪与游资/雪球高价值帖。",
    input: abilityInput,
    run: async (args) => {
      const limit = typeof args.limit === "number" ? args.limit : 15;
      const view = typeof args.view === "string" ? args.view : "all";
      const snapshot = filterSnapshot(await loadRadarSnapshot(), {
        theme: typeof args.theme === "string" ? args.theme : null,
        role: typeof args.role === "string" ? args.role : null,
        q: typeof args.query === "string" ? args.query : null,
      });
      const text = renderMarkdown(snapshot, {}, view, limit);
      return { text, structured: { snapshot } };
    },
  },
};

export default defineServerModule({
  name: "short-term-radar",
  http(app: FastifyInstance) {
    for (const prefix of ["/api/site", "/api/v1"]) {
      app.get(`${prefix}/radar`, async (req, reply) => {
        const snapshot = filterSnapshot(await loadRadarSnapshot(), filtersOf(req));
        return send(reply, prefix === "/api/v1" ? { ok: true, data: snapshot } : snapshot, `radar${req.url}`);
      });

      app.get(`${prefix}/radar/stock/:code`, async (req, reply) => {
        const code = (req.params as { code?: string }).code ?? "";
        const detail = findStock(await loadRadarSnapshot(), code);
        if (!detail) return notFound(reply, "Stock not found in radar snapshot");
        return send(reply, prefix === "/api/v1" ? { ok: true, data: detail } : detail, `radar-stock-${code}`);
      });
    }
  },
  agent: {
    abilities: [radarAbility],
    requests: ["短线雷达：GET /api/v1/radar?theme=&role=&q=（q 支持「易中天」「寒王」等社区黑话）"],
  },
});