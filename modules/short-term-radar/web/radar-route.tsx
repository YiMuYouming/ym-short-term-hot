// The radar page, V2 minimal (LITE-02) with LITE-04 density & honesty passes:
//
//   view 1 「热门板块」 — main-line themes by default (single-stock long-tail collapsed behind an
//                        expander, filterable); pick one and see its hot stocks in compact rows.
//   view 2 「热门股 Top 50」 — one fixed-layout table: rank, stock (keyboard-focusable button),
//                        change/board, themes (2 + N), why-hot, community heat.
//   any stock opens the same drawer: limitReason + six hard facts on top, collapsible whyHot below,
//                        the three communities' real posts under platform tabs with counts; ← / →
//                        (and ArrowLeft / ArrowRight) walk the current view's list.
//
// Missing values are shown as missing (LITE-04): 首板 instead of "1 连板", 封板时间待补 instead of
// "未封板/非涨停" next to a 4-board stock, 代表 instead of 领涨 for a falling leader, and a real
// three-colour sentiment bar whenever there are posts (grey only when there are none).
//
// The api's theme/role/q filters stay for agents and shareable links (contracts.ts unchanged here).
// Data comes from the api over HTTP only (`apiGet("/api/site/radar")`); this file never touches the
// database or the backend package (architecture red line A).
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
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
  leaderStock,
  sealedCount,
  sourceBadges,
  type RadarHighlightPost,
  type RadarStockItem,
  type RadarThemeLadder,
  type ShortTermRadarSnapshot,
} from "../contracts.ts";

export { pageHeaders as headers } from "@aihot/web/lib/api.server";

export async function loader({ request }: { request: Request }) {
  // Both views need the whole snapshot (the theme list and the full board), so the page filters
  // nothing itself: theme/role/q stay on the api for agents and shared links.
  return cachedPage(60, await apiGet<ShortTermRadarSnapshot>("/api/site/radar", { signal: request.signal }));
}

export const meta: MetaFunction = () => [
  ...pageMeta({
    title: withSubject("雷达"),
    description: `${SITE.name}短线雷达：热门板块与热门股 Top 50，点开即看为什么火与三社区真实评价。`,
    path: "/radar",
  }),
];

// ── 视角与公共小组件 ───────────────────────────────────────────────────────────

const VIEWS = [
  { key: "themes", label: "🔥 热门板块" },
  { key: "stocks", label: "📈 热门股 Top 50" },
] as const;

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

/** 单帖情绪四值（LITE-03 契约）→ 徽章配色与文案。 */
const SENTIMENT_TONE: Record<string, "hot" | "ok" | "amber" | "neutral"> = {
  bull: "hot",
  bear: "ok",
  divergence: "amber",
  neutral: "neutral",
};

const SENTIMENT_LABEL: Record<string, string> = {
  bull: "看多",
  bear: "看空",
  divergence: "分歧",
  neutral: "中性",
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
  // LITE-04：有有效帖就按真实三色比例渲染——不再因「情绪中性」把 1 多 1 空抹成全灰；
  // 0 帖才是全灰占位；样本 < 5 条弱化并标注小样本。
  const sampled = sentiment.validPosts > 0;
  const smallSample = sampled && sentiment.validPosts < 5;
  const parts = [
    { key: "bull", label: "看多", ratio: sentiment.bullRatio, className: "bg-hot" },
    { key: "divergence", label: "分歧", ratio: sentiment.divergenceRatio, className: "bg-amber" },
    { key: "bear", label: "看空", ratio: sentiment.bearRatio, className: "bg-ok" },
  ];
  return (
    <div
      className="w-full"
      title={sampled ? `${sentiment.label}｜有效帖 ${sentiment.validPosts} 条，水贴 ${sentiment.spamPosts} 条` : "暂无评论"}
    >
      <div className={`flex h-1.5 w-full overflow-hidden rounded-full bg-line-soft ${smallSample ? "opacity-65" : ""}`}>
        {sampled ? (
          parts.map((part) => <span key={part.key} className={part.className} style={{ width: pct(part.ratio) }} />)
        ) : (
          <span className="w-full bg-line-soft" />
        )}
      </div>
      {!compact && (
        <div className="mt-1 flex items-center justify-between text-[11px] text-ink-4">
          <span className="text-ink-3">
            {sampled ? sentiment.label : "暂无评论"}
            {smallSample && " (小样本)"}
          </span>
          <span className="num">
            {sampled
              ? `看多 ${pct(sentiment.bullRatio)} · 分歧 ${pct(sentiment.divergenceRatio)} · 看空 ${pct(sentiment.bearRatio)}`
              : "有效帖 0"}
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
        <Badge key={nickname} tone="amber" title="社区黑话外号">
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

/** 列表/表格里的为什么火摘要：limitReason 一句话优先，没有就退回 whyHot 首行。 */
function whyHotSummary(stock: RadarStockItem): string {
  if (stock.limitReason) return stock.limitReason;
  return stock.whyHot.split("\n")[0] ?? "";
}

/** 板块摘要自带「板块名：X 只热门股，涨停 Y 家，」前缀，副标题里去掉避免与标题和数字重复。 */
function ladderSummary(ladder: RadarThemeLadder): string {
  const prefix = `${ladder.theme}：`;
  const body = ladder.summary.startsWith(prefix) ? ladder.summary.slice(prefix.length) : ladder.summary;
  return body.replace(/^\d+\s*只热门股[，,]\s*涨停\s*\d+\s*家[，,；;\s]*/, "");
}

// ── LITE-04：缺失值与降级状态诚实化 ───────────────────────────────────────────

/**
 * 连板徽章：>=2 显示「N 连板」，1 显示「首板」（A 股术语，不再「1 连板」）；
 * 0 板但涨幅够涨停显示「涨停/待核连板」，盘中池降级且有归因显示「连板待补」，否则不显示。
 */
function boardBadge(
  stock: RadarStockItem,
  intradayDegraded: boolean,
): { text: string; tone: "hot" | "ok" | "neutral" } | null {
  if (stock.boardCount >= 2) return { text: `${stock.boardCount} 连板`, tone: "hot" };
  if (stock.boardCount === 1) return { text: "首板", tone: "ok" };
  if (stock.changePct >= 9.8) return { text: "涨停/待核连板", tone: "neutral" };
  if (intradayDegraded && stock.limitReason) return { text: "连板待补", tone: "neutral" };
  return null;
}

/** 抽屉硬指标卡的连板文案：与徽章同口径，无信号时明说「未连板」。 */
function boardFactText(stock: RadarStockItem, intradayDegraded: boolean): string {
  return boardBadge(stock, intradayDegraded)?.text ?? "未连板";
}

/**
 * 封板时间：有值直接显示；连板股缺值是「封板时间待补」——绝不能一边 4 连板一边写未封板；
 * 非连板但涨幅够涨停同样是待补；真正没涨停才写「未涨停」。
 */
function sealTimeText(stock: RadarStockItem): string {
  if (stock.sealTime) return stock.sealTime;
  if (stock.boardCount > 0) return "封板时间待补";
  if (stock.changePct >= 9.8) return "封板时间待补";
  return "未涨停";
}

/** 紧凑社区徽章：「15帖 · 偏多 60%」/「3帖 · 分歧」/「暂无评论」。 */
function communityBadgeText(sentiment: RadarStockItem["sentiment"]): string {
  if (sentiment.validPosts === 0) return "暂无评论";
  let direction = sentiment.label;
  if (sentiment.bullRatio >= 0.55) direction = `偏多 ${pct(sentiment.bullRatio)}`;
  else if (sentiment.bearRatio >= 0.55) direction = `偏空 ${pct(sentiment.bearRatio)}`;
  else if (sentiment.divergenceRatio >= 0.4) direction = `分歧 ${pct(sentiment.divergenceRatio)}`;
  return `${sentiment.validPosts}帖 · ${direction}`;
}

/** ISO 8601（北京时间）→ 「MM-DD HH:mm」；纯字符串切片，不碰本地时区。 */
function formatMoment(iso: string): string {
  const match = /^\d{4}-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso);
  return match ? `${match[1]}-${match[2]} ${match[3]}:${match[4]}` : iso.slice(0, 16).replace("T", " ");
}

/** 「20261016」→「2026-10-16」；形状不认识时原样返回。 */
function formatTradeDate(tradeDate: string): string {
  const digits = tradeDate.replace(/\D/g, "");
  return digits.length === 8
    ? `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`
    : tradeDate;
}

/** 盘中池是否降级（封板时间/连板数可能缺字段的那一个信源）。 */
function intradayDegradedOf(snapshot: ShortTermRadarSnapshot): boolean {
  const sources = (snapshot.dataQuality?.sources ?? {}) as Record<string, { status?: string }>;
  return sources.intraday?.status === "degraded";
}

// ── 视角一：热门板块 → 板块内热门股 ─────────────────────────────────────────────

function ThemeStockRow({
  stock,
  onOpen,
  intradayDegraded,
}: {
  stock: RadarStockItem;
  onOpen: (code: string) => void;
  intradayDegraded: boolean;
}) {
  const why = whyHotSummary(stock);
  const badge = boardBadge(stock, intradayDegraded);
  return (
    <button
      type="button"
      onClick={() => onOpen(stock.code)}
      className="block w-full rounded-panel bg-surface p-2.5 text-left ring-1 ring-inset ring-line-soft transition-colors hover:bg-accent-softer"
    >
      {/* 第一行：名称 + 代码 + 连板徽章 + 封板时间 ｜ 涨跌幅（大号）+ 成交额 */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="truncate font-semibold">{stock.name}</span>
          <span className="num shrink-0 text-[11px] text-ink-4">{stock.symbol}</span>
          {badge && <Badge tone={badge.tone}>{badge.text}</Badge>}
          {stock.sealTime && (
            <span className="num shrink-0 text-[11px] text-ink-4">{stock.sealTime} 封板</span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="num text-[15px]">
            <Change value={stock.changePct} />
          </span>
          {stock.amountYi > 0 && <span className="num text-[11px] text-ink-4">{stock.amountYi.toFixed(1)}亿</span>}
        </div>
      </div>
      {/* 第二行：一句话为什么火 ｜ 紧凑社区徽章 */}
      <div className="mt-1 flex items-center justify-between gap-2">
        <span className="truncate text-[12px] text-ink-3">{why || "—"}</span>
        <span
          className="num shrink-0 text-[11px] text-ink-4"
          title={`${stock.sentiment.label}｜有效帖 ${stock.sentiment.validPosts} 条`}
        >
          {communityBadgeText(stock.sentiment)}
        </span>
      </div>
    </button>
  );
}

function ThemePicker({
  ladders,
  selected,
  onSelect,
}: {
  ladders: RadarThemeLadder[];
  selected: RadarThemeLadder | null;
  onSelect: (theme: string) => void;
}) {
  const [filter, setFilter] = useState("");
  const [showTail, setShowTail] = useState(false);
  const needle = filter.trim().toLowerCase();

  // 主线默认展示：>=2 只热股或 >=2 家涨停；不足 12 个则补足前 15 个板块
  const { main, tail } = useMemo(() => {
    const core = ladders.filter((ladder) => ladder.stockCount >= 2 || (ladder.limitUpCount ?? 0) >= 2);
    const mainSet = core.length >= 12 ? core : ladders.slice(0, 15);
    const mainNames = new Set(mainSet.map((ladder) => ladder.theme));
    return { main: mainSet, tail: ladders.filter((ladder) => !mainNames.has(ladder.theme)) };
  }, [ladders]);

  // URL 选中的板块落在折叠区时自动展开，避免「选了却看不到」
  useEffect(() => {
    if (selected && tail.some((ladder) => ladder.theme === selected.theme)) setShowTail(true);
  }, [selected, tail]);

  const visible = needle
    ? ladders.filter(
        (ladder) =>
          ladder.theme.toLowerCase().includes(needle) ||
          ladder.stocks.some(
            (stock) =>
              stock.name.toLowerCase().includes(needle) ||
              stock.symbol.toLowerCase().includes(needle) ||
              stock.bareCode.includes(needle),
          ),
      )
    : showTail
      ? [...main, ...tail]
      : main;

  return (
    <aside className="rounded-panel bg-surface ring-1 ring-inset ring-line-soft lg:sticky lg:top-4 lg:self-start">
      <div className="border-b border-line-soft px-3 py-2 text-[12px] font-semibold text-ink-3">
        热门板块（按热度排序）
      </div>
      <div className="border-b border-line-soft px-3 py-2">
        <input
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="筛选板块或成分股..."
          aria-label="筛选板块或成分股"
          className="w-full rounded bg-bg-sunk px-2 py-1 text-[12px] outline-none ring-1 ring-inset ring-line-soft focus:ring-2 focus:ring-accent"
        />
      </div>
      <ul className="max-h-[300px] overflow-y-auto p-1 lg:max-h-[calc(100vh-16rem)]">
        {visible.map((ladder) => {
          const active = selected?.theme === ladder.theme;
          const leader = leaderStock(ladder);
          return (
            <li key={ladder.theme}>
              <button
                type="button"
                onClick={() => onSelect(ladder.theme)}
                aria-pressed={active}
                className={`w-full rounded px-2 py-1.5 text-left transition-colors ${active ? "bg-accent-soft text-accent" : "hover:bg-bg-sunk"}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-[13px] font-medium">{ladder.theme}</span>
                  {ladder.topBoardCount > 0 && (
                    <Badge tone="selected" title="板块最高连板">{ladder.topBoardCount}板</Badge>
                  )}
                </div>
                <div className="num text-[11px] text-ink-4">
                  {ladder.stockCount} 只 · 涨停 {sealedCount(ladder)} 家
                </div>
                {leader && (
                  <div className="truncate text-[11px] text-ink-4">
                    {leader.changePct > 0 ? "领涨 " : "代表 "}
                    {leader.name} <Change value={leader.changePct} />
                  </div>
                )}
              </button>
            </li>
          );
        })}
        {visible.length === 0 && (
          <li className="px-2 py-3 text-[12px] text-ink-4">没有匹配的板块或成分股。</li>
        )}
        {!needle && tail.length > 0 && (
          <li>
            <button
              type="button"
              onClick={() => setShowTail((value) => !value)}
              className="w-full rounded px-2 py-1.5 text-left text-[12px] text-accent hover:bg-bg-sunk"
            >
              {showTail ? "收起单股概念 ▴" : `展开其余 ${tail.length} 个单股异动概念 ▾`}
            </button>
          </li>
        )}
      </ul>
    </aside>
  );
}

// ── 视角二：热门股 Top 50 干净表格 ─────────────────────────────────────────────

/** 有帖但样本不足 5 条——表格里与情绪条一起标注，避免一条帖看成强共识。 */
function sampledSmall(sentiment: RadarStockItem["sentiment"]): boolean {
  return sentiment.validPosts > 0 && sentiment.validPosts < 5;
}

function StockTable({
  stocks,
  onOpen,
  onTheme,
  intradayDegraded,
}: {
  stocks: RadarStockItem[];
  onOpen: (code: string) => void;
  onTheme: (theme: string) => void;
  intradayDegraded: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-panel bg-surface ring-1 ring-inset ring-line-soft">
      <table className="w-full min-w-[960px] table-fixed border-collapse text-left text-[13px]">
        <colgroup>
          <col className="w-16" />
          <col className="w-44" />
          <col className="w-32" />
          <col className="w-44" />
          <col />
          <col className="w-36" />
        </colgroup>
        <thead className="bg-bg-sunk text-[12px] text-ink-4">
          <tr>
            <th className="px-3 py-2 font-medium">排名</th>
            <th className="px-3 py-2 font-medium">股票</th>
            <th className="px-3 py-2 font-medium">涨跌幅 · 连板</th>
            <th className="px-3 py-2 font-medium">所属板块</th>
            <th className="px-3 py-2 font-medium">为什么火</th>
            <th className="px-3 py-2 font-medium">社区热度</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, index) => {
            const badge = boardBadge(stock, intradayDegraded);
            return (
              <tr
                key={stock.code}
                onClick={() => onOpen(stock.code)}
                className="cursor-pointer border-t border-line-soft transition-colors hover:bg-accent-softer"
              >
                <td className="px-3 py-2 align-top">
                  <span className="num text-[13px] font-semibold">{index + 1}</span>
                  <div className="mt-0.5 flex flex-col gap-0.5">
                    {stock.thsRank && (
                      <span className="num text-[10px] text-ink-4" title="同花顺热榜名次">{`ths #${stock.thsRank}`}</span>
                    )}
                    {stock.dcRank && (
                      <span className="num text-[10px] text-ink-4" title="东财人气榜名次">{`dc #${stock.dcRank}`}</span>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2 align-top">
                  {/* 股票名是原生 button：可 Tab 聚焦、回车打开抽屉 */}
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpen(stock.code);
                    }}
                    className="block max-w-full text-left"
                  >
                    <span className="block truncate font-semibold">{stock.name}</span>
                    <span className="num block text-[11px] text-ink-4">{stock.symbol}</span>
                  </button>
                  <div className="mt-0.5">
                    <Nicknames stock={stock} />
                  </div>
                </td>
                <td className="px-3 py-2 align-top">
                  <Change value={stock.changePct} />
                  <div className="mt-0.5">{badge && <Badge tone={badge.tone}>{badge.text}</Badge>}</div>
                </td>
                <td className="px-3 py-2 align-top">
                  {stock.themes.length > 0 ? (
                    <div className="flex flex-wrap items-center gap-1">
                      {stock.themes.slice(0, 2).map((theme) => (
                        <button
                          key={theme}
                          type="button"
                          title={`跳到「${theme}」板块`}
                          onClick={(event) => {
                            event.stopPropagation();
                            onTheme(theme);
                          }}
                          className="rounded-full bg-bg-sunk px-2 py-0.5 text-[11px] text-ink-3 transition-colors hover:bg-accent-soft hover:text-accent"
                        >
                          #{theme}
                        </button>
                      ))}
                      {stock.themes.length > 2 && (
                        <span className="text-[11px] text-ink-4" title={stock.themes.join("、")}>
                          +{stock.themes.length - 2}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-ink-4">—</span>
                  )}
                </td>
                <td className="px-3 py-2 align-top">
                  <span className="line-clamp-2 text-ink-3" title={stock.whyHot || undefined}>
                    {whyHotSummary(stock) || "—"}
                  </span>
                </td>
                <td className="px-3 py-2 align-top">
                  <div className="num text-[12px]">
                    有效帖 {stock.sentiment.validPosts}
                    {sampledSmall(stock.sentiment) ? " · 小样本" : ""}
                  </div>
                  <div className="mt-1">
                    <SentimentBar sentiment={stock.sentiment} compact />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── 共用抽屉：为什么火（置顶）+ 硬指标 + 各平台真实评价 ─────────────────────────

function HighlightCard({ post }: { post: RadarHighlightPost }) {
  const tone = SENTIMENT_TONE[post.sentimentLabel] ?? "neutral";
  const label = SENTIMENT_LABEL[post.sentimentLabel] ?? "未判定";
  return (
    <article className="rounded-panel bg-surface p-3 ring-1 ring-inset ring-line-soft">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone="neutral">{PLATFORM_LABELS.find((item) => item.key === post.source)?.label ?? post.source}</Badge>
        {post.isVipYouzi && <Badge tone="hot" title="活跃实盘游资名录命中">🔥 游资/实盘复盘</Badge>}
        {post.isDeepLogic && <Badge tone="accent" title="深度作者或产业链长文">🧠 深度逻辑拆解</Badge>}
        <Badge tone={tone} title="单帖情绪（规则词典判定）">{label}</Badge>
        {post.matchedTerms.slice(0, 5).map((term) => (
          <Badge key={term} tone="amber">#{term}</Badge>
        ))}
      </div>
      <h3 className="mt-2 text-[13.5px] font-medium leading-snug">{post.title}</h3>
      {post.excerpt && post.excerpt !== post.title && (
        <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-ink-3">{post.excerpt}</p>
      )}
      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-4">
        <span>{post.author || "匿名"}</span>
        {post.publishedAt && <span className="num">{formatMoment(post.publishedAt)}</span>}
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

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded bg-surface px-2 py-1.5 ring-1 ring-inset ring-line-soft">
      <dt className="text-[11px] text-ink-4">{label}</dt>
      <dd className="mt-0.5 text-[13px] font-medium text-ink">{children}</dd>
    </div>
  );
}

function StockDrawer({
  stock,
  stocks,
  themes,
  onClose,
  onSelect,
  onTheme,
  intradayDegraded,
}: {
  stock: RadarStockItem | null;
  stocks: RadarStockItem[];
  themes: RadarThemeLadder[];
  onClose: () => void;
  onSelect: (code: string) => void;
  onTheme: (theme: string) => void;
  intradayDegraded: boolean;
}) {
  const panel = useRef<HTMLDivElement>(null);
  const [platform, setPlatform] = useState("all");
  const [whyExpanded, setWhyExpanded] = useState(false);

  // 上一只 / 下一只沿当前视角的股票列表
  const index = stock ? stocks.findIndex((item) => item.code === stock.code) : -1;
  const prev = index > 0 ? stocks[index - 1]! : null;
  const next = index >= 0 && index < stocks.length - 1 ? stocks[index + 1]! : null;

  // 切换股票：平台筛选回「全部」、收起长文本、滚回顾区顶部（LITE-04）
  useEffect(() => {
    setPlatform("all");
    setWhyExpanded(false);
    if (panel.current) panel.current.scrollTop = 0;
  }, [stock?.code]);

  useModal({
    open: !!stock,
    panel,
    onClose,
    onKeyDown: (event) => {
      if (event.key === "ArrowLeft" && prev) onSelect(prev.code);
      if (event.key === "ArrowRight" && next) onSelect(next.code);
    },
  });

  const platformCounts = useMemo(() => {
    const counts: Record<string, number> = { all: stock?.highlights.length ?? 0 };
    for (const post of stock?.highlights ?? []) counts[post.source] = (counts[post.source] ?? 0) + 1;
    return counts;
  }, [stock]);

  const highlights = useMemo(
    () =>
      platform === "all"
        ? (stock?.highlights ?? [])
        : (stock?.highlights ?? []).filter((post) => post.source === platform),
    [stock, platform],
  );

  // whyHot 超过 110 字或含换行时默认折叠前三行，首屏直达社区评价
  const whyLong = !!stock && (stock.whyHot.length > 110 || stock.whyHot.includes("\n"));

  return (
    <Presence show={!!stock} enter="anim-fade-in" exit="anim-fade-out" duration={160}>
      <div className="fixed inset-0 z-50 flex justify-end">
        <button type="button" aria-label="关闭抽屉" onClick={onClose} className="absolute inset-0 bg-black/40" />
        <div
          ref={panel}
          role="dialog"
          aria-modal="true"
          aria-label={stock ? `${stock.name} 个股详情` : "个股详情"}
          tabIndex={-1}
          className="relative flex h-full w-full max-w-[min(100vw,560px)] flex-col overflow-y-auto bg-surface shadow-xl ring-1 ring-line-soft"
        >
          {!stock ? null : (
            <>
              <header className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-line-soft bg-surface px-4 py-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-[16px] font-semibold">{stock.name}</h2>
                    <span className="num text-[12px] text-ink-4">{stock.symbol}</span>
                    <Nicknames stock={stock} />
                    <RoleBadge role={stock.role} />
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-ink-3">
                    <Change value={stock.changePct} />
                    <span className="num">{boardFactText(stock, intradayDegraded)}</span>
                    {stock.amountYi > 0 && <span className="num">成交额 {stock.amountYi.toFixed(1)} 亿</span>}
                  </div>
                  <div className="mt-1.5 flex items-center gap-1">
                    <button
                      type="button"
                      disabled={!prev}
                      onClick={() => prev && onSelect(prev.code)}
                      className="rounded-full bg-bg-sunk px-2 py-0.5 text-[11px] text-ink-3 enabled:hover:bg-accent-soft enabled:hover:text-accent disabled:opacity-40"
                    >
                      ← 上一只
                    </button>
                    <button
                      type="button"
                      disabled={!next}
                      onClick={() => next && onSelect(next.code)}
                      className="rounded-full bg-bg-sunk px-2 py-0.5 text-[11px] text-ink-3 enabled:hover:bg-accent-soft enabled:hover:text-accent disabled:opacity-40"
                    >
                      下一只 →
                    </button>
                    {index >= 0 && <span className="num text-[11px] text-ink-4">{index + 1}/{stocks.length}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <a
                    href={quoteUrl(stock)}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="rounded-full px-2 py-1 text-[12px] text-accent hover:bg-accent-softer"
                  >
                    行情 ↗
                  </a>
                  <button
                    type="button"
                    onClick={onClose}
                    aria-label="关闭"
                    className="rounded-full p-1.5 text-ink-3 hover:bg-bg-sunk"
                  >
                    <IconClose size={18} />
                  </button>
                </div>
              </header>

              <div className="space-y-4 px-4 py-3">
                {/* 第一块：一句话为什么火（置顶醒目） */}
                <section className="rounded-panel bg-accent-softer p-3">
                  <h3 className="text-[12px] font-semibold text-ink-3">为什么火</h3>
                  {stock.limitReason ? (
                    <p className="mt-1 text-[14px] font-semibold leading-relaxed text-ink">{stock.limitReason}</p>
                  ) : stock.whyHot ? (
                    <p className="mt-1 text-[14px] font-semibold leading-relaxed text-ink">
                      {stock.whyHot.split("\n")[0]}
                    </p>
                  ) : (
                    <p className="mt-1 text-[12px] leading-relaxed text-ink-4">
                      该股今日无详细上榜原因（仅榜单在榜），各平台真实评价见下方。
                    </p>
                  )}
                </section>

                {/* 六格硬指标：连板状态 / 封板时间 / 成交额 / 换手率 / 双榜名次 */}
                <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  <Fact label="连板">{boardFactText(stock, intradayDegraded)}</Fact>
                  <Fact label="封板时间">{sealTimeText(stock)}</Fact>
                  <Fact label="成交额">{stock.amountYi > 0 ? `${stock.amountYi.toFixed(1)} 亿` : "—"}</Fact>
                  <Fact label="换手率">{stock.turnoverRate > 0 ? `${stock.turnoverRate.toFixed(2)}%` : "—"}</Fact>
                  <Fact label="同花顺热榜">{stock.thsRank ? `#${stock.thsRank}` : "未上榜"}</Fact>
                  <Fact label="东财人气榜">{stock.dcRank ? `#${stock.dcRank}` : "未上榜"}</Fact>
                </dl>

                {/* whyHot 详细逻辑：长文本默认折叠，不把社区评价挤出首屏 */}
                {stock.whyHot && (
                  <section>
                    <p
                      className={`whitespace-pre-line text-[13px] leading-relaxed text-ink-3 ${
                        whyLong && !whyExpanded ? "line-clamp-3" : ""
                      }`}
                    >
                      {stock.whyHot}
                    </p>
                    {whyLong && (
                      <button
                        type="button"
                        onClick={() => setWhyExpanded((value) => !value)}
                        className="mt-1 text-[12px] text-accent hover:underline"
                      >
                        {whyExpanded ? "收起 ▴" : "展开完整逻辑 ▾"}
                      </button>
                    )}
                  </section>
                )}

                {themes.length > 0 && (
                  <section>
                    <h3 className="text-[12px] font-semibold text-ink-3">所属板块（点击回板块视角）</h3>
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {themes.map((ladder) => (
                        <button
                          key={ladder.theme}
                          type="button"
                          onClick={() => onTheme(ladder.theme)}
                          className="rounded-full bg-bg-sunk px-2 py-0.5 text-[11px] text-ink-3 transition-colors hover:bg-accent-soft hover:text-accent"
                        >
                          #{ladder.theme}
                        </button>
                      ))}
                    </div>
                  </section>
                )}

                <section className="rounded-panel bg-bg-sunk p-3">
                  <h3 className="text-[12px] font-semibold text-ink-3">社区情绪温度</h3>
                  <div className="mt-2">
                    <SentimentBar sentiment={stock.sentiment} />
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-3">
                    <span className="num">有效帖 {stock.sentiment.validPosts}</span>
                    <span className="num">15 分钟 {stock.sentiment.posts15m} 帖</span>
                    <span className="num">水贴拦截 {stock.sentiment.spamPosts}</span>
                  </div>
                </section>

                {/* 第二块：各平台真实评价（水贴已滤，Tab 带计数） */}
                <section>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-[12px] font-semibold text-ink-3">各平台真实评价</h3>
                    <div className="flex flex-wrap gap-1">
                      {PLATFORM_LABELS.map((item) => {
                        const count = platformCounts[item.key] ?? 0;
                        return (
                          <button
                            key={item.key}
                            type="button"
                            onClick={() => setPlatform(item.key)}
                            aria-pressed={platform === item.key}
                            className={`rounded-full px-2 py-0.5 text-[11px] ${
                              platform === item.key ? "bg-accent-soft text-accent" : "bg-bg-sunk text-ink-4"
                            } ${count === 0 ? "opacity-50" : ""}`}
                          >
                            {item.label} ({count})
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  <div className="mt-2 space-y-2">
                    {highlights.length ? (
                      highlights.map((post, postIndex) => (
                        <HighlightCard key={`${post.postId}-${postIndex}`} post={post} />
                      ))
                    ) : (
                      <p className="rounded-panel bg-bg-sunk p-3 text-[12px] text-ink-4">该平台暂无被挑出的高价值帖。</p>
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

// ── 页面 ───────────────────────────────────────────────────────────────────────

export default function RadarRoute({
  loaderData,
}: {
  loaderData: { snapshot?: ShortTermRadarSnapshot } & Record<string, unknown>;
}) {
  const snapshot = (loaderData?.snapshot ?? loaderData) as ShortTermRadarSnapshot;
  const [params, setParams] = useSearchParams();
  // 视图状态放 URL，可分享可刷新：/radar?view=stocks、/radar?theme=低空经济/eVTOL、/radar?stock=300308。
  const stocksView = params.get("view") === "stocks" || params.get("view") === "resonance"; // resonance 是旧版参数名
  const ladders = snapshot.themeLadders;

  // 一处交互常要同时改几个参数（点板块标签回板块视角 = view+theme+stock），所以一次成对地改。
  const updateParams = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(updates)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    setParams(next, { replace: true, preventScrollReset: true });
  };

  // 默认选中热度第一的板块；?theme= 命中则选中它，未命中退回第一个。
  const themeParam = params.get("theme") ?? "";
  const selectedTheme = useMemo(
    () => ladders.find((ladder) => ladder.theme === themeParam.trim()) ?? ladders[0] ?? null,
    [ladders, themeParam],
  );

  // The drawer may be addressed by bare code or by the qualified one; both open the same stock.
  const openCode = params.get("stock") ?? "";
  const stock = useMemo(() => {
    const wanted = openCode.toUpperCase();
    if (!wanted) return null;
    const bare = wanted.replace(/\..*$/, "");
    const same = (item: RadarStockItem) => item.bareCode === bare || item.code.toUpperCase() === wanted;
    return (
      snapshot.topResonanceStocks.find(same) ??
      snapshot.themeLadders.flatMap((ladder) => ladder.stocks).find(same) ??
      null
    );
  }, [snapshot, openCode]);
  const stockThemes = useMemo(
    () =>
      stock
        ? snapshot.themeLadders.filter((ladder) => ladder.stocks.some((item) => item.bareCode === stock.bareCode))
        : [],
    [snapshot, stock],
  );

  const isEmpty = ladders.length === 0 && snapshot.topResonanceStocks.length === 0;
  // LITE-04：页头分清「看的是哪一天」；盘中池降级决定连板/封板文案的口径。
  const tradeDate =
    typeof snapshot.dataQuality?.tradeDate === "string" ? (snapshot.dataQuality.tradeDate as string) : null;
  const intradayDegraded = intradayDegradedOf(snapshot);
  // 抽屉上一只/下一只沿当前视角的列表
  const drawerStocks = stocksView ? snapshot.topResonanceStocks : (selectedTheme?.stocks ?? []);

  return (
    <div className="mx-auto max-w-[var(--page-max-wide)] px-4 pb-16 pt-4 lg:px-6">
      <header className="mb-3">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-[19px] font-semibold">{withSubject("雷达")}</h1>
          {snapshot.mode !== "empty" && (
            <Badge tone="accent">
              {snapshot.mode === "live" ? "真实采集" : snapshot.mode === "offline_fixtures" ? "离线样本" : snapshot.mode}
            </Badge>
          )}
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink-4">
          <span className="num">
            {tradeDate ? `交易日 ${formatTradeDate(tradeDate)}` : "交易日未知"}
            {snapshot.generatedAt ? ` · ${formatMoment(snapshot.generatedAt)} 更新` : ""}
          </span>
          <span className="num">焦点股池 {snapshot.focusPoolSize} 只</span>
          {sourceBadges(snapshot).map((badge) => (
            <span key={badge.label} className="inline-flex items-center gap-1">
              {badge.label}
              <Badge
                tone={
                  badge.status === "ok" || badge.status === "success" || badge.status === "fixture"
                    ? "ok"
                    : badge.status === "empty" || badge.status === "degraded"
                      ? "amber"
                      : "neutral"
                }
              >
                {badge.status === "ok" || badge.status === "success"
                  ? "正常"
                  : badge.status === "fixture"
                    ? "样本"
                    : badge.status === "degraded"
                      ? "降级"
                      : badge.status === "empty"
                        ? "空"
                        : badge.status}
              </Badge>
            </span>
          ))}
        </div>
      </header>

      {/* 视角切换：只有两个 */}
      <div className="mb-4 flex gap-1 rounded-full bg-bg-sunk p-1">
        {VIEWS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => updateParams({ view: item.key === "themes" ? null : item.key, stock: null })}
            aria-pressed={stocksView === (item.key === "stocks")}
            className={`flex-1 rounded-full px-3 py-1.5 text-[13px] transition-colors ${
              stocksView === (item.key === "stocks") ? "bg-surface font-semibold shadow-sm" : "text-ink-3"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {isEmpty ? (
        <EmptyState
          title="暂无短线雷达快照"
          action={
            <code className="rounded bg-bg-sunk px-2 py-1 text-[12px] text-ink-3">
              python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run
            </code>
          }
        >
          先在项目根目录运行上面的命令生成快照，本页会立刻显示热门板块与热门股 Top 50。
        </EmptyState>
      ) : stocksView ? (
        <section>
          <p className="mb-2 text-[12px] text-ink-4">
            共 {snapshot.topResonanceStocks.length} 只，按跨平台共振分排序；点任意一行看「为什么火 +
            各平台真实评价」，点板块标签回板块视角。
          </p>
          <StockTable
            stocks={snapshot.topResonanceStocks}
            onOpen={(code) => updateParams({ stock: code })}
            onTheme={(theme) => updateParams({ view: null, theme, stock: null })}
            intradayDegraded={intradayDegraded}
          />
        </section>
      ) : (
        <div className="grid items-start gap-3 lg:grid-cols-[minmax(210px,250px)_1fr]">
          <ThemePicker
            ladders={ladders}
            selected={selectedTheme}
            onSelect={(theme) => updateParams({ theme, stock: null })}
          />
          <section className="rounded-panel bg-surface p-3 ring-1 ring-inset ring-line-soft">
            {selectedTheme ? (
              <>
                <header className="mb-2">
                  <h2 className="text-[15px] font-semibold">{selectedTheme.theme}</h2>
                  <p className="mt-0.5 text-[12px] text-ink-4">
                    {selectedTheme.stockCount} 只热门股 · 涨停 {sealedCount(selectedTheme)} 家 ·{" "}
                    {ladderSummary(selectedTheme)}
                  </p>
                </header>
                <ul className="space-y-2">
                  {selectedTheme.stocks.map((item) => (
                    <li key={item.code}>
                      <ThemeStockRow
                        stock={item}
                        onOpen={(code) => updateParams({ stock: code })}
                        intradayDegraded={intradayDegraded}
                      />
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <EmptyState title="暂无板块数据">快照里没有题材梯队，先跑一次桥接。</EmptyState>
            )}
          </section>
        </div>
      )}

      <StockDrawer
        stock={stock}
        stocks={drawerStocks}
        themes={stockThemes}
        onClose={() => updateParams({ stock: null })}
        onSelect={(code) => updateParams({ stock: code })}
        onTheme={(theme) => updateParams({ view: null, theme, stock: null })}
        intradayDegraded={intradayDegraded}
      />

      <footer className="mt-10 text-[11px] text-ink-4">
        数据来自同花顺/东财热榜、盘中涨跌停与淘股吧、雪球、东财股吧社区聚合；本页不构成投资建议。
        <Link to="/agent" className="ml-1 text-accent hover:underline">
          {subjectAfter("Agent", "接入")}
        </Link>
      </footer>
    </div>
  );
}
