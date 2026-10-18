"""System 1：反水贴过滤、三类情绪打分、社区情绪温度条与跨平台人气共振。

零 Token：全部规则来自 `docs/aihot_research/dict/sentiment_dict.json`（169 个情绪词 + 14 条
水贴正则，词表由谷米在东财 58 个股吧 7401 条标题上实测校准）。

两个容易做错的地方，这里明确按如下口径：

1. `context_dependent` 的单字/泛词（如「格局」「一字」）在股吧里几乎每帖都有，直接计入会把
   情绪条打平。词典只给了布尔标记没给配对规则，所以修正表写在本文件（`CONTEXT_RULES`）：
   只有「触发词 + 反向语境词」同帖出现时才翻转方向，并在 `sentiment_context_notes` 留痕，
   让「为什么这条算看多」可回查。
2. 水贴（加微信/进群/荐股老师/扫码）与情绪无关但会淹没热度：命中即 `is_spam=True`，
   既不计情绪，也不进推送。
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from .config import load_json
from .schema import (
    LABEL_CALM,
    LABEL_DIVERGENCE,
    LABEL_EUPHORIA,
    LABEL_NUKE,
    SENTIMENT_BEAR,
    SENTIMENT_BULL,
    SENTIMENT_DIVERGENCE,
    CommunityPost,
    FocusStock,
    SentimentSummary,
)

BEIJING = timezone(timedelta(hours=8))

# 情绪类别 → 词条键
CATEGORY_KEYS = {
    SENTIMENT_BULL: "extreme_bull_consistent",
    SENTIMENT_DIVERGENCE: "divergence_gaming",
    SENTIMENT_BEAR: "panic_bear_nuke",
}

# 上下文修正：(触发词, 反向语境词, 修正到的类别, 修正后的权重, 说明)
# 词表只标了 context_dependent=true，真正的配对规则来自短线社区的实际用法：
# 「吃面」单独出现是恐慌，但「吃面 + 大长腿/反包/地天板」是次日反包的看多预期；
# 「格局」单独出现是中性词，但「格局 + 被埋/大面/站岗」是把风险摊给追高者的结构。
CONTEXT_RULES: tuple[tuple[str, tuple[str, ...], str, int, str], ...] = (
    ("吃面", ("大长腿", "反包", "地天板", "翘板"), SENTIMENT_BULL, 2, "吃面+反包语境→转看多"),
    ("格局", ("被埋", "大面", "站岗", "接盘"), SENTIMENT_BEAR, -2, "格局+被埋/大面语境→转恐慌"),
    ("弱转强", ("炸板", "回封", "反抽", "低吸"), SENTIMENT_DIVERGENCE, 1, "弱转强+炸板回封语境→转分歧博弈"),
    ("格局", ("低吸", "潜伏", "打板", "加仓"), SENTIMENT_BULL, 1, "格局+主动做多语境→转一致看多"),
)

# 语境门控：这些词在产业/长文语境里是中性描述，在散户语境里才带方向
# （词典把其中多数标了 context_dependent=true，但没给配对规则；meta 也提示「单字/泛词误伤多」）。
# 实测误伤案例：雪球深度长文里的「出货节奏」「1.6T 产能释放」会把深度逻辑帖判成恐慌出逃——
# 所以这类词只在带明确散户语境线索时才计分，宁可漏判也不误杀。
GATED_TERMS = frozenset({"一字", "核", "面", "躺", "T", "崩", "出货", "格局", "板上", "分歧"})
CONTEXT_CUES: tuple[str, ...] = (
    "割肉", "跑路", "砸盘", "跳水", "绿盘", "被套", "吃面", "大面", "恐慌", "核按钮",
    "出货砸", "主力出货", "主力砸", "出货了", "砸了", "拉板", "封板", "涨停", "打板", "龙头", "低吸",
)

# 分句否定前缀（LITE-03）：正向情绪词被这些前缀修饰时不是看多——「无法继续涨停」「不能连板」
# 「谨防追高」都要按负向计分。前缀必须在命中词前方同一分句内（未被标点隔断）。
NEGATION_PREFIXES: tuple[str, ...] = (
    "无法", "不能", "不会", "难以", "未能", "没能", "不再", "不可能", "不看好", "谨防", "小心", "警惕", "没有",
)
# 单字否定前缀只认紧邻（前 1~2 字），避免「未来」「艰难」等无关词误伤
NEGATION_CHARS: tuple[str, ...] = ("未", "难", "别", "莫")
CLAUSE_BREAKS = "，。！？；,.!?;"


def _negated_before(text: str, start: int) -> bool:
    """命中词前方（同一分句内、1~6 字窗口）是否带否定前缀。"""
    window = text[max(0, start - 6) : start]
    cut = max((index + 1 for index, ch in enumerate(window) if ch in CLAUSE_BREAKS), default=0)
    clause = window[cut:]
    if not clause:
        return False
    if any(prefix in clause for prefix in NEGATION_PREFIXES):
        return True
    return any(ch in clause[-2:] for ch in NEGATION_CHARS)

# 情绪标签门槛：占比要够高且样本够多，否则只算「情绪中性」（1 条帖不叫一致亢奋）
LABEL_MIN_RATIO = 55.0
LABEL_MIN_POSTS = 2

# 共振分：五个来源的满分，合计 100
RESONANCE_WEIGHTS = {
    "ths": 20.0,
    "dc": 15.0,
    "xueqiu": 15.0,
    "taoguba": 20.0,
    "guba": 20.0,
    "breadth": 10.0,
}


@dataclass(frozen=True)
class SentimentEntry:
    """词典里的一条情绪词。"""

    term: str
    weight: int
    category: str
    context_dependent: bool = False
    meaning: str = ""


@dataclass(frozen=True)
class SpamRule:
    """一条水贴正则。"""

    rule_id: str
    pattern: re.Pattern[str]
    example: str = ""


class SentimentEngine:
    """加载词典并对帖子打分。无状态，可复用。"""

    def __init__(self, dictionary: dict[str, Any]) -> None:
        self.meta: dict[str, Any] = dictionary.get("meta") or {}
        self.entries: dict[str, tuple[SentimentEntry, ...]] = {}
        for category, key in CATEGORY_KEYS.items():
            rows: list[SentimentEntry] = []
            for row in dictionary.get(key) or []:
                term = str(row.get("term") or "").strip()
                if not term:
                    continue
                rows.append(
                    SentimentEntry(
                        term=term,
                        weight=int(row.get("weight") or 0),
                        category=category,
                        context_dependent=bool(row.get("context_dependent")),
                        meaning=str(row.get("meaning") or ""),
                    )
                )
            self.entries[category] = tuple(rows)

        self.spam_rules: tuple[SpamRule, ...] = tuple(
            SpamRule(
                rule_id=str(row.get("id") or f"rule{index}"),
                pattern=re.compile(str(row.get("regex") or "")),
                example=str(row.get("example") or ""),
            )
            for index, row in enumerate(dictionary.get("spam_noise_patterns") or [])
            if row.get("regex")
        )

        # 长词优先匹配：「核按钮」不能被「核」先吃掉，「一字板」优先于「一字」
        self._ordered: dict[str, tuple[SentimentEntry, ...]] = {
            category: tuple(sorted(entries, key=lambda entry: (-len(entry.term), entry.term)))
            for category, entries in self.entries.items()
        }
        # 三类合并成一条最长优先表：先命中的长词会「吃掉」被它包含的短词，
        # 否则「核按钮」「核」「跌停板」「跌停」会重复计权，把强度算虚。
        self._merged: tuple[SentimentEntry, ...] = tuple(
            sorted(
                (entry for entries in self._ordered.values() for entry in entries),
                key=lambda entry: (-len(entry.term), entry.term),
            )
        )

    @classmethod
    def load(cls, path) -> "SentimentEngine":
        return cls(load_json(path) or {})  # type: ignore[arg-type]

    # ── 水贴 ──────────────────────────────────────────────────────────────────

    def spam_rule_for(self, text: str) -> SpamRule | None:
        """返回命中的第一条水贴规则；没命中返回 None。"""
        for rule in self.spam_rules:
            if rule.pattern.search(text):
                return rule
        return None

    # ── 情绪 ──────────────────────────────────────────────────────────────────

    def _matches(self, text: str, category: str) -> list[SentimentEntry]:
        return [entry for entry in self._ordered[category] if entry.term in text]

    def _longest_matches(self, text: str) -> list[SentimentEntry]:
        """最长优先 + 语境门控：命中「核按钮」就不再计「核」；「出货」没有散户语境就不计。"""
        cue_hit = any(cue in text for cue in CONTEXT_CUES)
        matched: list[SentimentEntry] = []
        consumed: list[str] = []
        for entry in self._merged:
            if entry.term not in text:
                continue
            if any(entry.term != other and entry.term in other for other in consumed):
                continue  # 已被更长的命中词包含
            if entry.term in GATED_TERMS and not cue_hit:
                rule_hit = any(
                    entry.term == trigger and any(remedy in text for remedy in remedies)
                    for trigger, remedies, _target, _weight, _note in CONTEXT_RULES
                )
                if not rule_hit:
                    continue  # 泛词只在中性语境出现，忽略
            # 分句否定前缀：「无法继续涨停」不是看多，正向词被否定时改记负分（LITE-03）
            if entry.category == SENTIMENT_BULL and _negated_before(text, text.find(entry.term)):
                matched.append(
                    SentimentEntry(
                        term=entry.term,
                        weight=-entry.weight,
                        category=SENTIMENT_BEAR,
                        context_dependent=entry.context_dependent,
                        meaning="句内否定前缀修正：正向词不计看多，改记负分",
                    )
                )
                consumed.append(entry.term)
                continue
            consumed.append(entry.term)
            matched.append(entry)
        return matched

    def score_post(self, post: CommunityPost) -> CommunityPost:
        """就地回填 `is_spam` / `sentiment` / `sentiment_score` / 命中词，并返回同一对象。"""
        text = post.text
        spam = self.spam_rule_for(text)
        if spam is not None:
            post.is_spam = True
            post.spam_rule = spam.rule_id
            post.sentiment = None
            post.sentiment_score = 0
            post.sentiment_terms = ()
            post.sentiment_context_notes = ()
            return post

        post.is_spam = False
        post.spam_rule = None

        matched = self._longest_matches(text)

        # 上下文修正：触发词与反向语境同帖出现时改判类别并留痕
        notes: list[str] = []
        adjusted: list[SentimentEntry] = []
        for entry in matched:
            replacement: SentimentEntry | None = None
            for trigger, remedies, target, weight, note in CONTEXT_RULES:
                if entry.term != trigger:
                    continue
                if any(remedy in text for remedy in remedies):
                    replacement = SentimentEntry(
                        term=entry.term, weight=weight, category=target, context_dependent=True, meaning=note
                    )
                    notes.append(note)
                    break
            adjusted.append(replacement or entry)

        totals = {category: 0 for category in CATEGORY_KEYS}
        terms: list[str] = []
        for entry in adjusted:
            totals[entry.category] += entry.weight
            terms.append(entry.term)

        # 主类按强度（绝对值）选：一条「跌停+核按钮+被埋」的帖哪怕蹭到「板上」也仍然偏空。
        # 同强度时按谨慎原则归分歧。
        best = max(
            CATEGORY_KEYS,
            key=lambda category: (abs(totals[category]), category == SENTIMENT_DIVERGENCE),
        )
        top = totals[best]
        if top == 0 or not any(totals.values()):
            post.sentiment = None
            post.sentiment_score = 0
        else:
            post.sentiment = best
            post.sentiment_score = top
        post.sentiment_terms = tuple(dict.fromkeys(terms))
        post.sentiment_context_notes = tuple(dict.fromkeys(notes))
        return post

    def score_posts(self, posts: Iterable[CommunityPost]) -> list[CommunityPost]:
        return [self.score_post(post) for post in posts]

    # ── 汇总 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _within_15m(published_at: str | None, now: datetime) -> bool:
        if not published_at:
            return False
        try:
            moment = datetime.fromisoformat(published_at)
        except ValueError:
            return False
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=BEIJING)
        return now - timedelta(minutes=15) <= moment <= now + timedelta(minutes=1)

    def summarize(self, code: str, posts: list[CommunityPost], now: datetime) -> SentimentSummary:
        """一只票的情绪温度条。

        分母是**有明确三态判定的有效帖**（水贴与中性闲聊不进分母），
        因此 `bull_ratio + divergence_ratio + bear_ratio` 恒为 100；全中性时三项均为 0。
        `valid_posts` 记的是非水贴帖总数，便于对照「多少是噪声、多少是没有方向的话」。
        """
        scored = [self.score_post(post) for post in posts]
        valid = [post for post in scored if not post.is_spam]
        spam = len(scored) - len(valid)
        directed = [post for post in valid if post.sentiment]

        counts = {SENTIMENT_BULL: 0, SENTIMENT_DIVERGENCE: 0, SENTIMENT_BEAR: 0}
        for post in directed:
            counts[post.sentiment] += 1

        total_directed = len(directed)
        if total_directed:
            bull = counts[SENTIMENT_BULL] * 100.0 / total_directed
            divergence = counts[SENTIMENT_DIVERGENCE] * 100.0 / total_directed
            bear = counts[SENTIMENT_BEAR] * 100.0 / total_directed
        else:
            bull = divergence = bear = 0.0

        label = LABEL_CALM
        if total_directed >= LABEL_MIN_POSTS:
            ranked = sorted(
                ((SENTIMENT_BULL, bull), (SENTIMENT_DIVERGENCE, divergence), (SENTIMENT_BEAR, bear)),
                key=lambda item: item[1],
                reverse=True,
            )
            top_category, top_ratio = ranked[0]
            if top_ratio >= LABEL_MIN_RATIO:
                label = {
                    SENTIMENT_BULL: LABEL_EUPHORIA,
                    SENTIMENT_DIVERGENCE: LABEL_DIVERGENCE,
                    SENTIMENT_BEAR: LABEL_NUKE,
                }[top_category]

        return SentimentSummary(
            code=code,
            total_posts=len(scored),
            valid_posts=len(valid),
            spam_posts=spam,
            bull_count=counts[SENTIMENT_BULL],
            divergence_count=counts[SENTIMENT_DIVERGENCE],
            bear_count=counts[SENTIMENT_BEAR],
            bull_ratio=bull,
            divergence_ratio=divergence,
            bear_ratio=bear,
            label=label,
            posts_15m=sum(1 for post in valid if self._within_15m(post.published_at, now)),
            platforms=tuple(dict.fromkeys(post.platform for post in valid)),
        )


def _rank_decay(rank: int | None) -> float:
    """名次 → 0~1 热度系数：1 名满分，10 名约 0.5，20 名约 0.25，之后不再加分。"""
    if not rank or rank <= 0:
        return 0.0
    if rank <= 1:
        return 1.0
    if rank >= 20:
        return 0.25
    return max(0.25, 1.0 - math.log2(rank) / 4.0)


def score_resonance(
    stock: FocusStock,
    summary: SentimentSummary,
    taoguba_mentions: int | None = None,
) -> tuple[float, tuple[str, ...]]:
    """跨平台人气共振分（0~100）与命中平台说明。

    五个来源各给固定满分：热榜三家看名次衰减，淘股吧看提及量，东财股吧看 15m 盖楼流速，
    另给 10 分「情绪广度」——有足够多的有效帖且情绪方向明确才算真的有人吵。
    """
    parts = {
        "ths": RESONANCE_WEIGHTS["ths"] * _rank_decay(stock.hot_rank_ths),
        "dc": RESONANCE_WEIGHTS["dc"] * _rank_decay(stock.hot_rank_dc),
        "xueqiu": RESONANCE_WEIGHTS["xueqiu"] * _rank_decay(stock.hot_rank_xq),
        "taoguba": RESONANCE_WEIGHTS["taoguba"] * min(max(taoguba_mentions or stock.taoguba_mentions, 0) / 5.0, 1.0),
        "guba": RESONANCE_WEIGHTS["guba"] * min(summary.posts_15m / 10.0, 1.0),
        "breadth": RESONANCE_WEIGHTS["breadth"] if summary.valid_posts >= 5 and summary.label != LABEL_CALM else 0.0,
    }
    hits: list[str] = []
    if stock.hot_rank_ths:
        hits.append(f"同花顺热榜#{stock.hot_rank_ths}")
    if stock.hot_rank_dc:
        hits.append(f"东财热榜#{stock.hot_rank_dc}")
    if stock.hot_rank_xq:
        hits.append(f"雪球热股#{stock.hot_rank_xq}")
    mentions = taoguba_mentions if taoguba_mentions is not None else stock.taoguba_mentions
    if mentions:
        hits.append(f"淘股吧热议×{mentions}")
    if summary.posts_15m:
        hits.append(f"股吧15m盖楼×{summary.posts_15m}")
    return min(100.0, round(sum(parts.values()), 1)), tuple(hits)


def apply_to_stocks(
    stocks: list[FocusStock],
    posts_by_code: dict[str, list[CommunityPost]],
    engine: SentimentEngine,
    now: datetime,
) -> tuple[list[FocusStock], dict[str, SentimentSummary]]:
    """给每个焦点股算情绪与共振分。

    `FocusStock` 是不可变的，所以返回**新池**（带 `resonance_score` / `platforms_hit` /
    `taoguba_mentions`）与逐股情绪汇总，而不是就地改写调用方的对象。
    """
    summaries: dict[str, SentimentSummary] = {}
    updated: list[FocusStock] = []
    for stock in stocks:
        posts = posts_by_code.get(stock.code, [])
        summary = engine.summarize(stock.code, posts, now)
        summaries[stock.code] = summary
        mentions = sum(1 for post in posts if post.platform == "taoguba" and not post.is_spam)
        score, hits = score_resonance(stock, summary, mentions)
        updated.append(
            replace(stock, resonance_score=score, platforms_hit=hits, taoguba_mentions=mentions)
        )
    return updated, summaries


def now_beijing() -> datetime:
    return datetime.now(tz=BEIJING)
