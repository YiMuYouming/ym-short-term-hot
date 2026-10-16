"""桥接 CLI：焦点股池 → 三社区采集 → 情绪与共振 → 快照落盘 → 双轨推送。

    python3 -m bridge.run_bridge --offline-fixtures --sync-gold --dry-run   # 离线演练（默认用法）
    python3 -m bridge.run_bridge --live-smoke --max-stocks 3 --dry-run      # 真实抓取冒烟（少量）
    python3 -m bridge.run_bridge --push                                     # 真推送（需 INGEST_TOKEN）

离线模式（`--offline-fixtures`）只读 `bridge/tests/fixtures/`，不触网、不碰付费配额，
所以自动化测试与日常演练跑的是同一条代码路径。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from .collectors import FetchError, HttpClient, build_url
from .collectors import eastmoney_guba, taoguba, xueqiu
from .config import BridgeConfig, GOLD_PATH, SNAPSHOT_PATH, load_json
from .pipeline_loader import StockMatcher, load_focus_pool
from .push_to_aihot import build_push_plan, build_snapshot, push_items, sync_gold, write_snapshot
from .schema import CommunityPost
from .sentiment_engine import SentimentEngine, apply_to_stocks, now_beijing

# 离线报文的 URL 路由表：(URL 特征, 样本文件名)。按顺序匹配，先命中先用。
OFFLINE_ROUTES: tuple[tuple[str, str], ...] = (
    ("Articlelist", "guba_articlelist.json"),
    ("mguba", "guba_mobile.html"),
    ("getMZh", "tgb_getmzh.json"),
    ("jinghua/1-2", "tgb_jinghua_hot.html"),
    ("jinghua/1-1", "tgb_jinghua_time.html"),
    ("ticai/ranking", "tgb_ticai_ranking.html"),
    ("hot_stock/list.json", "xueqiu_hot_stock.json"),
    ("status.json", "xueqiu_status_alpha.json"),   # sort=time 由 URL 里的 sort=time 覆盖
    ("statuses/hot/listV2.json", "xueqiu_hot_statuses.json"),
    ("xueqiu.com/", "xueqiu_home.html"),
)

# sort=time 的样本单独一份（路由表里 status.json 默认 alpha）
TIME_SAMPLE = "xueqiu_status_time.json"


def build_offline_fetcher(fixtures_dir: Path, missing: list[str] | None = None) -> Any:
    """离线 fetcher：按 URL 特征返回 fixture；并按 `code`/`symbol` 过滤成「这只票的帖子」。

    真实接口是按股票返回的，同一个样本文件被多只票共享时若不过滤，一条帖子会被
    重复采集 N 次，情绪条与共振分都会虚高——所以这里让样本行为贴近线上。
    """
    missing = missing if missing is not None else []

    def _filter_by_code(payload: dict, code: str, key: str, field: str) -> dict:
        rows = payload.get(key)
        if not isinstance(rows, list):
            return payload
        payload = dict(payload)
        payload[key] = [row for row in rows if isinstance(row, dict) and str(row.get(field) or "") == code]
        return payload

    def fetch(url: str, headers: Mapping[str, str]) -> str:
        name: str | None = None
        for marker, sample in OFFLINE_ROUTES:
            if marker in url:
                name = sample
                break
        if name == "xueqiu_status_alpha.json" and "sort=time" in url:
            name = TIME_SAMPLE
        if name is None:
            missing.append(url)
            return ""
        path = fixtures_dir / name
        if not path.exists():
            missing.append(f"fixture 缺失：{path}")
            return ""
        text = path.read_text(encoding="utf-8")

        if name == "guba_articlelist.json" and "code=" in url:
            code = url.split("code=", 1)[1].split("&", 1)[0]
            payload = _filter_by_code(json.loads(text), code, "re", "stockbar_code")
            return json.dumps(payload, ensure_ascii=False)
        if name in {"xueqiu_status_alpha.json", TIME_SAMPLE} and "symbol=" in url:
            symbol = url.split("symbol=", 1)[1].split("&", 1)[0]
            code = "".join(ch for ch in symbol if ch.isdigit())[:6]
            payload = json.loads(text)
            data = dict(payload.get("data") or {})
            for key in ("list", "excellent_comments"):
                rows = data.get(key)
                if isinstance(rows, list):
                    data[key] = [row for row in rows if isinstance(row, dict) and str(row.get("code") or "") == code]
            payload["data"] = data
            return json.dumps(payload, ensure_ascii=False)
        return text

    return fetch


def _collect_offline(config: BridgeConfig, stocks: list) -> tuple[dict[str, list[CommunityPost]], list[str], list[dict[str, Any]]]:
    """离线采集：注入 fixture fetcher，HTTP 层一行网络都不走。"""
    from .config import FIXTURES_DIR

    missing: list[str] = []
    client = HttpClient(fetcher=build_offline_fetcher(FIXTURES_DIR, missing))
    posts: dict[str, list[CommunityPost]] = {"eastmoney_guba": [], "taoguba": [], "xueqiu": []}

    for items in eastmoney_guba.collect(client, stocks, top=10).values():
        posts["eastmoney_guba"].extend(items)

    posts["taoguba"].extend(taoguba.collect(client, config.research["tgb_vip"], top=20))

    hot, by_code = xueqiu.collect(client, config.research["xueqiu_authors"], stocks, per_stock=6)
    for items in by_code.values():
        posts["xueqiu"].extend(items)
    return posts, missing, hot


def _collect_live(config: BridgeConfig, stocks: list) -> tuple[dict[str, list[CommunityPost]], list[str], list[dict[str, Any]]]:
    """在线采集：真实 HTTP。任何一站失败都记进 client.failures 并继续。"""
    client = HttpClient(timeout=config.request_timeout, user_agent=config.user_agent)
    posts: dict[str, list[CommunityPost]] = {"eastmoney_guba": [], "taoguba": [], "xueqiu": []}

    for items in eastmoney_guba.collect(client, stocks, top=10).values():
        posts["eastmoney_guba"].extend(items)
    posts["taoguba"].extend(taoguba.collect(client, config.research["tgb_vip"], top=20))
    hot, by_code = xueqiu.collect(client, config.research["xueqiu_authors"], stocks, per_stock=10)
    for items in by_code.values():
        posts["xueqiu"].extend(items)
    return posts, list(client.failures), hot


def with_xq_ranks(stocks: list, hot_rows: list[dict[str, Any]]) -> list:
    """把雪球热股榜名次写回焦点股（共振分要三端名次，缺一端就少算一块）。"""
    rank_by_code = {row["code"]: row.get("rank") for row in hot_rows if row.get("code")}
    return [
        replace(stock, hot_rank_xq=rank_by_code.get(stock.code)) if stock.code in rank_by_code else stock
        for stock in stocks
    ]


def run(config: BridgeConfig, out=sys.stdout) -> int:
    """跑完整一轮，返回进程退出码。"""
    print(f"[bridge] 模式={config.mode} dry_run={config.dry_run} push={config.push}", file=out)

    pool, catalog, quality = load_focus_pool(config)
    if not pool:
        print("[bridge] 焦点股池为空：题材词典也没有代表股？检查 docs/aihot_research/dict/themes.json", file=out)
        return 2
    print(f"[bridge] 焦点股池 {len(pool)} 只（题材词典 {len(catalog.themes)} 个题材）", file=out)
    for warning in quality.get("warnings", []):
        print(f"[bridge] 管道提示：{warning}", file=out)

    if config.live_smoke and config.max_stocks:
        pool = pool[: config.max_stocks]

    if config.offline_fixtures:
        posts_by_platform, missing, hot_rows = _collect_offline(config, pool)
        quality["offlineMissing"] = missing[:10]
        if missing:
            print(f"[bridge] 离线样本未命中 {len(missing)} 个 URL（前几个：{missing[:3]}）", file=out)
    else:
        posts_by_platform, failures, hot_rows = _collect_live(config, pool)
        quality["httpFailures"] = failures[:10]
        for failure in failures[:5]:
            print(f"[bridge] 采集失败：{failure}", file=out)

    pool = with_xq_ranks(pool, hot_rows)
    matcher = StockMatcher(pool)
    posts_by_code: dict[str, list[CommunityPost]] = {}
    for posts in posts_by_platform.values():
        for code, items in matcher.group(posts).items():
            posts_by_code.setdefault(code, []).extend(items)

    engine = SentimentEngine.load(config.research["sentiment"])
    pool, summaries = apply_to_stocks(pool, posts_by_code, engine, now_beijing())
    scored = sum(summary.total_posts for summary in summaries.values())
    print(f"[bridge] 归类帖子 {scored} 条，覆盖 {len(posts_by_code)} 只票；词典情绪词 "
          f"{sum(len(v) for v in engine.entries.values())} 条、水贴正则 {len(engine.spam_rules)} 条", file=out)

    snapshot = build_snapshot(pool, summaries, posts_by_platform, config, quality, top_n=config.top_resonance_limit)
    snapshot_path = write_snapshot(snapshot, SNAPSHOT_PATH)
    print(f"[bridge] 快照已写 {snapshot_path}（梯队 {len(snapshot.theme_ladders)} 组、共振榜 {len(snapshot.top_resonance_stocks)} 只）", file=out)

    if config.sync_gold:
        count = sync_gold()
        print(f"[bridge] 金标集已同步 {GOLD_PATH}（{count} 条）", file=out)

    plan = build_push_plan(pool, summaries, posts_by_platform, top_n=config.top_resonance_limit)
    reports: dict[str, Any] = {}
    for source_id, items in plan.items():
        if not items:
            continue
        reports[source_id] = push_items(source_id, items, config)
    quality["push"] = reports
    snapshot.data_quality = quality
    write_snapshot(snapshot, snapshot_path)  # 把推送回执补进快照，便于复盘时对账

    for source_id, report in reports.items():
        print(f"[bridge] 推送 {source_id}：计划 {report['planned']} 条 / 批次 {report.get('batches', 0)} / "
              f"已发 {report.get('sent', 0)} / 状态 {report['status']}", file=out)

    if not snapshot.theme_ladders or not snapshot.top_resonance_stocks:
        print("[bridge] 快照为空梯队或空共振榜：离线样本或管道数据缺料", file=out)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bridge.run_bridge", description="YM-HOT 数据管道桥接")
    parser.add_argument("--offline-fixtures", action="store_true", help="只读 bridge/tests/fixtures，不触网")
    parser.add_argument("--live-smoke", action="store_true", help="真实抓取冒烟（配合 --max-stocks 少量）")
    parser.add_argument("--max-stocks", type=int, default=0, help="只处理前 N 只（0 = 不限）")
    parser.add_argument("--push", action="store_true", help="真推送（默认只 dry-run）")
    parser.add_argument("--dry-run", action="store_true", help="显式声明不推送（默认行为）")
    parser.add_argument("--sync-gold", action="store_true", help="同步 docs/aihot_research/gold 到 .data/gold.jsonl")
    parser.add_argument("--focus-limit", type=int, default=50, help="焦点股池上限")
    parser.add_argument("--top", type=int, default=30, help="共振榜条数")
    parser.add_argument("--base-url", default=None, help="AIHOT 实例地址（默认 http://127.0.0.1:3088）")
    parser.add_argument("--token", default="", help="推送令牌（默认取环境 INGEST_TOKEN）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = BridgeConfig(
        offline_fixtures=args.offline_fixtures,
        dry_run=not args.push,
        push=args.push,
        sync_gold=args.sync_gold,
        live_smoke=args.live_smoke,
        max_stocks=args.max_stocks,
        focus_limit=args.focus_limit,
        top_resonance_limit=args.top,
    )
    if args.base_url:
        config = replace(config, aihot_base_url=args.base_url)
    if args.token:
        config = replace(config, ingest_token=args.token)
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
