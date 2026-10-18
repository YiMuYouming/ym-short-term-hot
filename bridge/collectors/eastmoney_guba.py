"""东方财富股吧：免 Cookie 的 JSON 列表接口 + 本地热度重排。

实测要点（`docs/aihot_research/endpoints.json`，2026-10-16 Grok 实测）：

- `gbapi.eastmoney.com/webarticlelist/api/Article/Articlelist` 无需 cookie 即可 200；
- `sorttype=0` 是按发帖时间倒序，`sorttype=1~8` 都退化成按最后回复时间——**没有原生热度排序**，
  所以热度必须本地算：`hot_weight = post_comment_count * 5 + post_click_count * 0.1`
  （评论权重远高于点击，与股吧「回复即参与」的实际行为一致）。
- 没有 `sorttype` 能给出「最热」，因此本模块同时算 **15m 发帖流速**（盖楼速度），
  它才是短线情绪最灵的先行指标。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Iterable

from ..schema import CommunityPost
from ..sentiment_engine import BEIJING
from . import FetchError, HttpClient, build_url

API_BASE = "https://gbapi.eastmoney.com/webarticlelist/api/Article/Articlelist"
DETAIL_URL = "https://guba.eastmoney.com/news,{code},{post_id}.html"
MOBILE_LIST_URL = "https://mguba.eastmoney.com/mguba/list/{code}"

# 评论比点击更能说明「有人在吵」
COMMENT_WEIGHT = 5.0
CLICK_WEIGHT = 0.1


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _iso_from_ms(value: Any) -> str | None:
    """发布时间 → ISO 8601（北京时间）。

    接口给过两种形状：毫秒时间戳（旧）与「2026-10-17 20:02:14」字符串（2026-10-17 实测）；
    缺失或非法返回 None（不猜时间）。
    """
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    if text.isdigit():
        ms = int(text)
        if ms <= 0:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=BEIJING).isoformat()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=BEIJING)).isoformat()


def hot_weight(comment_count: int, click_count: int) -> float:
    """本地热度：评论 ×5 + 点击 ×0.1。"""
    return comment_count * COMMENT_WEIGHT + click_count * CLICK_WEIGHT


def parse_articlelist(payload: Any, code: str, stock_name: str | None = None) -> list[CommunityPost]:
    """Articlelist JSON → CommunityPost 列表（纯函数）。"""
    rows = payload.get("re") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    posts: list[CommunityPost] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("post_title") or "").strip()
        post_id = str(row.get("post_id") or "").strip()
        if not title or not post_id:
            continue
        comments = _int(row.get("post_comment_count"))
        clicks = _int(row.get("post_click_count"))
        bar_code = str(row.get("stockbar_code") or code).strip() or code
        posts.append(
            CommunityPost(
                platform="eastmoney_guba",
                post_id=post_id,
                url=str(row.get("art_unique_url") or DETAIL_URL.format(code=bar_code, post_id=post_id)),
                title=title,
                code=bar_code,
                stock_name=str(row.get("stockbar_name") or stock_name or "").strip() or None,
                author_id=str(row.get("user_id") or "").strip() or None,
                author_name=str(row.get("user_nickname") or "").strip() or None,
                published_at=_iso_from_ms(row.get("post_publish_time")),
                comment_count=comments,
                view_count=clicks,
                like_count=_int(row.get("post_forward_count")),
                hot_weight=hot_weight(comments, clicks),
            )
        )
    return posts


def parse_mobile_list(html: str, code: str) -> dict[str, str]:
    """移动端列表页里嵌 JSON 含 `post_content`；按 post_id 索引正文。

    实测该页约 300KB，正文在内嵌 JSON 的 `post_content` 字段里；解析失败返回空表，
    让调用方保持「只有标题」的帖子（情绪照样能打，标题就是全部信息）。
    """
    import json
    import re

    out: dict[str, str] = {}
    for match in re.finditer(r'"post_id"\s*:\s*"?(\d+)"?.{0,4000}?"post_content"\s*:\s*"((?:[^"\\]|\\.)*)"', html, re.S):
        try:
            content = json.loads(f'"{match.group(2)}"')
        except json.JSONDecodeError:
            continue
        out[match.group(1)] = re.sub(r"<[^>]+>", " ", content).strip()
    return out


def attach_bodies(posts: list[CommunityPost], bodies: dict[str, str]) -> list[CommunityPost]:
    """把正文贴回帖子（按 post_id）。"""
    for post in posts:
        content = bodies.get(post.post_id)
        if content:
            post.content = content
    return posts


def count_posts_15m(posts: Iterable[CommunityPost], now: datetime) -> int:
    """最近 15 分钟的发帖数（盖楼流速）。时间缺失或未来的帖子不计入。"""
    floor = now - timedelta(minutes=15)
    total = 0
    for post in posts:
        if not post.published_at:
            continue
        try:
            moment = datetime.fromisoformat(post.published_at)
        except ValueError:
            continue
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=BEIJING)
        if floor <= moment <= now:
            total += 1
    return total


def rank_by_hot(posts: list[CommunityPost], top: int = 10) -> list[CommunityPost]:
    """本地热度排序（热度相同时按发帖时间新的在前）。"""
    return sorted(
        posts,
        key=lambda post: (-post.hot_weight, -(datetime.fromisoformat(post.published_at).timestamp() if post.published_at else 0), post.post_id),
    )[:top]


def fetch_stock(client: HttpClient, code: str, stock_name: str | None, page_size: int = 50, with_body: bool = True) -> list[CommunityPost]:
    """抓单只票的股吧帖子。任一步失败都记进 `client.failures` 并返回已拿到的部分。"""
    url = build_url(
        API_BASE,
        {"code": code, "sorttype": 0, "ps": page_size, "p": 1, "from": "CommonBaPost",
         "deviceid": 1, "version": 200, "product": "Guba", "plat": "Web"},
    )
    try:
        payload = client.get_json(url, {"Referer": f"https://guba.eastmoney.com/list,{code}.html"})
    except FetchError as exc:
        client.note_failure(f"eastmoney_guba {code}: {exc}")
        return []
    posts = parse_articlelist(payload, code, stock_name)
    if with_body and posts:
        try:
            bodies = parse_mobile_list(client.get(MOBILE_LIST_URL.format(code=code)), code)
            if bodies:
                attach_bodies(posts, bodies)
            else:
                # 移动端正文页被 WAF「身份核实」拦下时静悄悄返回空——显式记账，
                # 快照 dataQuality.httpFailures 才说得出「为什么高亮帖只有标题」
                client.note_failure(f"eastmoney_guba body {code}: 移动端正文页无帖子正文（WAF 拦截或改版）")
        except FetchError as exc:
            client.note_failure(f"eastmoney_guba body {code}: {exc}")
    return posts


def collect(client: HttpClient, stocks: list[Any], top: int = 10) -> dict[str, list[CommunityPost]]:
    """按焦点股池逐只采集，返回 {code: 高热帖}。

    同一 `post_id` 只保留一次：股吧接口按 code 返回，可能出现同一帖挂在多个吧下，
    重复条目会在情绪条里被数两次，把热度算虚。
    """
    out: dict[str, list[CommunityPost]] = {}
    seen: set[str] = set()
    for stock in stocks:
        picked: list[CommunityPost] = []
        for post in fetch_stock(client, stock.code, stock.name):
            if post.post_id in seen:
                continue
            seen.add(post.post_id)
            picked.append(post)
        if picked:
            out[stock.code] = rank_by_hot(picked, top)
    return out
