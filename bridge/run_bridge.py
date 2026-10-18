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
from .pipeline_loader import StockMatcher, ThemeCatalog, load_focus_pool
from .push_to_aihot import (
    LADDER_ORDER,
    build_push_plan,
    build_snapshot,
    push_items,
    serialize_highlights,
    sync_gold,
    write_snapshot,
)
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


def _leader_stock(members: list):
    """领涨股（LITE-03）：板块内有涨幅的，按 (涨跌幅, 连板, 共振分) 取最高——不能再把
    -3.67% 的票写成「领涨」；全绿时才按 (共振分, 涨跌幅) 取代表股。"""
    if not members:
        return None
    rising = [stock for stock in members if (stock.change_pct or 0) > 0]
    if rising:
        return max(rising, key=lambda stock: (stock.change_pct or 0, stock.board_count, stock.resonance_score))
    return max(members, key=lambda stock: (stock.resonance_score, stock.change_pct or 0))


def _ladder_summary(members: list, leader) -> str:
    """精炼的板块内部结构摘要：「最高4板(冰山冷热)，首板3家，领涨 莱美药业 +19.93%」。

    不再重复拼接板块热股数与涨停数——那由 stockCount / limitUpCount 字段承载（LITE-03）。
    """
    parts: list[str] = []
    top_board = max((stock.board_count for stock in members), default=0)
    if top_board >= 2:
        top_stock = max(members, key=lambda stock: (stock.board_count, stock.resonance_score))
        parts.append(f"最高{top_board}板({top_stock.name})")
    first_boards = sum(1 for stock in members if stock.board_count == 1)
    if first_boards:
        parts.append(f"首板{first_boards}家")
    if leader is not None and (leader.change_pct or 0) > 0:
        parts.append(f"领涨 {leader.name} {leader.change_pct:+.2f}%")
    return "，".join(parts) or "热榜在榜"


def build_theme_ladders(
    pool: list,
    catalog: ThemeCatalog,
    reason_stats: dict[str, int] | None = None,
    summaries: dict | None = None,
    posts_by_code: dict | None = None,
) -> list[dict[str, Any]]:
    """热门板块梯队（LITE-01 建 / LITE-03 精修）：按当日真实热度排序的完整板块内热门股列表。

    热度口径（从强到弱）：
    1. `limit_up_count`：同义子标签的涨停原因统计取 `max()`（低空经济 11 / 飞行汽车 5 不相加），
       再与桶内实际涨停数取大——别名计数不再冒充分散股票的家数；
    2. 板块内上榜热股数（同花顺/东财热榜有名次）；
    3. 板块内涨停家数（涨停池连板股）；
    4. 板块共振分总和。

    板块内热门股按身位分桶（空间板 → 20cm弹性 → 容量中军 → 首板发酵 → 人气热股）、桶内按共振分，
    每只票是完整的 `FocusStock.to_dict()`（带 `limitReason`/`whyHot`/`sealTime`），
    传了 `summaries`/`posts_by_code` 时还带社区情绪与 highlights（LITE-03：梯队股不再只有身份字段，
    未进共振榜的股票从板块入口也能拿到同样的社区详情）。
    """
    groups: dict[str, list] = {}
    for stock in pool:
        for theme in stock.themes:
            groups.setdefault(theme, []).append(stock)

    # reason_stats 的原始原因串按别名归一到标准题材后取最大值（「飞行汽车」并入「低空经济/eVTOL」）
    stat_by_theme: dict[str, int] = {}
    for reason, count in (reason_stats or {}).items():
        name = catalog.normalize_theme(reason)
        if name:
            stat_by_theme[name] = max(stat_by_theme.get(name, 0), count)

    def limit_up_count(name: str, members: list) -> int:
        sealed = sum(1 for stock in members if stock.board_count >= 1)
        return max(stat_by_theme.get(name, 0), sealed)

    def sort_key(item: tuple[str, list]) -> tuple[int, int, int, float, str]:
        name, members = item
        listed = sum(1 for stock in members if stock.hot_rank_ths or stock.hot_rank_dc)
        sealed = sum(1 for stock in members if stock.board_count >= 1)
        resonance = round(sum(stock.resonance_score for stock in members), 1)
        return (-limit_up_count(name, members), -listed, -sealed, -resonance, name)

    ladders: list[dict[str, Any]] = []
    for theme, members in sorted(groups.items(), key=sort_key):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for stock in sorted(members, key=lambda item: -item.resonance_score):
            entry = stock.to_dict()
            summary = (summaries or {}).get(stock.code)
            if summary is not None:
                entry["sentiment"] = summary.to_dict()
            entry["highlights"] = serialize_highlights((posts_by_code or {}).get(stock.code) or [])
            grouped.setdefault(stock.role_label, []).append(entry)
        ordered = {role: grouped.get(role, []) for role in LADDER_ORDER if grouped.get(role)}
        if not ordered:
            continue
        ladders.append(
            {
                "theme": theme,
                "stockCount": len(members),
                "limitUpCount": limit_up_count(theme, members),
                "summary": _ladder_summary(members, _leader_stock(members)),
                "ladders": ordered,
            }
        )
    return ladders


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

    snapshot = build_snapshot(
        pool, summaries, posts_by_platform, config, quality,
        top_n=config.top_resonance_limit, posts_by_code=posts_by_code,
    )
    # LITE-01：热门板块按当日真实热度排序；LITE-03：同义子标签计数取 max、领涨按涨幅口径、
    # 桶内股票带情绪与 highlights（未进共振榜的梯队股从板块入口也拿得到社区详情）
    snapshot.theme_ladders = build_theme_ladders(
        pool, catalog, quality.get("reasonStats") or {}, summaries, posts_by_code
    )
    snapshot_path = write_snapshot(snapshot, SNAPSHOT_PATH)
    print(f"[bridge] 快照已写 {snapshot_path}（梯队 {len(snapshot.theme_ladders)} 组、共振榜 {len(snapshot.top_resonance_stocks)} 只）", file=out)

    if config.sync_gold:
        count = sync_gold()
        print(f"[bridge] 金标集已同步 {GOLD_PATH}（{count} 条）", file=out)

    plan = build_push_plan(pool, summaries, posts_by_platform, top_n=config.top_resonance_limit)

    if config.dump_payloads:
        # 原样落盘，跨语言契约脚本（scripts/verify-bridge-contract.ts）拿它去打真实 ingestItems。
        dump_path = Path(config.dump_payloads)
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_path.write_text(
            json.dumps(
                {source_id: {"sourceId": source_id, "items": [item.to_payload() for item in items]}
                 for source_id, items in plan.items() if items},
                ensure_ascii=False, indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"[bridge] 四轨 payload 已落 {dump_path}（供 scripts/verify-bridge-contract.ts 校验）", file=out)

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
    parser.add_argument("--dump-payloads", default="", metavar="PATH", help="把四轨 push payload 落盘（供跨语言契约校验）")
    parser.add_argument("--focus-limit", type=int, default=50, help="焦点股池上限")
    parser.add_argument("--top", type=int, default=None, help="共振榜条数（默认取 BridgeConfig.top_resonance_limit，LITE-03 起为 50）")
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
        dump_payloads=args.dump_payloads,
        max_stocks=args.max_stocks,
        focus_limit=args.focus_limit,
        top_resonance_limit=args.top,
    )
    if args.base_url:
        config = replace(config, aihot_base_url=args.base_url)
    if args.token:
        config = replace(config, ingest_token=args.token)
    if args.top is not None:
        config = replace(config, top_resonance_limit=args.top)  # 显式指定才覆盖，否则用 config 默认（LITE-03：50）
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main())
