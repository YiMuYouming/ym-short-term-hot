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
  whyHot: string;
  sealTime: string;
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
  /** 板块涨停家数：同义子标签统计取 max 后再与桶内实际涨停数取大（LITE-03，别名计数不相加）。 */
  limitUpCount: number | null;
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
  source?: string;
  postId?: string;
  post_id?: string;
  title?: string;
  content?: string;
  url?: string;
  author?: string;
  authorName?: string;
  author_name?: string;
  publishedAt?: string;
  published_at?: string;
  commentCount?: number;
  comment_count?: number;
  likeCount?: number;
  like_count?: number;
  viewCount?: number;
  view_count?: number;
  isKol?: boolean;
  isVipYouzi?: boolean;
  isDeepLogic?: boolean;
  qualityTier?: string;
  sentiment?: string;
  sentimentLabel?: string;
  sentiment_label?: string;
  sentimentScore?: number;
  sentimentTerms?: string[];
  sentiment_terms?: string[];
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
  limitReason?: string;
  whyHot?: string;
  sealTime?: string;
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
    stockCount?: number;
    limitUpCount?: number | null;
    // LITE-01: a bucket entry is the stock's full dict (whyHot/limitReason/sealTime included),
    // not just identity — the ladders reach stocks the resonance board never lists.
    ladders?: Record<string, FileStock[]>;
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
  const platform = file.platform ?? file.source ?? "";
  const source = PLATFORM_SOURCE[platform] ?? platform ?? "unknown";
  return {
    source,
    postId: file.postId ?? file.post_id ?? file.url ?? `${source}-${index}`,
    title: file.title ?? "",
    // LITE-03: the body when the bridge serialized it, the title otherwise (old snapshots).
    excerpt: file.content ?? file.title ?? "",
    url: file.url ?? "",
    author: file.author ?? file.authorName ?? file.author_name ?? "",
    publishedAt: file.publishedAt ?? file.published_at ?? "",
    readCount: num(file.viewCount ?? file.view_count),
    replyCount: num(file.commentCount ?? file.comment_count),
    likeCount: num(file.likeCount ?? file.like_count),
    isVipYouzi: (file.isKol ?? file.isVipYouzi) === true,
    isDeepLogic: file.isDeepLogic === true,
    sentimentLabel: file.sentiment ?? file.sentimentLabel ?? file.sentiment_label ?? "neutral",
    sentimentScore: num(file.sentimentScore),
    matchedTerms: file.sentimentTerms ?? file.sentiment_terms ?? [],
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
    limitReason: file.limitReason ?? "",
    whyHot: file.whyHot ?? "",
    sealTime: file.sealTime ?? "",
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
    // A bucket entry is the stock's full dict (LITE-03: sentiment + highlights included), and the
    // resonance board holds the same stock with its community data when it made the top N. Either
    // way the stock is mapped once, by mapStock, so no field is silently dropped for the tail
    // (audit P0-4: changePct/amountYi/sentiment/highlights used to collapse to 0/empty for the
    // stocks outside the board).
    const ordered: FileStock[] = [];
    const buckets = theme.ladders ?? {};
    for (const role of ROLE_ORDER) {
      for (const entry of buckets[role] ?? []) {
        if (!entry?.code) continue;
        const base = byCode.get(entry.code);
        ordered.push({
          ...entry,
          ...(base ?? {}),
          code: entry.code,
          // The bucket is where the stock's ladder position lives; a board stock carries its own, and
          // they agree, but the bucket is authoritative for the ladder it is rendered under.
          exchange: base?.exchange ?? entry.exchange ?? exchangeOfSymbol(entry.symbol),
          themes: Array.from(new Set([...(base?.themes ?? []), ...(entry.themes ?? []), ...(themesByCode.get(entry.code) ?? [])])),
          roleLabel: base?.roleLabel ?? entry.roleLabel ?? role,
        });
      }
    }
    const stocks = ordered.map(mapStock);
    return {
      theme: theme.theme ?? "",
      heatScore: Math.round(stocks.reduce((sum, stock) => sum + stock.resonanceScore, 0) * 10) / 10,
      stockCount: stocks.length,
      limitUpCount: theme.limitUpCount ?? null,
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

/** 板块内当日涨停家数（连板数 ≥1 即涨停在池）：热门板块列表的「涨停 N 家」。 */
export function sealedCount(ladder: RadarThemeLadder): number {
  return ladder.stocks.filter((stock) => stock.boardCount >= 1).length;
}

/**
 * 领涨股（LITE-03）：板块内有涨幅的，按 (涨跌幅, 连板, 共振分) 取最高——不能把 -3.67% 的票
 * 写成「领涨」；全绿时才按 (共振分, 涨跌幅) 取代表股。空板块返回 null。
 */
export function leaderStock(ladder: RadarThemeLadder): RadarStockItem | null {
  if (!ladder.stocks.length) return null;
  const rising = ladder.stocks.filter((stock) => stock.changePct > 0);
  if (rising.length) {
    return rising.reduce((best, stock) => {
      if (stock.changePct !== best.changePct) return stock.changePct > best.changePct ? stock : best;
      if (stock.boardCount !== best.boardCount) return stock.boardCount > best.boardCount ? stock : best;
      return stock.resonanceScore > best.resonanceScore ? stock : best;
    });
  }
  return ladder.stocks.reduce((best, stock) =>
    stock.resonanceScore !== best.resonanceScore
      ? stock.resonanceScore > best.resonanceScore ? stock : best
      : stock.changePct > best.changePct ? stock : best,
  );
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