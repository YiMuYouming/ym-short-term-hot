"""淘股吧：移动端 JSON XHR + PC 精华复盘帖 + 题材榜，命中活跃实盘游资名录的打上 VIP 标记。

实测要点（`docs/aihot_research/endpoints.json`）：

- **不存在独立的 24h 热帖榜路由**：`/hot`、`/hotTopic` 都是 200 但内容是首页回退，调用它们
  等于白跑一趟。本模块只用三个真实入口。
- 移动版首页信息流由 XHR `m.tgb.cn/getMZh?pageNo=1` 加载，返回 JSON，数据在
  `dto.indexList.listData[]`，含 `userID`/`userName`/`subject`/`subinfo`/`replyNum`/`viewNum`。
- 精华页分页必须带 `-{sort}` 后缀：`/jinghua/1-1`（按发帖日期）、`/jinghua/1-2`（按热度），
  `/jinghua/2` 直接 404。
- 活跃实盘游资名录在 `docs/aihot_research/tgb.json`（33 人，谷米核实），命中即提权。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from typing import Any

from ..config import load_json
from ..schema import CommunityPost
from ..sentiment_engine import BEIJING
from . import FetchError, HttpClient, build_url

MZH_URL = "https://m.tgb.cn/getMZh"
JINGHUA_URL = "https://www.tgb.cn/jinghua/{page}-{sort}"
TICAI_RANKING_URL = "https://www.tgb.cn/ticai/ranking"
STOCK_BAR_URL = "https://www.tgb.cn/quotes/{market}{code}"
POST_URL = "https://www.tgb.cn/a/{short_code}"
USER_URL = "https://www.tgb.cn/blog/{user_id}"

# 严禁使用：实测为首页回退的伪路由，保留常量只为让「为什么不调它」有据可查
FORBIDDEN_ROUTES = ("https://www.tgb.cn/hot", "https://www.tgb.cn/hotTopic")

XHR_HEADERS = {"X-Requested-With": "XMLHttpRequest", "Referer": "https://m.tgb.cn/"}

# 列表页上的时间常写成「10-16 10:05」（没有年份），年份要按当前基准补齐
_YEARLESS_TIME = re.compile(r"^(\d{1,2})-(\d{1,2})[ T](\d{1,2}):(\d{2})$")


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def load_vip_index(path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """`tgb.json` → (按 user_id 的索引, 按昵称的索引)。昵称大小写不敏感。"""
    rows = load_json(path) or []
    by_id: dict[str, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        entry = {
            "nickname": str(row.get("nickname") or ""),
            "style": tuple(str(item) for item in row.get("style_tags") or []),
            "why_watch": str(row.get("why_watch") or ""),
            "verify_status": str(row.get("verify_status") or ""),
        }
        user_id = str(row.get("user_id") or "").strip()
        if user_id:
            by_id[user_id] = entry
        if entry["nickname"]:
            by_name[entry["nickname"].lower()] = entry
    return by_id, by_name


def match_vip(user_id: str | None, user_name: str | None, vip_by_id: dict, vip_by_name: dict) -> dict[str, Any] | None:
    """按 ID 优先、昵称兜底匹配名录；两个都不中返回 None。"""
    if user_id and str(user_id).strip() in vip_by_id:
        return vip_by_id[str(user_id).strip()]
    if user_name:
        return vip_by_name.get(user_name.strip().lower())
    return None


def parse_getmzh(payload: Any, vip_by_id: dict | None = None, vip_by_name: dict | None = None) -> list[CommunityPost]:
    """`getMZh` JSON → 帖子列表（纯函数）。真实路径：dto.indexList.listData[]。"""
    rows: Any = payload
    if isinstance(payload, dict):
        dto = payload.get("dto") or payload.get("data") or payload
        index_list = dto.get("indexList") if isinstance(dto, dict) else None
        rows = (index_list or {}).get("listData") if isinstance(index_list, dict) else None
    if not isinstance(rows, list):
        return []

    posts: list[CommunityPost] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        subject = str(row.get("subject") or "").strip()
        topic_id = str(row.get("newTopicID") or row.get("topicID") or "").strip()
        if not subject or not topic_id:
            continue
        user_id = str(row.get("userID") or "").strip() or None
        user_name = str(row.get("userName") or "").strip() or None
        vip = match_vip(user_id, user_name, vip_by_id or {}, vip_by_name or {})
        posts.append(
            CommunityPost(
                platform="taoguba",
                post_id=topic_id,
                url=POST_URL.format(short_code=topic_id),
                title=subject,
                content=str(row.get("subinfo") or "").strip() or None,
                author_id=user_id,
                author_name=user_name,
                published_at=_normalize_time(row.get("createTime") or row.get("lastReplyDate")),
                comment_count=_int(row.get("replyNum")),
                view_count=_int(row.get("viewNum")),
                is_vip_youzi=vip is not None,
                youzi_style=vip["style"] if vip else (),
            )
        )
    return posts


class _JinghuaParser(HTMLParser):
    """精华帖列表页：`div.Nbbs-tiezi-lists` 里取标题链接、作者 data 属性与回复/浏览数。

    用 div 深度计数切分行——列表页里每行的标签嵌套不固定，靠 class 逐个判断会把
    兄弟节点吞进同一行（实测第一版就丢了作者与计数）。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, Any]] = []
        self._row: dict[str, Any] | None = None
        self._depth = 0
        self._talk_parts: list[str] = []
        self._in_talk = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: (value or "") for key, value in attrs}
        if tag == "div":
            self._depth += 1
        if tag == "div" and "Nbbs-tiezi-lists" in attributes.get("class", "").split():
            self._row = {"short_code": None, "title": None, "user_id": None, "last_reply": None, "counts": ""}
            self._depth = 1
            return
        if self._row is None:
            return
        if tag == "a" and attributes.get("href", "").startswith("/a/"):
            short = attributes["href"].rsplit("/", 1)[-1]
            title = (attributes.get("title") or "").strip()
            if self._row["short_code"] is None:
                self._row["short_code"] = short
                self._row["title"] = title or None
        if tag == "a" and attributes.get("href", "").startswith("/blog/") and attributes.get("data-user-id"):
            self._row["user_id"] = attributes["data-user-id"]
            self._row["last_reply"] = attributes.get("data-last-reply-date") or self._row["last_reply"]
        if tag == "div" and "middle-list-talk" in attributes.get("class", "").split():
            self._in_talk = True
            self._talk_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self._in_talk:
            if self._row is not None:
                self._row["counts"] = " ".join("".join(self._talk_parts).split())
            self._in_talk = False
        if tag != "div":
            return
        if self._row is not None:
            self._depth -= 1
            if self._depth <= 0:
                if self._row.get("short_code"):
                    self.rows.append(self._row)
                self._row = None
        else:
            self._depth = max(self._depth - 1, 0)

    def handle_data(self, data: str) -> None:
        if self._in_talk:
            self._talk_parts.append(data)


def _counts(text: str) -> tuple[int, int]:
    """从「回复 12 / 浏览 345」里取两个数。"""
    import re

    numbers = [int(value) for value in re.findall(r"\d+", text or "")]
    if not numbers:
        return 0, 0
    if len(numbers) == 1:
        return numbers[0], 0
    return numbers[0], numbers[1]


def parse_jinghua(html: str, vip_by_id: dict | None = None, vip_by_name: dict | None = None) -> list[CommunityPost]:
    """精华页 HTML → 帖子列表（纯函数）。"""
    parser = _JinghuaParser()
    parser.feed(html or "")
    posts: list[CommunityPost] = []
    for row in parser.rows:
        short_code = row.get("short_code")
        title = (row.get("title") or "").strip()
        if not short_code or not title:
            continue
        replies, views = _counts(row.get("counts", ""))
        vip = match_vip(row.get("user_id"), None, vip_by_id or {}, vip_by_name or {})
        posts.append(
            CommunityPost(
                platform="taoguba",
                post_id=short_code,
                url=POST_URL.format(short_code=short_code),
                title=title,
                author_id=str(row.get("user_id") or "").strip() or None,
                published_at=_normalize_time(row.get("last_reply")),
                comment_count=replies,
                view_count=views,
                is_vip_youzi=vip is not None,
                youzi_style=vip["style"] if vip else (),
            )
        )
    return posts


class _TicaiParser(HTMLParser):
    """题材榜 `ticai/ranking`：题材名 + 关联个股。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.themes: list[dict[str, Any]] = []
        self._theme: dict[str, Any] | None = None
        self._name_parts: list[str] = []
        self._in_name = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: (value or "") for key, value in attrs}
        if tag == "div" and "ka" in attributes.get("class", "").split():
            pass
        if tag in {"a", "span"} and attributes.get("href", "").startswith("/quotes/"):
            if self._theme is not None:
                self._theme["stocks"].append(attributes.get("title") or attributes["href"].rsplit("/", 1)[-1])

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or len(text) > 12:
            return
        if self._theme is None:
            self._theme = {"name": text, "stocks": []}
            self._name_parts = [text]
            self.themes.append(self._theme)
        elif self._theme["name"] == text:
            pass


def parse_ticai_ranking(html: str) -> list[dict[str, Any]]:
    """题材排名 → [{name, stocks}]（纯函数；解析不到题材名时返回空表，不猜）。"""
    parser = _TicaiParser()
    parser.feed(html or "")
    return [{"name": item["name"], "stocks": [stock for stock in item["stocks"] if stock]} for item in parser.themes if item["name"]]


def _normalize_time(value: Any, now: datetime | None = None) -> str | None:
    """淘股吧时间字段形态不一：统一成 ISO；认不出就返回 None（不猜时间）。

    「10-16 10:05」这类省略年份的写法不能直接 `strptime`（默认 year=1900）：那样送到后端
    会因距今超过 48 小时被判 `stale-on-discovery` 历史回填，等于把昨天的复盘当古董丢掉。
    所以按「不晚于当前」的年份补齐——若补出来的时刻比现在还晚超过 1 天，说明是去年的贴。
    """
    if value in (None, ""):
        return None
    reference = now or datetime.now(tz=BEIJING)
    if isinstance(value, (int, float)):
        try:
            seconds = float(value)
            if seconds > 1e11:
                seconds /= 1000.0
            return datetime.fromtimestamp(seconds, tz=BEIJING).isoformat()
        except (ValueError, OSError, OverflowError):
            return None
    text = str(value).strip()
    if text.isdigit():
        return _normalize_time(int(text), reference)
    # 省略年份的写法（"10-16 10:05"）不用 strptime：Python 3.12 起它对无年份格式发弃用警告，
    # 3.15 起行为还会变。显式解析再补年份，结果稳定也不会误导后来人。
    yearless = _YEARLESS_TIME.match(text)
    if yearless:
        month, day, hour, minute = (int(part) for part in yearless.groups())
        try:
            return _fill_year(datetime(year=reference.year, month=month, day=day, hour=hour, minute=minute), reference).isoformat()
        except ValueError:
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=BEIJING).isoformat()
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.replace(tzinfo=BEIJING).isoformat() if parsed.tzinfo is None else parsed.isoformat()
    except ValueError:
        return None


def _fill_year(parsed: datetime, reference: datetime) -> datetime:
    """给省略年份的时刻补上不晚于当前的那一年。"""
    if reference.tzinfo is not None:
        parsed = parsed.replace(tzinfo=reference.tzinfo)
    candidate = parsed.replace(year=reference.year)
    if candidate - reference > timedelta(days=1):
        candidate = candidate.replace(year=reference.year - 1)
    return candidate


def fetch_hot(client: HttpClient, page: int = 1, vip_by_id: dict | None = None, vip_by_name: dict | None = None) -> list[CommunityPost]:
    """移动端首页推荐流（站方没有 24h 热帖榜，这是实测最接近的入口）。"""
    try:
        payload = client.get_json(build_url(MZH_URL, {"pageNo": page}), XHR_HEADERS)
    except FetchError as exc:
        client.note_failure(f"taoguba getMZh: {exc}")
        return []
    return parse_getmzh(payload, vip_by_id, vip_by_name)


def fetch_jinghua(client: HttpClient, sort: int = 1, vip_by_id: dict | None = None, vip_by_name: dict | None = None) -> list[CommunityPost]:
    """精华复盘帖：sort=1 按发帖日期，sort=2 按热度（分页后缀不能省）。"""
    try:
        html = client.get(JINGHUA_URL.format(page=1, sort=sort))
    except FetchError as exc:
        client.note_failure(f"taoguba jinghua/{sort}: {exc}")
        return []
    return parse_jinghua(html, vip_by_id, vip_by_name)


def fetch_ticai_ranking(client: HttpClient) -> list[dict[str, Any]]:
    try:
        html = client.get(TICAI_RANKING_URL)
    except FetchError as exc:
        client.note_failure(f"taoguba ticai/ranking: {exc}")
        return []
    return parse_ticai_ranking(html)


def collect(client: HttpClient, vip_path, top: int = 20) -> list[CommunityPost]:
    """采集淘股吧：精华（热度）+ 精华（时间）+ 首页流，游资名录命中即排前面。

    返回扁平帖子列表——淘股吧的复盘帖往往泛题材（不带股票），归到哪只票由 `StockMatcher`
    按股票名/代码/黑话匹配决定，采集器不猜。
    """
    vip_by_id, vip_by_name = load_vip_index(vip_path)
    posts = fetch_jinghua(client, sort=2, vip_by_id=vip_by_id, vip_by_name=vip_by_name)
    posts += fetch_jinghua(client, sort=1, vip_by_id=vip_by_id, vip_by_name=vip_by_name)
    posts += fetch_hot(client, vip_by_id=vip_by_id, vip_by_name=vip_by_name)

    ranked = sorted(posts, key=lambda post: (not post.is_vip_youzi, -post.comment_count, -post.view_count))
    seen: set[str] = set()
    unique: list[CommunityPost] = []
    for post in ranked:
        if post.post_id in seen:
            continue
        seen.add(post.post_id)
        unique.append(post)
        if len(unique) >= top:
            break
    return unique
