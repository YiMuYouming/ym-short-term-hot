"""双轨推送与雷达快照。

两条轨道，边界由信源参与模式决定（见 `industry/sources.json`）：

- **editorial 轨**（会进入评分/精选）：`external-ym-pipeline` 推结构化战报，
  `external-taoguba-hot` 推游资复盘，`external-xueqiu-hot` 推深度逻辑拆解。全部带 `bodyText`——
  后端据此直接落 `body_status='ok'`，不会再对这些 URL 发一次无效抓取。
- **hot_signal 轨**（只算事件热度与共振，不烧 Token）：`external-eastmoney-guba` 只带标题与摘要，
  不带正文，worker 也不会去分析它。

推送本身分批（后端 `MAX_ITEMS=50`）、带 `Authorization: Bearer`；`--dry-run` 时只打印不发。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .config import (
    GOLD_PATH,
    GOLD_SOURCE_PATH,
    INGEST_BATCH_SIZE,
    SNAPSHOT_PATH,
    SOURCE_GUBA,
    SOURCE_PIPELINE,
    SOURCE_TAOGUBA,
    SOURCE_XUEQIU,
    BridgeConfig,
)
from .schema import (
    CommunityPost,
    FocusStock,
    IngestItem,
    LABEL_CALM,
    RadarSnapshot,
    SentimentSummary,
)

# 梯队分组的展示顺序（与 schema 的 ROLE_* 一致）
LADDER_ORDER = ("空间板", "20cm弹性", "容量中军", "首板发酵", "人气热股")


def _fmt(value: float | None, suffix: str = "%") -> str:
    return "—" if value is None else f"{value:+.2f}{suffix}" if suffix == "%" else f"{value:.1f}{suffix}"


def _post_excerpt(post: CommunityPost, limit: int = 220) -> str:
    text = (post.content or post.title).replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def pipeline_report_item(stock: FocusStock, summary: SentimentSummary) -> IngestItem:
    """一只焦点股 → 一条结构化战报（editorial 轨）。

    正文是固定格式的 Markdown：身位、题材、三端热度、情绪温度条、盖楼流速。
    这类战报有真实数字、结论清楚，模型只需要照实写标题摘要，不需要它去发现事实。
    """
    themes = "、".join(stock.themes) or "未归题材"
    nicknames = "、".join(stock.nicknames) or "无"
    platforms = "、".join(stock.platforms_hit) or "暂无跨端共振"
    body = (
        f"# {stock.name}（{stock.symbol}）{stock.role_label}\n\n"
        f"- 题材归属：{themes}\n"
        f"- 社区黑话：{nicknames}\n"
        f"- 连板高度：{stock.board_count} 板；涨跌幅：{_fmt(stock.change_pct)}；成交额：{_fmt(stock.amount_yi, ' 亿')}\n"
        f"- 跨平台共振分：{stock.resonance_score}（命中：{platforms}）\n"
        f"- 社区情绪：{summary.label}｜一致看多 {summary.bull_ratio:.0f}%｜分歧博弈 {summary.divergence_ratio:.0f}%｜恐慌核按钮 {summary.bear_ratio:.0f}%\n"
        f"- 讨论热度：有效帖 {summary.valid_posts} 条（拦截水贴 {summary.spam_posts} 条），15 分钟盖楼 {summary.posts_15m} 条\n"
        f"- 覆盖平台：{'、'.join(summary.platforms) or '无'}\n"
    )
    return IngestItem(
        source_id=SOURCE_PIPELINE,
        title=f"{stock.name}({stock.code}) {stock.role_label}｜{summary.label}｜共振 {stock.resonance_score}",
        url=f"ymhot://radar/stock/{stock.symbol}",
        author="YM-data-pipeline",
        excerpt=f"{themes}；{stock.role_label}；社区情绪{summary.label}，15 分钟 {summary.posts_15m} 条新帖",
        body_text=body,
        raw={
            "_aihot": {"backfill": False, "baseline": False},
            "ymhot": {
                "kind": "radar_stock",
                "code": stock.code,
                "symbol": stock.symbol,
                "roleLabel": stock.role_label,
                "themes": list(stock.themes),
                "resonanceScore": stock.resonance_score,
                "sentiment": summary.to_dict(),
            },
        },
    )


def community_item(post: CommunityPost, source_id: str, with_body: bool) -> IngestItem | None:
    """一条社区帖 → 一条 ingest 条目。水贴直接丢弃（不占推送额度）。"""
    if post.is_spam or not post.title.strip():
        return None
    title = post.title if len(post.title) <= 90 else post.title[:89] + "…"
    author = post.author_name
    if post.is_vip_youzi:
        author = f"{author or '未知游资'}（实盘名录）"
    return IngestItem(
        source_id=source_id,
        title=title,
        url=post.url,
        author=author,
        excerpt=_post_excerpt(post, 160),
        body_text=_post_excerpt(post, 4000) if with_body else None,
        raw={
            "_aihot": {"backfill": False, "baseline": False},
            "ymhot": {
                "kind": "community_post",
                "platform": post.platform,
                "code": post.code,
                "sentiment": post.sentiment,
                "sentimentScore": post.sentiment_score,
                "isVipYouzi": post.is_vip_youzi,
                "isDeepLogic": post.is_deep_logic,
            },
        },
    )


def build_push_plan(
    stocks: list[FocusStock],
    summaries: dict[str, SentimentSummary],
    posts_by_platform: Mapping[str, list[CommunityPost]],
    top_n: int = 30,
) -> dict[str, list[IngestItem]]:
    """把焦点股与三社区帖子分装成四条轨的推送清单。"""
    plan: dict[str, list[IngestItem]] = {
        SOURCE_PIPELINE: [], SOURCE_TAOGUBA: [], SOURCE_XUEQIU: [], SOURCE_GUBA: [],
    }

    ranked = sorted(stocks, key=lambda stock: -stock.resonance_score)[:top_n]
    for stock in ranked:
        summary = summaries.get(stock.code)
        if summary:
            plan[SOURCE_PIPELINE].append(pipeline_report_item(stock, summary))

    for post in posts_by_platform.get("taoguba", []):
        # 淘股吧只推游资复盘与高热帖：无名小号的高赞闲聊不占 editorial 额度
        if post.is_vip_youzi or post.comment_count >= 30:
            item = community_item(post, SOURCE_TAOGUBA, with_body=True)
            if item:
                plan[SOURCE_TAOGUBA].append(item)

    for post in posts_by_platform.get("xueqiu", []):
        if post.is_deep_logic:
            item = community_item(post, SOURCE_XUEQIU, with_body=True)
            if item:
                plan[SOURCE_XUEQIU].append(item)

    for post in posts_by_platform.get("eastmoney_guba", []):
        # hot_signal 轨：只留标题与摘要，不带正文，worker 不为它做正文抽取
        item = community_item(post, SOURCE_GUBA, with_body=False)
        if item:
            plan[SOURCE_GUBA].append(item)

    return plan


def build_snapshot(
    stocks: list[FocusStock],
    summaries: dict[str, SentimentSummary],
    posts_by_platform: Mapping[str, list[CommunityPost]],
    config: BridgeConfig,
    quality: dict[str, Any],
    top_n: int = 30,
) -> RadarSnapshot:
    """生成 SH-03 直接消费的双视图快照：题材主线梯队 + 跨平台人气共振 Top 30。"""
    from .sentiment_engine import now_beijing

    highlights_by_code: dict[str, list[CommunityPost]] = {}
    for posts in posts_by_platform.values():
        for post in posts:
            if post.is_spam or not post.code:
                continue
            highlights_by_code.setdefault(post.code, []).append(post)

    def highlights(code: str, limit: int = 3) -> list[dict[str, Any]]:
        picked = sorted(highlights_by_code.get(code, []), key=lambda post: -(post.comment_count + post.like_count))[:limit]
        return [
            {
                "platform": post.platform,
                "title": post.title,
                "authorName": post.author_name,
                "isVipYouzi": post.is_vip_youzi,
                "isDeepLogic": post.is_deep_logic,
                "commentCount": post.comment_count,
                "url": post.url,
            }
            for post in picked
        ]

    themes: dict[str, list[FocusStock]] = {}
    for stock in stocks:
        for theme in stock.themes or ("未归题材",):
            themes.setdefault(theme, []).append(stock)

    ladders: list[dict[str, Any]] = []
    # 主线排序看「当日热度」而不是题材代表股数量：SH-03 默认视图第一梯队必须是今天最强的那条主线，
    # 一个 8 只票但全是低分跟风股的题材不该排在共振分最高的主线前面。
    def theme_heat(item: tuple[str, list[FocusStock]]) -> tuple[float, int, str]:
        name, members = item
        return (-round(sum(stock.resonance_score for stock in members), 1), len(members), name)

    for theme, members in sorted(themes.items(), key=theme_heat):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for stock in sorted(members, key=lambda item: -item.resonance_score):
            grouped.setdefault(stock.role_label, []).append(
                {"code": stock.code, "name": stock.name, "symbol": stock.symbol,
                 "boardCount": stock.board_count, "resonanceScore": stock.resonance_score}
            )
        ordered = {role: grouped.get(role, []) for role in LADDER_ORDER if grouped.get(role)}
        if not ordered:
            continue
        ladders.append(
            {
                "theme": theme,
                "summary": f"{theme}：{len(members)} 只焦点股，" + "、".join(
                    f"{role} {len(items)} 只" for role, items in ordered.items()
                ),
                "ladders": ordered,
            }
        )

    top = []
    for stock in sorted(stocks, key=lambda item: -item.resonance_score)[:top_n]:
        summary = summaries.get(stock.code) or SentimentSummary(
            code=stock.code, total_posts=0, valid_posts=0, spam_posts=0,
            bull_count=0, divergence_count=0, bear_count=0,
            bull_ratio=0.0, divergence_ratio=0.0, bear_ratio=0.0, label=LABEL_CALM,
        )
        entry = stock.to_dict()
        entry["sentiment"] = summary.to_dict()
        entry["highlights"] = highlights(stock.code)
        top.append(entry)

    return RadarSnapshot(
        generated_at=now_beijing().isoformat(),
        mode=config.mode,
        data_quality=quality,
        theme_ladders=ladders,
        top_resonance_stocks=top,
        focus_pool_size=len(stocks),
    )


def write_snapshot(snapshot: RadarSnapshot, path: Path | None = None) -> Path:
    """把快照写到 `.data/short-term-radar-snapshot.json`（默认路径由 config 给）。"""
    if path is None:
        path = SNAPSHOT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def sync_gold(source: Path = GOLD_SOURCE_PATH, dest: Path = GOLD_PATH) -> int:
    """把 70 条金标集同步到 `.data/gold.jsonl`，供后续 eval-selection 校准门槛。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def _batches(items: list[IngestItem], size: int = INGEST_BATCH_SIZE) -> Iterable[list[IngestItem]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def push_items(
    source_id: str,
    items: list[IngestItem],
    config: BridgeConfig,
    post: Callable[[str, Mapping[str, str], bytes], tuple[int, str]] | None = None,
) -> dict[str, Any]:
    """分批 POST `/api/ingest/items`。dry-run 只汇报不发；post 可注入（测试用）。"""
    report: dict[str, Any] = {"sourceId": source_id, "planned": len(items), "batches": 0, "sent": 0, "status": "dry_run" if config.dry_run else "pushed"}
    if not items:
        report["status"] = "empty"
        return report
    if config.dry_run and post is None:
        report["batches"] = len(list(_batches(items)))
        return report

    token = config.resolve_token()
    if not token:
        report["status"] = "no_token"
        report["error"] = "缺少 INGEST_TOKEN（只推送需要；离线 dry-run 不需要）"
        return report

    url = f"{config.aihot_base_url.rstrip('/')}/api/ingest/items"
    sender = post or _http_post
    for batch in _batches(items):
        payload = json.dumps({"sourceId": source_id, "items": [item.to_payload() for item in batch]}, ensure_ascii=False).encode("utf-8")
        try:
            status, body = sender(url, {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, payload)
        except Exception as exc:  # noqa: BLE001 - 网络错误按批次失败记账，继续下一批
            report.setdefault("errors", []).append(str(exc)[:200])
            continue
        report["batches"] += 1
        if status >= 200 and status < 300:
            report["sent"] += len(batch)
        else:
            report.setdefault("errors", []).append(f"HTTP {status}: {body[:200]}")
    return report


def _http_post(url: str, headers: Mapping[str, str], payload: bytes) -> tuple[int, str]:
    request = urllib.request.Request(url, data=payload, headers=dict(headers), method="POST")  # noqa: S310 - 地址来自本地配置
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
