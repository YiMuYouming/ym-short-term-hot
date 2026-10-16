"""雪球：首页匿名 Cookie 预热 + 热股榜 + 个股最新/最热讨论，深度作者提权。

实测要点（`docs/aihot_research/endpoints.json`，2026-10-16 浏览器实测）：

- **纯 curl 会被阿里云 WAF 拦**，必须先访问首页把匿名 cookie（`xq_a_token`、`acw_tc`）拿到手，
  再打 JSON 接口；不需要账号密码。
- 热股榜 `stock.xueqiu.com/v5/stock/hot_stock/list.json` 无 cookie 直接 400。
- 个股讨论 `query/v1/symbol/search/status.json`：`sort=time` 最新讨论、`sort=alpha` 高赞深度帖，
  后者带 `excellent_comments[]`。
- 深度作者名录在 `docs/aihot_research/xueqiu.json`（23 人）；名录之外再给一条规则：
  正文 ≥150 字且含产业链/订单/预期差类关键词的也算深度逻辑候选。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from ..config import load_json
from ..schema import CommunityPost
from ..sentiment_engine import BEIJING
from . import FetchError, HttpClient

HOME_URL = "https://www.xueqiu.com/"
HOT_STOCK_URL = "https://stock.xueqiu.com/v5/stock/hot_stock/list.json"
STATUS_URL = "https://www.xueqiu.com/query/v1/symbol/search/status.json"
HOT_STATUS_URL = "https://www.xueqiu.com/statuses/hot/listV2.json"

# 深度逻辑候选：字数够 + 出现产业/预期差类表述
DEEP_LOGIC_MIN_CHARS = 150
DEEP_LOGIC_KEYWORDS = (
    "产业链", "订单", "产能", "预期差", "正宗", "份额", "提价", "涨价", "毛利",
    "业绩", "测算", "弹性", "壁垒", "卡位", "供需", "出货", "量产",
)


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _iso_from_ms(value: Any) -> str | None:
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    if ms <= 0:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=BEIJING).isoformat()


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def load_author_index(path) -> dict[str, dict[str, Any]]:
    """`xueqiu.json` → {uid: {nickname, focus}}。"""
    rows = load_json(path) or []
    index: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        uid = str(row.get("xueqiu_id") or "").strip()
        if uid:
            index[uid] = {
                "nickname": str(row.get("nickname") or ""),
                "focus": str(row.get("focus") or ""),
            }
    return index


def looks_deep_logic(title: str, content: str | None) -> bool:
    """长文 + 产业/预期差关键词 = 深度逻辑候选（名录之外的第二条规则）。"""
    text = f"{title}\n{content or ''}"
    if len(_strip_html(text)) < DEEP_LOGIC_MIN_CHARS:
        return False
    return any(keyword in text for keyword in DEEP_LOGIC_KEYWORDS)


def parse_hot_stock(payload: Any) -> list[dict[str, Any]]:
    """热股榜 → [{code, name, rank, symbol, change_pct}]。"""
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = (data or {}).get("items") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        code = "".join(ch for ch in symbol if ch.isdigit())[:6]
        if not code:
            continue
        out.append(
            {
                "code": code,
                "symbol": symbol,
                "name": str(row.get("name") or code),
                "rank": _int(row.get("rank")) or index,
                "change_pct": row.get("percent"),
            }
        )
    return out


def parse_symbol_status(payload: Any, code: str, stock_name: str | None = None,
                        author_index: dict[str, dict[str, Any]] | None = None,
                        symbol: str | None = None) -> list[CommunityPost]:
    """个股讨论 JSON → 帖子列表（纯函数）。`list[]` 是主帖，`excellent_comments[]` 一并带上。"""
    data = payload.get("data") if isinstance(payload, dict) else payload
    rows = data.get("list") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []

    def build(row: dict[str, Any], from_comment: bool) -> CommunityPost | None:
        text = _strip_html(str(row.get("text") or row.get("description") or ""))
        if not text:
            return None
        post_id = str(row.get("id") or "")
        if not post_id:
            return None
        user = row.get("user") if isinstance(row.get("user"), dict) else {}
        uid = str(user.get("id") or row.get("user_id") or "").strip()
        known = (author_index or {}).get(uid)
        title = text if len(text) <= 60 else text[:57] + "…"
        return CommunityPost(
            platform="xueqiu",
            post_id=post_id,
            url=f"https://xueqiu.com{row.get('target') or '/statuses/' + post_id}",
            title=title,
            code=code,
            stock_name=stock_name,
            content=text,
            author_id=uid or None,
            author_name=str(user.get("screen_name") or "").strip() or None,
            published_at=_iso_from_ms(row.get("created_at") or row.get("timeBefore")),
            like_count=_int(row.get("like_count")),
            comment_count=_int(row.get("reply_count")),
            is_deep_logic=bool(known) or looks_deep_logic(text, None),
            youzi_style=(known["focus"],) if known else (),
        )

    posts: list[CommunityPost] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        post = build(row, from_comment=False)
        if post:
            posts.append(post)
    for row in (data.get("excellent_comments") or []) if isinstance(data, dict) else []:
        if isinstance(row, dict):
            post = build(row, from_comment=True)
            if post:
                post.post_id = f"{post.post_id}-c"
                posts.append(post)
    return posts


def parse_hot_statuses(payload: Any, author_index: dict[str, dict[str, Any]] | None = None) -> list[CommunityPost]:
    """全站热门动态 → 帖子列表（纯函数）。"""
    data = payload.get("data") if isinstance(payload, dict) else payload
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    out: list[CommunityPost] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        data_item = item.get("data") if isinstance(item.get("data"), dict) else item
        text = _strip_html(str(data_item.get("text") or ""))
        if not text:
            continue
        uid = str(data_item.get("user_id") or "")
        known = (author_index or {}).get(uid)
        out.append(
            CommunityPost(
                platform="xueqiu",
                post_id=str(item.get("id") or data_item.get("id") or text[:12]),
                url=f"https://xueqiu.com{data_item.get('target') or '/statuses/' + str(item.get('id'))}",
                title=text if len(text) <= 60 else text[:57] + "…",
                content=text,
                author_id=uid or None,
                author_name=str(data_item.get("screen_name") or "").strip() or None,
                published_at=_iso_from_ms(item.get("created_at")),
                like_count=_int(item.get("like_count")),
                comment_count=_int(item.get("reply_count")),
                is_deep_logic=bool(known) or looks_deep_logic(text, None),
                youzi_style=(known["focus"],) if known else (),
            )
        )
    return out


def warm_up(client: HttpClient) -> None:
    """先访问首页拿匿名 cookie；失败只记账，不抛。"""
    client.warm_up(HOME_URL)


def fetch_hot_stock(client: HttpClient, size: int = 30) -> list[dict[str, Any]]:
    """雪球热股榜（沪深 A 股 1 小时热度）。"""
    from . import build_url

    try:
        payload = client.get_json(build_url(HOT_STOCK_URL, {"size": size, "_type": 10, "type": 10}))
    except FetchError as exc:
        client.note_failure(f"xueqiu hot_stock: {exc}")
        return []
    return parse_hot_stock(payload)


def fetch_stock_status(client: HttpClient, code: str, symbol: str, stock_name: str | None,
                       author_index: dict[str, dict[str, Any]] | None, sort: str = "time", count: int = 20) -> list[CommunityPost]:
    """单只票的最新（time）或最热（alpha）讨论。"""
    from . import build_url

    try:
        payload = client.get_json(
            build_url(STATUS_URL, {"count": count, "comment": 0, "symbol": symbol, "hl": 0,
                                   "source": "all", "sort": sort, "page": 1, "q": "", "type": 11})
        )
    except FetchError as exc:
        client.note_failure(f"xueqiu status {symbol}: {exc}")
        return []
    return parse_symbol_status(payload, code, stock_name, author_index, symbol)


def collect(client: HttpClient, author_path, stocks: list[Any], per_stock: int = 10) -> tuple[list[dict[str, Any]], dict[str, list[CommunityPost]]]:
    """采集雪球：热股榜 + 每只焦点股的最热讨论。返回 (热股榜, {code: 帖子})。

    跨股票按 `post_id` 去重：一条热帖可能同时出现在多只票的讨论流里，
    重复计入会让情绪条与共振分虚高。
    """
    warm_up(client)
    hot = fetch_hot_stock(client)
    author_index = load_author_index(author_path)
    posts_by_code: dict[str, list[CommunityPost]] = {}
    seen: set[str] = set()
    for stock in stocks:
        picked: list[CommunityPost] = []
        for sort in ("alpha", "time"):
            for post in fetch_stock_status(client, stock.code, stock.symbol, stock.name, author_index, sort=sort):
                if post.post_id in seen:
                    continue
                seen.add(post.post_id)
                picked.append(post)
            if len(picked) >= per_stock:
                break
        if picked:
            posts_by_code[stock.code] = picked[:per_stock]
    return hot, posts_by_code
