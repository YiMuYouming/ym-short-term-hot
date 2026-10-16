// What the radar shows, in two shapes:
//
// - `RadarSnapshotFile` is what `bridge/run_bridge.py` writes to
//   `.data/short-term-radar-snapshot.json` — read verbatim, never rewritten;
// - `ShortTermRadarSnapshot` is what the api answers with and the web renders: the same facts under
//   the names the site's views use.
//
// The two differ because the bridge's schema is the collector's (role buckets per theme, ratios in
// 0~100) while a page wants one flat list per theme and 0~1 ratios. The mapping is here, in one file
// with no imports, so both sides agree on it: the backend maps on the way out, the web reads only the
// mapped shape, and a test pins the translation.
//
// Frontend-safe: types and pure functions only, no backend imports (architecture red line A).

/** 三类情绪占比（0~1），页面用 A 股红/琥珀/绿三色条渲染。 */
export interface RadarStockSentiment {
  bullRatio: number;
  divergenceRatio: number;
  bearRatio: number;
  validPosts: number;
  spamPosts: number;
  posts15m: number;
  label: string;
}

/** 三社区里一条被挑出来的高价值帖子。 */
export interface RadarHighlightPost {
  source: string;
  postId: string;
  title: string;
  excerpt: string;
  url: string;
  author: string;
  publishedAt: string;
  readCount: number;
  replyCount: number;
  likeCount: number;
  isVipYouzi: boolean;
  isDeepLogic: boolean;
  sentimentLabel: string;
  sentimentScore: number;
  matchedTerms: string[];
}

/** 一只焦点股在一个视图里的全部字段。 */
export interface RadarStockItem {
  code: string;
  symbol: string;
  bareCode: string;
  name: string;
  nicknames: string[];
  themes: string[];
  role: string;
  boardCount: number;
  changePct: number;
  turnoverRate: number;
  amountYi: number;
  thsRank: number | null;
  dcRank: number | null;
  kplTag: string;
  limitReason: string;
  resonanceScore: number;
  platformsHit: string[];
  sentiment: RadarStockSentiment;
  highlights: RadarHighlightPost[];
}

/** 一个题材主线及其梯队（按身位拍平后的有序列表）。 */
export interface RadarThemeLadder {
  theme: string;
  heatScore: number;
  stockCount: number;
  topBoardCount: number;
  summary: string;
  stocks: RadarStockItem[];
}

export interface ShortTermRadarSnapshot {
  generatedAt: string | null;
  mode: string;
  dataQuality: Record<string, unknown>;
  focusPoolSize: number;
  themeLadders: RadarThemeLadder[];
  topResonanceStocks: RadarStockItem[];
}

/** One stock as the bridge wrote it (percentages 0~100, highlights in the collector's field names). */
interface FileSentiment {
  code?: string;
  totalPosts?: number;
  validPosts?: number;
  spamPosts?: number;
  bullCount?: number;
  divergenceCount?: number;
  bearCount?: number;
  bullRatio?: number;
  divergenceRatio?: number;
  bearRatio?: number;
  label?: string;
  posts15m?: number;
  platforms?: string[];
}

interface FileHighlight {
  platform?: string;
  title?: string;
  url?: string;
  authorName?: string;
  isVipYouzi?: boolean;
  isDeepLogic?: boolean;
  commentCount?: number;
  publishedAt?: string;
  sentiment?: string;
  sentimentScore?: number;
  sentimentTerms?: string[];
}

interface FileStock {
  code?: string;
  name?: string;
  symbol?: string;
  exchange?: string;
  themes?: string[];
  nicknames?: string[];
  roleLabel?: string;
  boardCount?: number;
  changePct?: number | null;
  amountYi?: number | null;
  hotRankThs?: number | null;
  hotRankDc?: number | null;
  hotRankXq?: number | null;
  resonanceScore?: number;
  platformsHit?: string[];
  sentiment?: FileSentiment;
  highlights?: FileHighlight[];
}

/** A theme as the bridge wrote it: one bucket per role, not a flat list. */
export interface RadarSnapshotFile {
  generatedAt?: string | null;
  mode?: string;
  dataQuality?: Record<string, unknown>;
  focusPoolSize?: number;
  themeLadders?: Array<{
    theme?: string;
    summary?: string;
    ladders?: Record<string, Array<{ code?: string; name?: string; symbol?: string; boardCount?: number; resonanceScore?: number }>>;
  }>;
  topResonanceStocks?: FileStock[];
}

/** 身位在梯队里的顺序：最高的梯队排前面。 */
export const ROLE_ORDER = ["空间板", "20cm弹性", "容量中军", "首板发酵", "人气热股"] as const;

const PLATFORM_SOURCE: Record<string, string> = {
  taoguba: "taoguba",
  xueqiu: "xueqiu",
  eastmoney_guba: "eastmoney_guba",
};

const PLATFORM_LABEL: Record<string, string> = {
  taoguba: "淘股吧",
  xueqiu: "雪球",
  eastmoney_guba: "东财股吧",
};

/** 三社区的展示顺序。 */
export const PLATFORM_LABELS: Array<{ key: string; label: string }> = [
  { key: "all", label: "全部" },
  { key: "taoguba", label: PLATFORM_LABEL.taoguba! },
  { key: "xueqiu", label: PLATFORM_LABEL.xueqiu! },
  { key: "eastmoney_guba", label: PLATFORM_LABEL.eastmoney_guba! },
];

/** The empty snapshot the api answers with when there is no file yet (never a 500). */
export function emptyRadarSnapshot(): ShortTermRadarSnapshot {
  return { generatedAt: null, mode: "empty", dataQuality: {}, focusPoolSize: 0, themeLadders: [], topResonanceStocks: [] };
}

function ratio(value: number | undefined): number {
  if (!value || !Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value / 100));
}

/** `SZ300308` → `SZ`; anything else stays undefined so the code is left bare rather than guessed. */
function exchangeOfSymbol(symbol: string | undefined): string | undefined {
  return symbol?.match(/^(SH|SZ|BJ)/i)?.[1]?.toUpperCase();
}

function num(value: number | null | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function mapSentiment(file: FileSentiment | undefined): RadarStockSentiment {
  return {
    bullRatio: ratio(file?.bullRatio),
    divergenceRatio: ratio(file?.divergenceRatio),
    bearRatio: ratio(file?.bearRatio),
    validPosts: num(file?.validPosts),
    spamPosts: num(file?.spamPosts),
    posts15m: num(file?.posts15m),
    label: file?.label || "讨论平淡",
  };
}

function mapHighlight(file: FileHighlight, index: number): RadarHighlightPost {
  const source = PLATFORM_SOURCE[file.platform ?? ""] ?? file.platform ?? "unknown";
  return {
    source,
    postId: file.url ?? `${source}-${index}`,
    title: file.title ?? "",
    excerpt: file.title ?? "",
    url: file.url ?? "",
    author: file.authorName ?? "",
    publishedAt: file.publishedAt ?? "",
    readCount: 0,
    replyCount: num(file.commentCount),
    likeCount: 0,
    isVipYouzi: file.isVipYouzi === true,
    isDeepLogic: file.isDeepLogic === true,
    sentimentLabel: file.sentiment ?? "neutral",
    sentimentScore: num(file.sentimentScore),
    matchedTerms: file.sentimentTerms ?? [],
  };
}

function mapStock(file: FileStock): RadarStockItem {
  const bare = file.code ?? "";
  const exchange = (file.exchange ?? "").toUpperCase();
  // The site's address form for a stock: `300308.SZ`, with `bareCode` for the exchange-free code the
  // collectors use and `symbol` for the prefixed one (`SZ300308`). Accepting all three in a lookup is
  // what lets an agent paste whichever it has.
  const qualified = exchange ? `${bare}.${exchange}` : bare;
  return {
    code: qualified,
    symbol: file.symbol ?? bare,
    bareCode: bare,
    name: file.name ?? bare,
    nicknames: file.nicknames ?? [],
    themes: file.themes ?? [],
    role: file.roleLabel ?? "人气热股",
    boardCount: num(file.boardCount),
    changePct: num(file.changePct),
    turnoverRate: 0, // 换手率不在快照里（bridge 未采），页面按 0 显示「—」
    amountYi: num(file.amountYi),
    thsRank: file.hotRankThs ?? null,
    dcRank: file.hotRankDc ?? null,
    kplTag: "", // 开盘啦标签本阶段无来源（kpl intent 在 pipeline 中不存在）
    limitReason: "",
    resonanceScore: num(file.resonanceScore),
    platformsHit: file.platformsHit ?? [],
    sentiment: mapSentiment(file.sentiment),
    highlights: (file.highlights ?? []).map(mapHighlight),
  };
}

/** File → api shape. Unknown or missing fields become empty values, never exceptions. */
export function mapSnapshot(file: RadarSnapshotFile | null | undefined): ShortTermRadarSnapshot {
  if (!file || typeof file !== "object") return emptyRadarSnapshot();
  const byCode = new Map<string, FileStock>();
  for (const stock of file.topResonanceStocks ?? []) {
    if (stock?.code) byCode.set(stock.code, stock);
  }

  // The resonance board holds the top 30, but the theme ladders reach across the whole focus pool
  // (50). Everything outside the board is described only by its ladder bucket, so collect from all
  // of them which themes a stock belongs to: without this the tail stocks arrive with no themes at
  // all, which both drops them from `?theme=` and makes a ladder's summary contradict its cards.
  const themesByCode = new Map<string, string[]>();
  for (const theme of file.themeLadders ?? []) {
    const name = theme?.theme;
    if (!name) continue;
    for (const bucket of Object.values(theme.ladders ?? {})) {
      for (const entry of bucket ?? []) {
        if (!entry?.code) continue;
        const list = themesByCode.get(entry.code) ?? [];
        if (!list.includes(name)) list.push(name);
        themesByCode.set(entry.code, list);
      }
    }
  }

  const ladders = (file.themeLadders ?? []).map((theme) => {
    // The buckets hold only identity + a few numbers; the full item comes from the resonance board
    // when it is there, and from the bucket (role, themes, exchange) when it is not.
    const ordered: FileStock[] = [];
    const buckets = theme.ladders ?? {};
    for (const role of ROLE_ORDER) {
      for (const entry of buckets[role] ?? []) {
        if (!entry?.code) continue;
        const base = byCode.get(entry.code);
        ordered.push({
          ...base,
          code: entry.code,
          name: base?.name ?? entry.name,
          symbol: base?.symbol ?? entry.symbol,
          // The bucket is where the stock's ladder position lives; a board stock carries its own, and
          // they agree, but the bucket is authoritative for the ladder it is rendered under.
          exchange: base?.exchange ?? exchangeOfSymbol(entry.symbol),
          themes: Array.from(new Set([...(base?.themes ?? []), ...(themesByCode.get(entry.code) ?? [])])),
          roleLabel: base?.roleLabel ?? role,
          boardCount: base?.boardCount ?? entry.boardCount,
          resonanceScore: base?.resonanceScore ?? entry.resonanceScore,
        });
      }
    }
    const stocks = ordered.map(mapStock);
    return {
      theme: theme.theme ?? "",
      heatScore: Math.round(stocks.reduce((sum, stock) => sum + stock.resonanceScore, 0) * 10) / 10,
      stockCount: stocks.length,
      topBoardCount: stocks.reduce((top, stock) => Math.max(top, stock.boardCount), 0),
      summary: theme.summary ?? "",
      stocks,
    };
  });

  return {
    generatedAt: file.generatedAt ?? null,
    mode: file.mode ?? "empty",
    dataQuality: file.dataQuality ?? {},
    focusPoolSize: num(file.focusPoolSize),
    themeLadders: ladders.filter((ladder) => ladder.theme),
    topResonanceStocks: (file.topResonanceStocks ?? []).map(mapStock),
  };
}

export interface RadarFilter {
  theme?: string | null;
  role?: string | null;
  q?: string | null;
}

/** `q` 命中代码、名称、黑话外号（易中天 / 寒王 / 宁王）或题材名。 */
export function matchesQuery(stock: RadarStockItem, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;
  return [stock.code, stock.symbol, stock.name, ...stock.nicknames, ...stock.themes, stock.role]
    .some((field) => field.toLowerCase().includes(needle));
}

function keeps(stock: RadarStockItem, filter: RadarFilter): boolean {
  if (filter.theme && !stock.themes.some((theme) => theme.includes(filter.theme!))) return false;
  if (filter.role && stock.role !== filter.role) return false;
  if (filter.q && !matchesQuery(stock, filter.q)) return false;
  return true;
}

/** Filters both views by the same predicate, so a filtered page never shows a stock in one view and not the other. */
export function filterSnapshot(snapshot: ShortTermRadarSnapshot, filter: RadarFilter): ShortTermRadarSnapshot {
  const active = !!(filter.theme || filter.role || filter.q);
  if (!active) return snapshot;
  return {
    ...snapshot,
    themeLadders: snapshot.themeLadders
      .map((ladder) => ({
        ...ladder,
        stocks: ladder.stocks.filter((stock) => keeps(stock, filter)),
        stockCount: ladder.stocks.filter((stock) => keeps(stock, filter)).length,
      }))
      .filter((ladder) => ladder.stocks.length > 0 || (!!filter.theme && ladder.theme.includes(filter.theme!))),
    topResonanceStocks: snapshot.topResonanceStocks.filter((stock) => keeps(stock, filter)),
  };
}

/** One stock with the themes it belongs to, for the detail route. */
export interface RadarStockDetail {
  stock: RadarStockItem;
  themes: RadarThemeLadder[];
}

function stockMatches(stock: RadarStockItem, needle: string): boolean {
  if (stock.code.toUpperCase() === needle || stock.symbol.toUpperCase() === needle || stock.bareCode.toUpperCase() === needle) return true;
  // A bare code pasted without knowing the suffix still resolves.
  return /^\d{6}$/.test(needle) && stock.bareCode === needle;
}

export function findStock(snapshot: ShortTermRadarSnapshot, query: string): RadarStockDetail | null {
  const needle = query.trim().toUpperCase();
  if (!needle) return null;
  const inBoard = snapshot.topResonanceStocks.find((stock) => stockMatches(stock, needle));
  const inLadders = snapshot.themeLadders
    .flatMap((ladder) => ladder.stocks)
    .find((stock) => stockMatches(stock, needle));
  const stock = inBoard ?? inLadders;
  if (!stock) return null;
  const themes = snapshot.themeLadders.filter((ladder) => ladder.stocks.some((item) => item.bareCode === stock.bareCode));
  return { stock, themes };
}

/** The platform status a header badge shows: what the bridge recorded for each source. */
export function sourceBadges(snapshot: ShortTermRadarSnapshot): Array<{ label: string; status: string }> {
  const sources = (snapshot.dataQuality?.sources ?? {}) as Record<string, { status?: string; provider?: string; rows?: number }>;
  const label: Record<string, string> = {
    ths_hot: "同花顺热榜",
    dc_hot: "东财热榜",
    intraday: "盘中涨跌停",
  };
  return Object.entries(label).map(([key, text]) => ({
    label: text,
    status: sources[key]?.status ?? "unavailable",
  }));
}