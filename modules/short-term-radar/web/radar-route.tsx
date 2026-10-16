// The radar page: two views over one snapshot — the theme ladders (what the主线 is doing) and the
// cross-platform resonance board (what everyone is looking at) — plus a per-stock drawer with the
// community posts behind the number.
//
// Data comes from the api over HTTP only (`apiGet("/api/site/radar")`); this file never touches the
// database or the backend package (architecture red line A). The bridge writes the snapshot, the api
// maps it (modules/short-term-radar/contracts.ts) and this page renders what comes back.
import { useMemo, useRef, useState } from "react";
import { Link, useSearchParams, type MetaFunction } from "react-router";
import { SITE, subjectAfter, withSubject } from "@aihot/site";
import { apiGet, cachedPage, pageHeaders } from "@aihot/web/lib/api.server";
import { pageMeta } from "@aihot/web/lib/seo";
import { Badge } from "@aihot/web/components/ui/Badge";
import { EmptyState } from "@aihot/web/components/ui/Page";
import { Presence } from "@aihot/web/components/ui/Presence";
import { useModal } from "@aihot/web/components/ui/modal";
import { IconClose } from "@aihot/web/components/icons";
import {
  PLATFORM_LABELS,
  ROLE_ORDER,
  matchesQuery,
  sourceBadges,
  type RadarHighlightPost,
  type RadarStockItem,
  type RadarThemeLadder,
  type ShortTermRadarSnapshot,
} from "../contracts.ts";

export { pageHeaders as headers } from "@aihot/web/lib/api.server";

/** The filters the api understands. `view` and `stock` are the page's own state and stay here. */
const SERVER_FILTERS = ["q", "theme", "role"] as const;

export async function loader({ request }: { request: Request }) {
  // Filtering happens on the server, not only in the component: React Router inlines the loader's
  // data into the document, so a link like /radar?q=易中天 must arrive pre-filtered or the unfiltered
  // payload is what ships to the browser (audit R1, P1-2).
  const url = new URL(request.url);
  const filters = new URLSearchParams();
  for (const key of SERVER_FILTERS) {
    const value = url.searchParams.get(key);
    if (value) filters.set(key, value);
  }
  const query = filters.toString();
  const path = query ? `/api/site/radar?${query}` : "/api/site/radar";
  return cachedPage(60, await apiGet<ShortTermRadarSnapshot>(path, { signal: request.signal }));
}

export const meta: MetaFunction = () => [
  ...pageMeta({
    title: withSubject("短线雷达"),
    description: `${SITE.name}短线情绪雷达：题材主线梯队、跨平台人气共振榜与三大社区情绪温度。`,
    path: "/radar",
  }),
];

// ── 视图与筛选 ────────────────────────────────────────────────────────────────

const VIEWS = [
  { key: "ladders", label: "🧩 题材主线梯队" },
  { key: "resonance", label: "🔥 人气共振 Top 30" },
] as const;

type ViewKey = (typeof VIEWS)[number]["key"];

/** 身位徽章的配色：空间板最亮，20cm 次之，中军沉稳，首板与人气中性。 */
const ROLE_TONE: Record<string, "selected" | "hot" | "accent" | "ok" | "neutral"> = {
  空间板: "selected",
  "20cm弹性": "hot",
  容量中军: "accent",
  首板发酵: "ok",
  人气热股: "neutral",
};

const ROLE_HINT: Record<string, string> = {
  空间板: "连板高度最高的题材龙头",
  "20cm弹性": "创业板/科创板涨停或大涨，弹性最大",
  容量中军: "成交额居前，决定板块容量",
  首板发酵: "今日首板，题材可能启动",
  人气热股: "热榜在榜但暂无连板",
};

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/** A 股配色：涨红跌绿；情绪三色同源，看多红、分歧琥珀、看空绿。 */
function Change({ value }: { value: number }) {
  const tone = value > 0 ? "text-hot" : value < 0 ? "text-ok" : "text-ink-4";
  return <span className={`num font-semibold ${tone}`}>{value > 0 ? "+" : ""}{value.toFixed(2)}%</span>;
}

function SentimentBar({ sentiment, compact = false }: { sentiment: RadarStockItem["sentiment"]; compact?: boolean }) {
  const parts = [
    { key: "bull", label: "看多", ratio: sentiment.bullRatio, className: "bg-hot" },
    { key: "divergence", label: "分歧", ratio: sentiment.divergenceRatio, className: "bg-amber" },
    { key: "bear", label: "看空", ratio: sentiment.bearRatio, className: "bg-ok" },
  ];
  return (
    <div className="w-full" title={`${sentiment.label}｜有效帖 ${sentiment.validPosts} 条，水贴 ${sentiment.spamPosts} 条`}>
      <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-line-soft">
        {parts.map((part) => (
          <span key={part.key} className={part.className} style={{ width: pct(part.ratio) }} />
        ))}
      </div>
      {!compact && (
        <div className="mt-1 flex items-center justify-between text-[11px] text-ink-4">
          <span className="text-ink-3">{sentiment.label}</span>
          <span className="num">
            看多 {pct(sentiment.bullRatio)} · 分歧 {pct(sentiment.divergenceRatio)} · 看空 {pct(sentiment.bearRatio)}
          </span>
        </div>
      )}
    </div>
  );
}

function Nicknames({ stock }: { stock: RadarStockItem }) {
  if (!stock.nicknames.length) return null;
  return (
    <span className="flex flex-wrap gap-1">
      {stock.nicknames.map((nickname) => (
        <Badge key={nickname} tone="amber" title="社区黑话外号，可在搜索框直接输入">
          「{nickname}」
        </Badge>
      ))}
    </span>
  );
}

function RoleBadge({ role }: { role: string }) {
  return <Badge tone={ROLE_TONE[role] ?? "neutral"} title={ROLE_HINT[role]}>{role}</Badge>;
}

function quoteUrl(stock: RadarStockItem): string {
  return `https://quote.eastmoney.com/${stock.symbol.toLowerCase()}.html`;
}

// ── 个股卡片 ──────────────────────────────────────────────────────────────────

function StockRow({ stock, rank, onOpen }: { stock: RadarStockItem; rank?: number; onOpen: (code: string) => void }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(stock.code)}
      className="block w-full rounded-panel bg-bg-elevated p-3 text-left ring-1 ring-inset ring-line-soft transition-colors hover:bg-accent-softer"
    >
      <div className="flex flex-wrap items-center gap-2">
        {rank !== undefined && <span className="num w-6 text-[13px] font-semibold text-ink-4">{rank}</span>}
        <span className="font-semibold">{stock.name}</span>
        <span className="num text-[12px] text-ink-4">{stock.symbol}</span>
        <Nicknames stock={stock} />
        <RoleBadge role={stock.role} />
        {stock.boardCount > 0 && <Badge tone="neutral" title="连板高度">{stock.boardCount}连板</Badge>}
      </div>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-ink-3">
        <Change value={stock.changePct} />
        {stock.amountYi > 0 && <span className="num">成交额 {stock.amountYi.toFixed(1)} 亿</span>}
        {stock.turnoverRate > 0 && <span className="num">换手 {stock.turnoverRate.toFixed(2)}%</span>}
        <span className="num">共振 {stock.resonanceScore}</span>
        <span className="num">15m {stock.sentiment.posts15m} 帖</span>
        {stock.sentiment.spamPosts > 0 && <span className="text-ink-4">已滤除 {stock.sentiment.spamPosts} 条水贴</span>}
      </div>
      {stock.themes.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1 text-[11px] text-ink-4">
          {stock.themes.map((theme) => <span key={theme}>#{theme}</span>)}
        </div>
      )}
      <div className="mt-2"><SentimentBar sentiment={stock.sentiment} /></div>
      {stock.platformsHit.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {stock.platformsHit.map((hit) => <Badge key={hit} tone="accent">{hit}</Badge>)}
        </div>
      )}
    </button>
  );
}

// ── 视图一：题材主线梯队 ───────────────────────────────────────────────────────

function Ladder({ ladder, query, role, theme, onOpen }: { ladder: RadarThemeLadder; query: string; role: string | null; theme: string | null; onOpen: (code: string) => void }) {
  const stocks = useMemo(
    () => ladder.stocks.filter((stock) =>
      (!theme || stock.themes.some((name) => name.includes(theme))) && (!role || stock.role === role) && matchesQuery(stock, query)),
    [ladder.stocks, query, role, theme],
  );
  if (!stocks.length) return null;
  return (
    <section className="rounded-panel bg-bg-elevated p-4 ring-1 ring-inset ring-line-soft">
      <header className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h2 className="text-[15px] font-semibold">{ladder.theme}</h2>
        <span className="num text-[12px] text-ink-4">热度 {ladder.heatScore}</span>
        {ladder.topBoardCount > 0 && <Badge tone="selected">最高 {ladder.topBoardCount} 板</Badge>}
        <span className="num text-[12px] text-ink-4">{ladder.stockCount} 只</span>
      </header>
      <p className="mt-1 text-[12px] text-ink-3">{ladder.summary}</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {stocks.map((stock) => <StockRow key={stock.code} stock={stock} onOpen={onOpen} />)}
      </div>
    </section>
  );
}

// ── 抽屉：个股社区舆情与游资逻辑 ──────────────────────────────────────────────

function HighlightCard({ post }: { post: RadarHighlightPost }) {
  const tone = post.sentimentLabel === "extreme_bull_consistent" ? "hot" : post.sentimentLabel === "panic_bear_nuke" ? "ok" : "amber";
  const label = post.sentimentLabel === "extreme_bull_consistent" ? "看多" : post.sentimentLabel === "panic_bear_nuke" ? "看空" : post.sentimentLabel === "divergence_gaming" ? "分歧" : "中性";
  return (
    <article className="rounded-panel bg-bg-elevated p-3 ring-1 ring-inset ring-line-soft">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone="neutral">{PLATFORM_LABELS.find((item) => item.key === post.source)?.label ?? post.source}</Badge>
        {post.isVipYouzi && <Badge tone="hot" title="活跃实盘游资名录命中">🔥 游资/实盘复盘</Badge>}
        {post.isDeepLogic && <Badge tone="accent" title="深度作者或产业链长文">🧠 深度逻辑拆解</Badge>}
        <Badge tone={tone}>{label}</Badge>
        {post.matchedTerms.slice(0, 5).map((term) => <Badge key={term} tone="amber">#{term}</Badge>)}
      </div>
      <h3 className="mt-2 text-[13.5px] font-medium leading-snug">{post.title}</h3>
      {post.excerpt && post.excerpt !== post.title && <p className="mt-1 line-clamp-3 text-[12px] leading-relaxed text-ink-3">{post.excerpt}</p>}
      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-4">
        <span>{post.author || "匿名"}</span>
        {post.readCount > 0 && <span className="num">{post.readCount} 阅读</span>}
        <span className="num">{post.replyCount} 评论</span>
        {post.likeCount > 0 && <span className="num">{post.likeCount} 赞</span>}
        {post.url && (
          <a href={post.url} target="_blank" rel="noreferrer noopener" className="text-accent hover:underline">
            原帖 ↗
          </a>
        )}
      </div>
    </article>
  );
}

function StockDrawer({ stock, themes, onClose }: { stock: RadarStockItem | null; themes: RadarThemeLadder[]; onClose: () => void }) {
  const panel = useRef<HTMLDivElement>(null);
  const [platform, setPlatform] = useState("all");
  useModal({ open: !!stock, panel, onClose });
  const highlights = useMemo(
    () => (platform === "all" ? (stock?.highlights ?? []) : (stock?.highlights ?? []).filter((post) => post.source === platform)),
    [stock, platform],
  );

  return (
    <Presence show={!!stock} enter="animate-[fadeIn_.18s_ease-out]" exit="animate-[fadeOut_.15s_ease-in]" duration={150}>
      <div className="fixed inset-0 z-50 flex justify-end">
        <button type="button" aria-label="关闭抽屉" onClick={onClose} className="absolute inset-0 bg-black/40" />
        <div
          ref={panel}
          role="dialog"
          aria-modal="true"
          aria-label={stock ? `${stock.name} 社区舆情与游资逻辑` : "个股详情"}
          tabIndex={-1}
          className="relative flex h-full w-full max-w-[440px] flex-col overflow-y-auto bg-bg-elevated shadow-xl ring-1 ring-line-soft"
        >
          {!stock ? null : (
            <>
              <header className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-line-soft bg-bg-elevated px-4 py-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-[15px] font-semibold">{stock.name}</h2>
                    <span className="num text-[12px] text-ink-4">{stock.symbol}</span>
                    <Nicknames stock={stock} />
                    <RoleBadge role={stock.role} />
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-ink-3">
                    <Change value={stock.changePct} />
                    {stock.boardCount > 0 && <span className="num">{stock.boardCount}连板</span>}
                    {stock.amountYi > 0 && <span className="num">{stock.amountYi.toFixed(1)} 亿</span>}
                    {stock.turnoverRate > 0 && <span className="num">换手 {stock.turnoverRate.toFixed(2)}%</span>}
                    {stock.kplTag && <Badge tone="accent">{stock.kplTag}</Badge>}
                    {stock.limitReason && <span>{stock.limitReason}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <a href={quoteUrl(stock)} target="_blank" rel="noreferrer noopener" className="rounded-full px-2 py-1 text-[12px] text-accent hover:bg-accent-softer">
                    行情 ↗
                  </a>
                  <button type="button" onClick={onClose} aria-label="关闭" className="rounded-full p-1.5 text-ink-3 hover:bg-bg-sunk">
                    <IconClose size={18} />
                  </button>
                </div>
              </header>

              <div className="space-y-4 px-4 py-3">
                <section className="rounded-panel bg-bg-sunk p-3">
                  <h3 className="text-[12px] font-semibold text-ink-3">跨平台热度</h3>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[12px] text-ink-3">
                    <span className="num">同花顺热榜 {stock.thsRank ? `#${stock.thsRank}` : "未上榜"}</span>
                    <span className="num">东财热榜 {stock.dcRank ? `#${stock.dcRank}` : "未上榜"}</span>
                    <span className="num">共振总分 {stock.resonanceScore}</span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {stock.platformsHit.map((hit) => <Badge key={hit} tone="accent">{hit}</Badge>)}
                  </div>
                </section>

                <section className="rounded-panel bg-bg-sunk p-3">
                  <h3 className="text-[12px] font-semibold text-ink-3">社区情绪温度</h3>
                  <div className="mt-2"><SentimentBar sentiment={stock.sentiment} /></div>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-3">
                    <span className="num">有效帖 {stock.sentiment.validPosts}</span>
                    <span className="num">15 分钟 {stock.sentiment.posts15m} 帖</span>
                    <span className="num">水贴拦截 {stock.sentiment.spamPosts}</span>
                  </div>
                </section>

                {themes.length > 0 && (
                  <section>
                    <h3 className="text-[12px] font-semibold text-ink-3">所属题材梯队</h3>
                    <ul className="mt-1 space-y-1 text-[12px] text-ink-3">
                      {themes.map((ladder) => (
                        <li key={ladder.theme} className="flex items-center gap-2">
                          <span>{ladder.theme}</span>
                          <span className="num text-ink-4">{ladder.stockCount} 只 · 热度 {ladder.heatScore}</span>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                <section>
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="text-[12px] font-semibold text-ink-3">三大社区高价值帖</h3>
                    <div className="flex flex-wrap gap-1">
                      {PLATFORM_LABELS.map((item) => (
                        <button
                          key={item.key}
                          type="button"
                          onClick={() => setPlatform(item.key)}
                          aria-pressed={platform === item.key}
                          className={`rounded-full px-2 py-0.5 text-[11px] ${platform === item.key ? "bg-accent-soft text-accent" : "bg-bg-sunk text-ink-4"}`}
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="mt-2 space-y-2">
                    {highlights.length ? highlights.map((post, index) => <HighlightCard key={`${post.postId}-${index}`} post={post} />) : (
                      <p className="rounded-panel bg-bg-sunk p-3 text-[12px] text-ink-4">该社区暂无被挑出的高价值帖。</p>
                    )}
                  </div>
                </section>
              </div>
            </>
          )}
        </div>
      </div>
    </Presence>
  );
}

// ── 页面 ──────────────────────────────────────────────────────────────────────

export default function RadarRoute({ loaderData }: { loaderData: { snapshot?: ShortTermRadarSnapshot } & Record<string, unknown> }) {
  const snapshot = (loaderData?.snapshot ?? loaderData) as ShortTermRadarSnapshot;
  const [params, setParams] = useSearchParams();
  const view = (params.get("view") === "resonance" ? "resonance" : "ladders") as ViewKey;
  const role = params.get("role");
  const theme = params.get("theme");
  const openCode = params.get("stock");
  // The search lives in the URL so a filtered radar can be shared and survives a reload: typing keeps
  // `?q=` in step, and arriving with `?q=易中天` filters the first paint instead of only after a
  // keystroke.
  const query = params.get("q") ?? "";

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true, preventScrollReset: true });
  };

  // The drawer may be addressed by bare code or by the qualified one; both open the same stock.
  const stock = useMemo(() => {
    const wanted = (openCode ?? "").toUpperCase();
    const bare = wanted.replace(/\..*$/, "");
    const same = (item: RadarStockItem) => item.bareCode === bare || item.code.toUpperCase() === wanted;
    return snapshot.topResonanceStocks.find(same)
      ?? snapshot.themeLadders.flatMap((ladder) => ladder.stocks).find(same)
      ?? null;
  }, [snapshot, openCode]);
  const stockThemes = useMemo(
    () => (stock ? snapshot.themeLadders.filter((ladder) => ladder.stocks.some((item) => item.bareCode === stock.bareCode)) : []),
    [snapshot, stock],
  );

  const inTheme = (item: RadarStockItem) => !theme || item.themes.some((name) => name.includes(theme));
  const boards = snapshot.topResonanceStocks.filter((item) => inTheme(item) && (!role || item.role === role) && matchesQuery(item, query));
  const isEmpty = snapshot.themeLadders.length === 0 && snapshot.topResonanceStocks.length === 0;

  return (
    <div className="mx-auto max-w-[var(--page-max-board)] px-4 pb-16 pt-4 lg:px-6">
      <header className="mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-[19px] font-semibold">{withSubject("短线情绪雷达")}</h1>
          {snapshot.mode !== "empty" && <Badge tone="accent">{snapshot.mode === "live" ? "实时" : snapshot.mode}</Badge>}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink-4">
          <span>{snapshot.generatedAt ? `快照 ${snapshot.generatedAt.slice(0, 16).replace("T", " ")}` : "暂无快照"}</span>
          <span className="num">焦点股池 {snapshot.focusPoolSize} 只</span>
          {theme && (
            <span className="inline-flex items-center gap-1">
              题材
              <button type="button" onClick={() => setParam("theme", null)} className="text-accent hover:underline">#{theme} ✕</button>
            </span>
          )}
          {query && <span className="inline-flex items-center gap-1">搜索 <b className="text-ink-3">{query}</b></span>}
          {sourceBadges(snapshot).map((badge) => (
            <span key={badge.label} className="inline-flex items-center gap-1">
              {badge.label}
              <Badge tone={badge.status === "ok" || badge.status === "fixture" ? "ok" : badge.status === "empty" ? "amber" : "neutral"}>{badge.status}</Badge>
            </span>
          ))}
        </div>
      </header>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input
          value={query}
          onChange={(event) => setParam("q", event.target.value || null)}
          placeholder="搜代码 / 名称 / 黑话外号（易中天、寒王）"
          aria-label="搜索短线雷达"
          className="h-9 min-w-[220px] flex-1 rounded-full bg-bg-sunk px-3 text-[13px] outline-none ring-1 ring-inset ring-line-soft focus:ring-2 focus:ring-accent"
        />
        <div className="flex flex-wrap gap-1">
          <button
            type="button"
            onClick={() => setParam("role", null)}
            aria-pressed={!role}
            className={`h-9 rounded-full px-3 text-[12px] ${!role ? "bg-accent-soft text-accent" : "bg-bg-sunk text-ink-3"}`}
          >
            全部身位
          </button>
          {ROLE_ORDER.map((item) => (
            <button
              key={item}
              type="button"
              title={ROLE_HINT[item]}
              onClick={() => setParam("role", role === item ? null : item)}
              aria-pressed={role === item}
              className={`h-9 rounded-full px-3 text-[12px] ${role === item ? "bg-accent-soft text-accent" : "bg-bg-sunk text-ink-3"}`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4 flex gap-1 rounded-full bg-bg-sunk p-1">
        {VIEWS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setParam("view", item.key === "ladders" ? null : item.key)}
            aria-pressed={view === item.key}
            className={`flex-1 rounded-full px-3 py-1.5 text-[13px] transition-colors ${view === item.key ? "bg-bg-elevated font-semibold shadow-sm" : "text-ink-3"}`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {isEmpty ? (
        <EmptyState title="暂无短线雷达快照" action={
          <code className="rounded bg-bg-sunk px-2 py-1 text-[12px] text-ink-3">python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run</code>
        }>
          先在项目根目录运行上面的命令生成快照，本页会立刻显示题材梯队与人气共振榜。
        </EmptyState>
      ) : view === "ladders" ? (
        <div className="space-y-3">
          {snapshot.themeLadders.map((ladder) => (
            <Ladder key={ladder.theme} ladder={ladder} query={query} role={role} theme={theme} onOpen={(code) => setParam("stock", code)} />
          ))}
        </div>
      ) : (
        <ol className="space-y-2">
          {boards.map((item, index) => (
            <li key={item.code}>
              <StockRow stock={item} rank={index + 1} onOpen={(code) => setParam("stock", code)} />
            </li>
          ))}
          {boards.length === 0 && <li><EmptyState title="没有匹配的标的">换个关键词或身位再试。</EmptyState></li>}
        </ol>
      )}

      <StockDrawer stock={stock} themes={stockThemes} onClose={() => setParam("stock", null)} />

      <footer className="mt-10 text-[11px] text-ink-4">
        数据来自同花顺/东财热榜、盘中涨跌停与淘股吧、雪球、东财股吧社区聚合；本页不构成投资建议。
        <Link to="/agent" className="ml-1 text-accent hover:underline">{subjectAfter("Agent", "接入")}</Link>
      </footer>
    </div>
  );
}