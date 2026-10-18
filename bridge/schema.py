"""桥接各层之间传递的数据结构。

全部是不可变 dataclass，`to_dict()` 直接产出快照 JSON / ingest payload，
因此不做手工序列化，也不引入 pydantic 之类的重依赖。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── 焦点股池 ──────────────────────────────────────────────────────────────────

# 梯队身位标签：与 industry/topics.json 的题材方向分开，这里回答「这只票在短线梯队里的位置」
ROLE_SPACE = "空间板"          # 连板数最高（≥3 板）
ROLE_ELASTIC_20CM = "20cm弹性"  # 30/68 开头且涨停或涨幅 ≥10%
ROLE_MID_CAP = "容量中军"       # 成交额 ≥50 亿，或题材词典归为容量中军
ROLE_FIRST_BOARD = "首板发酵"    # 首板涨停
ROLE_POPULAR = "人气热股"       # 其余热榜股


@dataclass(frozen=True)
class FocusStock:
    """焦点股池的一只票：题材归属 + 身位 + 三端热度位次。"""

    code: str
    name: str
    exchange: str                      # sh / sz / bj
    themes: tuple[str, ...] = ()
    nicknames: tuple[str, ...] = ()    # 社区黑话别名（易中天、寒王、宁王…）
    role_label: str = ROLE_POPULAR
    board_count: int = 0               # 连板数，0 = 非连板
    change_pct: float | None = None
    amount_yi: float | None = None      # 成交额（亿元）
    hot_rank_ths: int | None = None    # 同花顺热榜名次
    hot_rank_dc: int | None = None     # 东财热榜名次
    hot_rank_xq: int | None = None     # 雪球热股榜名次
    taoguba_mentions: int = 0
    sources: tuple[str, ...] = ()      # ths / dc / intraday / legacy / theme_base
    resonance_score: float = 0.0
    platforms_hit: tuple[str, ...] = ()
    limit_reason: str = ""             # 一句话涨停/热门原因标签（如「卫星通信芯片+低空经济」）
    why_hot: str = ""                  # 详细原因正文（优先同花顺 rank_reason，其次涨停原因+连板描述）
    seal_time: str = ""                # 封板时间（涨停池如实记录，未封/非涨停为空）

    @property
    def symbol(self) -> str:
        """雪球/淘股吧用的带市场前缀代码。"""
        return f"{self.exchange.upper()}{self.code}"

    @property
    def board_kind(self) -> str:
        """东财股吧接口用的纯 6 位代码。"""
        return self.code

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "themes": list(self.themes),
            "nicknames": list(self.nicknames),
            "roleLabel": self.role_label,
            "boardCount": self.board_count,
            "changePct": self.change_pct,
            "amountYi": self.amount_yi,
            "hotRankThs": self.hot_rank_ths,
            "hotRankDc": self.hot_rank_dc,
            "hotRankXq": self.hot_rank_xq,
            "taogubaMentions": self.taoguba_mentions,
            "sources": list(self.sources),
            "resonanceScore": round(self.resonance_score, 1),
            "platformsHit": list(self.platforms_hit),
            "limitReason": self.limit_reason,
            "whyHot": self.why_hot,
            "sealTime": self.seal_time,
        }


# ── 社区帖子 ──────────────────────────────────────────────────────────────────

PLATFORM_GUBA = "eastmoney_guba"
PLATFORM_TGB = "taoguba"
PLATFORM_XQ = "xueqiu"

# 三类情绪（与 sentiment_dict.json 的三组词条同名）
SENTIMENT_BULL = "extreme_bull_consistent"
SENTIMENT_DIVERGENCE = "divergence_gaming"
SENTIMENT_BEAR = "panic_bear_nuke"


@dataclass
class CommunityPost:
    """一条社区帖子。采集器只负责填事实字段，sentiment_engine 再补情绪与水贴判定。"""

    platform: str
    post_id: str
    url: str
    title: str
    code: str | None = None
    stock_name: str | None = None
    content: str | None = None
    author_id: str | None = None
    author_name: str | None = None
    published_at: str | None = None      # ISO 8601（北京时间）
    comment_count: int = 0
    view_count: int = 0
    like_count: int = 0
    # 采集器命中的名录/规则标记
    is_vip_youzi: bool = False           # 淘股吧活跃实盘游资
    youzi_style: tuple[str, ...] = ()
    is_deep_logic: bool = False          # 雪球深度作者或长文产业链拆解
    # sentiment_engine 回填
    is_spam: bool = False
    spam_rule: str | None = None
    sentiment: str | None = None
    sentiment_score: int = 0
    sentiment_terms: tuple[str, ...] = ()
    sentiment_context_notes: tuple[str, ...] = ()
    hot_weight: float = 0.0

    @property
    def text(self) -> str:
        """参与情绪打分的全文：标题 + 正文，社区语境里标题往往就是全部信息。"""
        return "\n".join(part for part in (self.title, self.content) if part)

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "postId": self.post_id,
            "url": self.url,
            "title": self.title,
            "code": self.code,
            "stockName": self.stock_name,
            "content": self.content,
            "authorId": self.author_id,
            "authorName": self.author_name,
            "publishedAt": self.published_at,
            "commentCount": self.comment_count,
            "viewCount": self.view_count,
            "likeCount": self.like_count,
            "isVipYouzi": self.is_vip_youzi,
            "youziStyle": list(self.youzi_style),
            "isDeepLogic": self.is_deep_logic,
            "isSpam": self.is_spam,
            "spamRule": self.spam_rule,
            "sentiment": self.sentiment,
            "sentimentScore": self.sentiment_score,
            "sentimentTerms": list(self.sentiment_terms),
            "sentimentContextNotes": list(self.sentiment_context_notes),
            "hotWeight": round(self.hot_weight, 2),
        }


# ── 情绪汇总 ──────────────────────────────────────────────────────────────────

# 情绪标签：读者看到的三态（与 CATEGORY_TAGS 的「一致亢奋」「多空分歧」「核按钮预警」同源）
LABEL_EUPHORIA = "一致亢奋"
LABEL_DIVERGENCE = "分歧博弈"
LABEL_NUKE = "恐慌核按钮"
LABEL_CALM = "情绪中性"


@dataclass(frozen=True)
class SentimentSummary:
    """一只焦点股的社区情绪温度条（占比之和恒为 100）。"""

    code: str
    total_posts: int
    valid_posts: int
    spam_posts: int
    bull_count: int
    divergence_count: int
    bear_count: int
    bull_ratio: float
    divergence_ratio: float
    bear_ratio: float
    label: str
    posts_15m: int = 0          # 最近 15 分钟发帖流速（盖楼速度）
    platforms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "totalPosts": self.total_posts,
            "validPosts": self.valid_posts,
            "spamPosts": self.spam_posts,
            "bullCount": self.bull_count,
            "divergenceCount": self.divergence_count,
            "bearCount": self.bear_count,
            "bullRatio": round(self.bull_ratio, 1),
            "divergenceRatio": round(self.divergence_ratio, 1),
            "bearRatio": round(self.bear_ratio, 1),
            "label": self.label,
            "posts15m": self.posts_15m,
            "platforms": list(self.platforms),
        }


# ── 快照 ──────────────────────────────────────────────────────────────────────


@dataclass
class RadarSnapshot:
    """`.data/short-term-radar-snapshot.json` 的结构：SH-03 的双视图直接消费它。"""

    generated_at: str
    mode: str
    data_quality: dict[str, Any] = field(default_factory=dict)
    theme_ladders: list[dict[str, Any]] = field(default_factory=list)
    top_resonance_stocks: list[dict[str, Any]] = field(default_factory=list)
    focus_pool_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "generatedAt": self.generated_at,
            "mode": self.mode,
            "dataQuality": self.data_quality,
            "focusPoolSize": self.focus_pool_size,
            "themeLadders": self.theme_ladders,
            "topResonanceStocks": self.top_resonance_stocks,
        }


# ── 推送条目 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class IngestItem:
    """`POST /api/ingest/items` 的一条：字段与后端 `ItemIn` 一一对应。

    bodyText 缺失时后端保持 `body_status='pending'`；带上则直接落 `ok`，
    worker 不再对 WAF 页面或合成管道 URL 发起无效二次抓取。
    """

    source_id: str
    title: str
    url: str
    published_at: str | None = None
    author: str | None = None
    excerpt: str | None = None
    body_text: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": self.title, "url": self.url}
        if self.published_at:
            payload["publishedAt"] = self.published_at
        if self.author:
            payload["author"] = self.author
        if self.excerpt:
            payload["excerpt"] = self.excerpt
        if self.body_text:
            payload["bodyText"] = self.body_text
        if self.raw:
            payload["raw"] = self.raw
        return payload
