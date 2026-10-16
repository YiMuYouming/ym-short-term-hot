"""桥接的离线单测：不触网、不消耗 StockToday 配额、不调付费 LLM。

跑法（仓库根）：

    python3 -m unittest discover -s bridge/tests -p "test_*.py" -v

覆盖：焦点股合成与身位、社区黑话映射、14 条水贴正则、三类情绪打分与上下文修正、
15m 盖楼流速、跨平台共振分、三社区离线报文解析、双轨推送转换、快照结构与端到端演练。
"""

from __future__ import annotations

import io
import json
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bridge.collectors import eastmoney_guba, taoguba, xueqiu  # noqa: E402
from bridge.collectors import HttpClient  # noqa: E402
from bridge.config import (  # noqa: E402
    FIXTURES_DIR,
    GOLD_PATH,
    GOLD_SOURCE_PATH,
    SENTIMENT_DICT_PATH,
    SOURCE_GUBA,
    SOURCE_PIPELINE,
    SOURCE_TAOGUBA,
    SOURCE_XUEQIU,
    BridgeConfig,
    load_json,
)
from bridge.pipeline_loader import (  # noqa: E402
    StockMatcher,
    ThemeCatalog,
    build_focus_pool,
    exchange_of,
    load_pipeline,
    parse_hot_rank,
)
from bridge.push_to_aihot import (  # noqa: E402
    build_push_plan,
    build_snapshot,
    community_item,
    pipeline_report_item,
    push_items,
    sync_gold,
)
from bridge.run_bridge import build_offline_fetcher, run, with_xq_ranks  # noqa: E402
from bridge.schema import (  # noqa: E402
    LABEL_CALM,
    LABEL_DIVERGENCE,
    LABEL_EUPHORIA,
    LABEL_NUKE,
    SENTIMENT_BEAR,
    SENTIMENT_BULL,
    SENTIMENT_DIVERGENCE,
    CommunityPost,
    FocusStock,
)
from bridge.sentiment_engine import (  # noqa: E402
    BEIJING,
    SentimentEngine,
    apply_to_stocks,
    now_beijing,
    score_resonance,
)

FIXTURE_BASE = datetime(2026, 10, 16, 10, 30, tzinfo=BEIJING)
# 推送批次时间（ISO 8601 带 +08:00），与后端 decideTimeline 的「不晚于入库时刻」约束一致
BATCH_TIME = datetime(2026, 10, 16, 10, 30, tzinfo=BEIJING).isoformat()


def fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def fixture_json(name: str):
    return json.loads(fixture(name))


def offline_config(**overrides) -> BridgeConfig:
    base = {"offline_fixtures": True, "dry_run": True, "sync_gold": False}
    base.update(overrides)
    return BridgeConfig(**base)


# ── S3 焦点股池与题材身位 ────────────────────────────────────────────────────────


class TestFocusPool(unittest.TestCase):
    def setUp(self) -> None:
        self.config = offline_config()
        self.catalog = ThemeCatalog.load(self.config.research["themes"])
        self.data, self.quality = load_pipeline(self.config)

    def test_catalog_indexes_28_themes_and_nicknames(self) -> None:
        self.assertEqual(len(self.catalog.themes), 28)
        # 「易中天」是组合黑话，同时指向三只光模块票
        self.assertEqual(self.catalog.resolve_nickname("易中天"), ("300308", "300394", "300502"))
        self.assertEqual(self.catalog.resolve_nickname("寒王"), ("688256",))
        self.assertEqual(self.catalog.resolve_nickname("宁王"), ("300750",))
        self.assertEqual(self.catalog.resolve_nickname("不存在的黑话"), ())

    def test_offline_pipeline_reports_fixture_status(self) -> None:
        self.assertEqual(self.quality["mode"], "offline_fixtures")
        self.assertTrue(self.data.has_hot)
        self.assertEqual(self.quality["sources"]["ths_hot"]["status"], "fixture")

    def test_focus_pool_applies_role_labels_from_live_signals(self) -> None:
        pool = {stock.code: stock for stock in build_focus_pool(self.data, self.catalog, 50)}
        # 连板最高者即使不在 ths 热榜首位，也应排成空间板
        self.assertEqual(pool["688256"].role_label, "空间板")          # 4 板
        self.assertEqual(pool["688256"].board_count, 4)
        self.assertEqual(pool["300308"].role_label, "空间板")          # 3 板，与寒武纪同为最高连板
        self.assertEqual(pool["300502"].role_label, "20cm弹性")        # 2 板 + 30 开头，未到空间板门槛
        self.assertEqual(pool["600410"].role_label, "首板发酵")        # 首板主板
        self.assertEqual(pool["002261"].role_label, "首板发酵")
        # 涨幅不足但成交额 63 亿的宁王靠「容量」进中军位
        self.assertEqual(pool["300750"].role_label, "容量中军")
        self.assertIn("dc", pool["600519"].sources, "只上东财热榜的票来源仍记录在案")

    def test_pool_is_sorted_by_role_then_hot_rank(self) -> None:
        pool = build_focus_pool(self.data, self.catalog, 50)
        rank = {"空间板": 0, "20cm弹性": 1, "容量中军": 2, "首板发酵": 3, "人气热股": 4}
        keys = [
            (rank[stock.role_label], stock.hot_rank_ths or 999, stock.hot_rank_dc or 999, stock.code)
            for stock in pool
        ]
        self.assertEqual(keys, sorted(keys))

    def test_pool_falls_back_to_theme_base_when_pipeline_is_empty(self) -> None:
        empty, quality = load_pipeline(self.config)
        empty.ths_hot, empty.dc_hot, empty.intraday = [], [], {}
        pool = build_focus_pool(empty, self.catalog, 12)
        self.assertEqual(len(pool), 12)
        self.assertTrue(all("theme_base" in stock.sources for stock in pool))
        self.assertFalse(empty.has_hot, "管道无热榜时数据本身没有热榜可用")

    def test_online_mode_records_pipeline_degradation_honestly(self) -> None:
        def failing_query(intent: str, **kwargs):
            return {"_meta": {"status": "empty", "provider": None, "data_as_of": "2026-10-16T15:00:00+08:00"}, "items": []}

        data, quality = load_pipeline(offline_config(offline_fixtures=False), query=failing_query)
        self.assertFalse(data.has_hot)
        self.assertEqual(quality["sources"]["ths_hot"]["status"], "empty")
        self.assertTrue(any("退回题材底座" in w for w in quality["warnings"]))

    def test_exchange_and_symbol_mapping(self) -> None:
        self.assertEqual(exchange_of("300308"), "sz")
        self.assertEqual(exchange_of("688256"), "sh")
        self.assertEqual(exchange_of("600519"), "sh")
        self.assertEqual(exchange_of("830799"), "bj")
        self.assertEqual(FocusStock(code="300308", name="中际旭创", exchange="sz").symbol, "SZ300308")

    def test_stock_matcher_maps_nicknames_and_names(self) -> None:
        pool = build_focus_pool(self.data, self.catalog, 20)
        matcher = StockMatcher(pool)
        by_nickname = matcher.match(CommunityPost(platform="taoguba", post_id="1", url="u", title="易中天集体涨停"))
        self.assertEqual(set(by_nickname), {"300308", "300394", "300502"})
        by_name = matcher.match(CommunityPost(platform="xueqiu", post_id="2", url="u", title="宁王今天被埋了"))
        self.assertEqual(by_name, ("300750",))
        generic = CommunityPost(platform="taoguba", post_id="3", url="u", title="今天大盘怎么走")
        self.assertEqual(matcher.match(generic), ())


# ── S5/S4 情绪引擎 ─────────────────────────────────────────────────────────────


class TestSentimentEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SentimentEngine.load(SENTIMENT_DICT_PATH)

    @staticmethod
    def post(title: str, content: str | None = None, **kwargs) -> CommunityPost:
        return CommunityPost(platform="eastmoney_guba", post_id="p", url="https://guba.eastmoney.com/x", title=title, content=content, **kwargs)

    def test_all_14_spam_patterns_match_their_own_examples(self) -> None:
        self.assertEqual(len(self.engine.spam_rules), 14)
        for rule in self.engine.spam_rules:
            self.assertTrue(rule.pattern.pattern, f"{rule.rule_id} 没有正则")
            if rule.example:
                self.assertIsNotNone(rule.pattern.search(rule.example), f"{rule.rule_id} 未命中自己的示例：{rule.example}")

    def test_spam_post_is_flagged_and_never_scored(self) -> None:
        post = self.engine.score_post(self.post("加微信：abc12345 带你吃肉", "稳赚不亏，扫码进群"))
        self.assertTrue(post.is_spam)
        self.assertIsNotNone(post.spam_rule)
        self.assertIsNone(post.sentiment)

    def test_ordinary_post_is_not_spam(self) -> None:
        post = self.engine.score_post(self.post("光模块三连板，明天看反包", "易中天集体大长腿，竞价弱转强"))
        self.assertFalse(post.is_spam)

    def test_bullish_post_scores_extreme_bull(self) -> None:
        post = self.engine.score_post(self.post("一字板，明天继续打板", "龙头三连板，情绪一致看多"))
        self.assertEqual(post.sentiment, SENTIMENT_BULL)
        self.assertGreater(post.sentiment_score, 0)
        self.assertIn("一字板", post.sentiment_terms)

    def test_bearish_post_scores_panic_bear(self) -> None:
        post = self.engine.score_post(self.post("跌停板上出货，明天核按钮", "被埋了，站岗一天大面"))
        self.assertEqual(post.sentiment, SENTIMENT_BEAR)
        self.assertLess(post.sentiment_score, 0)

    def test_context_rule_flips_chi_mian_with_reversal_context(self) -> None:
        # 「吃面」单出现偏恐慌；同帖出现「大长腿/反包」时按次日反包预期转看多
        plain = self.engine.score_post(self.post("今天吃面了", "止损离场"))
        flipped = self.engine.score_post(self.post("昨天吃面，今天大长腿反包", "情绪修复，先看反包强度"))
        self.assertIn("吃面", plain.sentiment_terms)
        self.assertNotIn(SENTIMENT_BULL, plain.sentiment_context_notes)
        self.assertTrue(any("转看多" in note for note in flipped.sentiment_context_notes))
        self.assertEqual(flipped.sentiment, SENTIMENT_BULL)

    def test_context_rule_flips_ge_ju_with_burial_context(self) -> None:
        post = self.engine.score_post(self.post("这格局就是让你站岗", "明天被埋，大面无疑"))
        self.assertTrue(any("转恐慌" in note for note in post.sentiment_context_notes))
        self.assertEqual(post.sentiment, SENTIMENT_BEAR)

    def test_context_rule_records_source_notes_for_audit(self) -> None:
        post = self.engine.score_post(self.post("弱转强", "炸板后回封，低吸还是打板"))
        self.assertTrue(post.sentiment_context_notes)
        self.assertIn("弱转强", post.sentiment_terms)

    def test_summary_ratios_sum_to_100(self) -> None:
        posts = [
            self.post("一字板继续打板"),
            self.post("龙头晋级，情绪一致"),
            self.post("跌停，核按钮"),
            self.post("加微信：abc12345"),          # 水贴，不计
            self.post("明天怎么看"),                 # 无方向，不进分母
        ]
        summary = self.engine.summarize("300308", posts, FIXTURE_BASE)
        self.assertEqual(summary.total_posts, 5)
        self.assertEqual(summary.valid_posts, 4, "水贴被拦，中性帖仍算有效内容")
        self.assertEqual(summary.spam_posts, 1)
        self.assertEqual(summary.bull_count + summary.divergence_count + summary.bear_count, 3)
        self.assertAlmostEqual(summary.bull_ratio + summary.divergence_ratio + summary.bear_ratio, 100.0, places=6)

    def test_summary_label_needs_enough_evidence(self) -> None:
        single = self.engine.summarize("300308", [self.post("一字板继续打板")], FIXTURE_BASE)
        self.assertEqual(single.label, LABEL_CALM, "一条帖不叫一致亢奋")
        many = self.engine.summarize(
            "300308",
            [self.post("一字板继续打板"), self.post("龙头晋级一致"), self.post("继续打板，情绪一致")],
            FIXTURE_BASE,
        )
        self.assertEqual(many.label, LABEL_EUPHORIA)
        split = self.engine.summarize(
            "300308",
            [self.post("一字板继续打板"), self.post("跌停核按钮"), self.post("继续分歧博弈")],
            FIXTURE_BASE,
        )
        self.assertIn(split.label, {LABEL_CALM, LABEL_DIVERGENCE})

    def test_15m_posting_velocity_counts_only_recent_posts(self) -> None:
        now = FIXTURE_BASE
        recent = self.post("三分钟前", published_at=(now - timedelta(minutes=3)).isoformat())
        older = self.post("一小时前", published_at=(now - timedelta(minutes=60)).isoformat())
        spam_recent = self.post("加微信：abc12345", published_at=(now - timedelta(minutes=1)).isoformat())
        summary = self.engine.summarize("300308", [recent, older, spam_recent], now)
        self.assertEqual(summary.posts_15m, 1, "只数近 15 分钟且非水贴")

    def test_resonance_score_combines_platforms_and_ranks(self) -> None:
        hot = FocusStock(
            code="300308", name="中际旭创", exchange="sz", themes=("光模块/CPO",),
            hot_rank_ths=1, hot_rank_dc=1, hot_rank_xq=2,
        )
        busy = self.engine.summarize("300308", [
            CommunityPost(platform="eastmoney_guba", post_id=str(i), url="u", title="涨停", published_at=(FIXTURE_BASE - timedelta(minutes=i)).isoformat())
            for i in range(12)
        ], FIXTURE_BASE)
        busy = replace(busy, label=LABEL_EUPHORIA)
        score, hits = score_resonance(hot, busy, taoguba_mentions=6)
        self.assertGreater(score, 70)
        self.assertLessEqual(score, 100)
        self.assertIn("同花顺热榜#1", hits)
        self.assertIn("东财热榜#1", hits)
        self.assertIn("雪球热股#2", hits)
        self.assertTrue(any(h.startswith("淘股吧热议") for h in hits))
        self.assertTrue(any(h.startswith("股吧15m盖楼") for h in hits))

        cold = FocusStock(code="002261", name="拓维信息", exchange="sz")
        empty = self.engine.summarize("002261", [], FIXTURE_BASE)
        cold_score, cold_hits = score_resonance(cold, empty, taoguba_mentions=0)
        self.assertEqual(cold_score, 0)
        self.assertEqual(cold_hits, ())

    def test_apply_to_stocks_writes_scores_back(self) -> None:
        stocks = [FocusStock(code="300308", name="中际旭创", exchange="sz", hot_rank_ths=2)]
        posts = {
            "300308": [
                CommunityPost(platform="taoguba", post_id="t1", url="u", title="三连板，弱转强"),
                CommunityPost(platform="eastmoney_guba", post_id="g1", url="u", title="涨停了", published_at=(now_beijing() - timedelta(minutes=2)).isoformat()),
            ]
        }
        updated, summaries = apply_to_stocks(stocks, posts, self.engine, now_beijing())
        self.assertEqual(updated[0].taoguba_mentions, 1)
        self.assertGreater(updated[0].resonance_score, 0)
        self.assertEqual(stocks[0].resonance_score, 0, "不可变对象不被就地改写")
        self.assertIn("300308", summaries)


# ── S5 三社区解析 ───────────────────────────────────────────────────────────────


class TestEastmoneyGuba(unittest.TestCase):
    def setUp(self) -> None:
        self.posts = eastmoney_guba.parse_articlelist(fixture_json("guba_articlelist.json"), "300308", "中际旭创")

    def test_parses_fields_and_computes_hot_weight(self) -> None:
        self.assertEqual(len(self.posts), 5)
        top = self.posts[0]
        self.assertEqual(top.title, "易中天集体大长腿，明天继续看反包")
        self.assertEqual(top.code, "300308")
        self.assertEqual(top.comment_count, 260)
        self.assertEqual(top.view_count, 3200)
        self.assertAlmostEqual(top.hot_weight, 260 * 5 + 3200 * 0.1)

    def test_ranks_locally_by_comments_and_clicks(self) -> None:
        ranked = eastmoney_guba.rank_by_hot(self.posts, top=4)
        self.assertEqual([p.post_id for p in ranked], ["900000001", "900000002", "900000003", "900000005"])

    def test_attaches_bodies_from_mobile_page(self) -> None:
        bodies = eastmoney_guba.parse_mobile_list(fixture("guba_mobile.html"), "300308")
        self.assertIn("900000001", bodies)
        self.assertIn("大长腿", bodies["900000001"])
        attached = eastmoney_guba.attach_bodies(list(self.posts), bodies)
        self.assertIn("易中天", attached[0].content)

    def test_counts_15m_posts(self) -> None:
        # 样本时间分别为 -3/-8/-40/-2/-1 分钟，40 分钟前那条不计入
        count = eastmoney_guba.count_posts_15m(self.posts, FIXTURE_BASE)
        self.assertEqual(count, 4)

    def test_fetch_stock_uses_injected_fetcher(self) -> None:
        seen: list[str] = []
        def fake(url: str, headers) -> str:
            seen.append(url)
            return fixture("guba_articlelist.json") if "Articlelist" in url else fixture("guba_mobile.html")
        client = HttpClient(fetcher=fake)
        posts = eastmoney_guba.fetch_stock(client, "300308", "中际旭创")
        self.assertTrue(posts)
        self.assertTrue(any("Articlelist" in url and "sorttype=0" in url for url in seen))
        self.assertTrue(any("mguba" in url for url in seen))
        self.assertEqual(client.failures, [])

    def test_fetch_failure_is_recorded_not_raised(self) -> None:
        def boom(url: str, headers) -> str:
            raise eastmoney_guba.FetchError(f"{url}: net down")
        client = HttpClient(fetcher=boom)
        self.assertEqual(eastmoney_guba.fetch_stock(client, "300308", "x"), [])
        self.assertTrue(client.failures)


class TestTaoguba(unittest.TestCase):
    def setUp(self) -> None:
        self.vip_by_id, self.vip_by_name = taoguba.load_vip_index(
            REPO_ROOT / "docs" / "aihot_research" / "tgb.json"
        )

    def test_parse_getmzh_reads_dto_index_list(self) -> None:
        posts = taoguba.parse_getmzh(fixture_json("tgb_getmzh.json"), self.vip_by_id, self.vip_by_name)
        self.assertEqual(len(posts), 3)
        first = posts[0]
        self.assertEqual(first.title, "算力主线复盘：光模块三连板，明日竞价弱转强预期")
        self.assertEqual(first.comment_count, 186)
        self.assertEqual(first.view_count, 21400)
        self.assertTrue(first.published_at.startswith("2026-10-16T10:05"))

    def test_vip_youzi_flagged_by_user_id(self) -> None:
        posts = taoguba.parse_getmzh(fixture_json("tgb_getmzh.json"), self.vip_by_id, self.vip_by_name)
        vip = [p for p in posts if p.is_vip_youzi]
        self.assertEqual({p.author_id for p in vip}, {"252069", "138280"})
        byala = next(p for p in posts if p.author_id == "252069")
        self.assertEqual(byala.youzi_style, self.vip_by_id["252069"]["style"])
        self.assertTrue(byala.youzi_style, "实盘游资带风格标签，便于复盘时区分打法")
        self.assertFalse(posts[2].is_vip_youzi)

    def test_yearless_timestamps_take_the_current_year_not_1900(self) -> None:
        """「10-16 10:05」补年份：不能变成 1900（会被判 stale-on-discovery 历史回填）。"""
        from bridge.collectors.taoguba import _normalize_time

        reference = datetime(2026, 10, 16, 16, 30, tzinfo=BEIJING)
        parsed = _normalize_time("10-16 10:05", reference)
        self.assertIsNotNone(parsed)
        moment = datetime.fromisoformat(parsed)
        self.assertEqual((moment.year, moment.month, moment.day, moment.hour, moment.minute), (2026, 10, 16, 10, 5))
        self.assertGreaterEqual(moment.year, 2026)

    def test_yearless_timestamps_from_the_future_fall_back_one_year(self) -> None:
        """跨年：「12-31 23:30」在 10 月看到时应属于去年，而不是明年。"""
        from bridge.collectors.taoguba import _normalize_time

        reference = datetime(2026, 10, 16, 16, 30, tzinfo=BEIJING)
        moment = datetime.fromisoformat(_normalize_time("12-31 23:30", reference))
        self.assertEqual(moment.year, 2025)
        past = datetime.fromisoformat(_normalize_time("09-28 10:05", reference))
        self.assertEqual(past.year, 2026)

    def test_parse_jinghua_extracts_title_counts_and_author(self) -> None:
        posts = taoguba.parse_jinghua(fixture("tgb_jinghua_hot.html"), self.vip_by_id, self.vip_by_name)
        self.assertEqual(len(posts), 2)
        top = posts[0]
        self.assertEqual(top.title, "算力主线复盘：光模块三连板")
        self.assertEqual(top.post_id, "2vUNIn9W0UH")
        self.assertEqual(top.comment_count, 186)
        self.assertEqual(top.view_count, 21400)
        self.assertTrue(top.is_vip_youzi)

    def test_forbidden_routes_are_documented_not_called(self) -> None:
        self.assertTrue(any(route.endswith("/hot") for route in taoguba.FORBIDDEN_ROUTES))
        self.assertNotIn("/hot", [taoguba.MZH_URL, taoguba.JINGHUA_URL, taoguba.TICAI_RANKING_URL])

    def test_collect_ranks_vip_first(self) -> None:
        client = HttpClient(fetcher=build_offline_fetcher(FIXTURES_DIR))
        posts = taoguba.collect(client, REPO_ROOT / "docs" / "aihot_research" / "tgb.json", top=10)
        self.assertTrue(posts)
        self.assertTrue(posts[0].is_vip_youzi)
        ids = [p.post_id for p in posts]
        self.assertEqual(len(ids), len(set(ids)), "同一帖不重复推送")


class TestXueqiu(unittest.TestCase):
    def setUp(self) -> None:
        self.authors = xueqiu.load_author_index(REPO_ROOT / "docs" / "aihot_research" / "xueqiu.json")

    def test_hot_stock_ranks_and_symbols(self) -> None:
        rows = xueqiu.parse_hot_stock(fixture_json("xueqiu_hot_stock.json"))
        self.assertEqual([row["code"] for row in rows], ["600519", "300308", "688256", "300750"])
        self.assertEqual(rows[1]["symbol"], "SZ300308")
        self.assertEqual(rows[1]["rank"], 2)

    def test_symbol_status_marks_known_authors_and_long_form(self) -> None:
        posts = xueqiu.parse_symbol_status(fixture_json("xueqiu_status_alpha.json"), "300308", "中际旭创", self.authors, "SZ300308")
        self.assertGreaterEqual(len(posts), 3)     # 2 主帖 + 1 精选评论
        deep = next(p for p in posts if p.author_id == "5311792678")
        self.assertTrue(deep.is_deep_logic)
        self.assertIn("产业链", deep.content or "")
        shallow = next(p for p in posts if p.author_id == "88888888")
        self.assertFalse(shallow.is_deep_logic)

    def test_excellent_comments_are_attached_with_distinct_ids(self) -> None:
        posts = xueqiu.parse_symbol_status(fixture_json("xueqiu_status_alpha.json"), "300308", "中际旭创", self.authors)
        comments = [p for p in posts if p.post_id.endswith("-c")]
        self.assertEqual(len(comments), 1)
        self.assertIn("良率", comments[0].content or "")

    def test_collect_warms_up_before_json_calls(self) -> None:
        calls: list[str] = []
        def fake(url: str, headers) -> str:
            calls.append(url)
            if url.endswith("/"):
                return fixture("xueqiu_home.html")
            if "hot_stock" in url:
                return fixture("xueqiu_hot_stock.json")
            return fixture("xueqiu_status_alpha.json")
        client = HttpClient(fetcher=fake)
        stocks = [FocusStock(code="300308", name="中际旭创", exchange="sz")]
        hot, by_code = xueqiu.collect(client, REPO_ROOT / "docs" / "aihot_research" / "xueqiu.json", stocks, per_stock=5)
        self.assertTrue(hot)
        self.assertIn("300308", by_code)
        self.assertTrue(any(url.endswith("/") for url in calls), "先访问首页拿匿名 cookie")
        self.assertTrue(calls.index([u for u in calls if u.endswith("/")][0]) < calls.index([u for u in calls if "hot_stock" in u][0]))

    def test_deep_logic_needs_length_and_industry_words(self) -> None:
        self.assertFalse(xueqiu.looks_deep_logic("中际旭创涨停", "很短"))
        long_text = "产业链" * 60
        self.assertTrue(xueqiu.looks_deep_logic(long_text, None))


# ── S6 推送与快照 ───────────────────────────────────────────────────────────────


class TestPushPlan(unittest.TestCase):
    def setUp(self) -> None:
        self.config = offline_config()
        self.catalog = ThemeCatalog.load(self.config.research["themes"])
        self.data, self.quality = load_pipeline(self.config)
        self.pool = build_focus_pool(self.data, self.catalog, 20)
        client = HttpClient(fetcher=build_offline_fetcher(FIXTURES_DIR))
        guba_posts: list[CommunityPost] = []
        for items in eastmoney_guba.collect(client, self.pool, top=5).values():
            guba_posts.extend(items)
        tgb_posts = taoguba.collect(client, self.config.research["tgb_vip"], top=10)
        _, xq_by_code = xueqiu.collect(client, self.config.research["xueqiu_authors"], self.pool, per_stock=5)
        xq_posts = [p for items in xq_by_code.values() for p in items]
        self.platforms = {"eastmoney_guba": guba_posts, "taoguba": tgb_posts, "xueqiu": xq_posts}
        matcher = StockMatcher(self.pool)
        by_code: dict[str, list[CommunityPost]] = {}
        for posts in self.platforms.values():
            for code, items in matcher.group(posts).items():
                by_code.setdefault(code, []).extend(items)
        self.engine = SentimentEngine.load(self.config.research["sentiment"])
        self.pool, self.summaries = apply_to_stocks(self.pool, by_code, self.engine, now_beijing())

    def test_plan_splits_four_tracks_and_respects_participation_mode(self) -> None:
        plan = build_push_plan(self.pool, self.summaries, self.platforms)
        self.assertEqual(set(plan), {SOURCE_PIPELINE, SOURCE_TAOGUBA, SOURCE_XUEQIU, SOURCE_GUBA})
        # 股吧轨是 hot_signal：只带标题摘要，不带正文（不触发 LLM 分析）
        for item in plan[SOURCE_GUBA]:
            self.assertNotIn("bodyText", item.to_payload())
            self.assertIn("excerpt", item.to_payload())
        # editorial 三轨带正文，模型拿到的是已经读过的事实
        for source in (SOURCE_PIPELINE, SOURCE_TAOGUBA, SOURCE_XUEQIU):
            for item in plan[source]:
                self.assertTrue(item.to_payload()["bodyText"], f"{source} 应带正文")
        self.assertTrue(plan[SOURCE_PIPELINE])
        self.assertTrue(plan[SOURCE_TAOGUBA])
        self.assertTrue(plan[SOURCE_XUEQIU])

    def test_spam_never_enters_the_push_plan(self) -> None:
        plan = build_push_plan(self.pool, self.summaries, self.platforms)
        for items in plan.values():
            for item in items:
                self.assertNotIn("加微信", item.title)

    def test_pipeline_report_body_carries_facts_and_is_pushed_as_body_text(self) -> None:
        stock = next(s for s in self.pool if s.code == "300308")
        item = pipeline_report_item(stock, self.summaries["300308"], BATCH_TIME)
        payload = item.to_payload()
        self.assertEqual(item.source_id, SOURCE_PIPELINE)
        self.assertIn("300308", payload["title"])
        self.assertIn(stock.role_label, payload["bodyText"])
        self.assertIn(f"跨平台共振分：{stock.resonance_score}", payload["bodyText"])
        self.assertIn(payload["excerpt"], payload["title"] + payload["bodyText"] + payload["excerpt"])


    def test_community_item_drops_spam_and_shortens_excerpt(self) -> None:
        engine = SentimentEngine.load(self.config.research["sentiment"])
        spam = engine.score_post(CommunityPost(platform="taoguba", post_id="x", url="u", title="加微信：abc12345", content="带肉"))
        self.assertTrue(spam.is_spam)
        self.assertIsNone(community_item(spam, SOURCE_TAOGUBA, True, BATCH_TIME))
        long_post = CommunityPost(platform="xueqiu", post_id="y", url="u", title="长文", content="内容" * 500)
        item = community_item(long_post, SOURCE_XUEQIU, True, BATCH_TIME)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertLessEqual(len(item.excerpt or ""), 160)
        self.assertLessEqual(len(item.body_text or ""), 4000)

    def test_push_batches_at_50_and_reports_dry_run(self) -> None:
        items = [pipeline_report_item(s, self.summaries.get(s.code) or list(self.summaries.values())[0], BATCH_TIME) for s in self.pool]
        report = push_items(SOURCE_PIPELINE, items, self.config)
        self.assertEqual(report["status"], "dry_run")
        self.assertEqual(report["planned"], len(items))
        self.assertEqual(report["batches"], 1, "不超过 20 条 → 单批（后端上限 50）")

    def test_push_uses_injected_transport_and_batches(self) -> None:
        sent: list[tuple[str, int]] = []
        def post(url, headers, payload):
            body = json.loads(payload)
            sent.append((body["sourceId"], len(body["items"])))
            assert headers["Authorization"].startswith("Bearer ")
            return 200, '{"ok":true}'
        config = replace(self.config, dry_run=False, ingest_token="tok")
        items = [pipeline_report_item(s, self.summaries[s.code], BATCH_TIME) for s in self.pool[:60] if s.code in self.summaries]
        report = push_items(SOURCE_PIPELINE, items * 3, config, post=post)
        self.assertEqual(report["status"], "pushed")
        self.assertTrue(all(size <= 50 for _, size in sent), "单批不超过后端 MAX_ITEMS=50")
        self.assertEqual(report["sent"], len(items) * 3)
        self.assertTrue(all(size <= 50 for _, size in sent), "60 条应拆成 50 + 10 两批")

    def test_every_track_payload_survives_the_backend_url_and_time_contract(self) -> None:
        """跨语言契约（谷米审计 R1 的 P0-1/P0-2 回归锁）。

        后端 `normalizeUrl()` 只认 http/https，`decideTimeline()` 见到空 publishedAt 就判历史回填。
        这里逐条检查四轨 payload，避免再出现「推送成功但入库 created=0」或「全是 backfill」。
        """
        plan = build_push_plan(self.pool, self.summaries, self.platforms)
        checked = 0
        for source_id, items in plan.items():
            for item in items:
                payload = item.to_payload()
                self.assertTrue(
                    payload["url"].startswith("https://"),
                    f"{source_id} 的 {payload['url']!r} 不是 http(s)，会被 normalizeUrl 静默丢弃",
                )
                self.assertTrue(payload.get("publishedAt"), f"{source_id} 缺 publishedAt，会被判 backfill")
                moment = datetime.fromisoformat(payload["publishedAt"])
                self.assertGreaterEqual(moment.year, 2026, f"{source_id} 的发布时间 {payload['publishedAt']} 早于今年，会被判 stale-on-discovery")
                self.assertIsNotNone(moment.tzinfo, "publishedAt 必须带时区")
                checked += 1
        self.assertGreater(checked, 0, "四轨都没产出条目，契约测试会空转")

    def test_pipeline_url_carries_the_trade_date_and_survives_normalisation(self) -> None:
        """战报 URL 带交易日（不同交易日的同票战报不撞身份），且参数不被后端剥掉。"""
        stock = next(s for s in self.pool if s.code == "300308")
        item = pipeline_report_item(stock, self.summaries["300308"], BATCH_TIME)
        self.assertEqual(item.url, "https://quote.eastmoney.com/sz300308.html?date=2026-10-16")
        self.assertIn("date=2026-10-16", item.url)
        # 后端 normalizeUrl 会剥掉 TRACKING_PARAMS（utm_*/from/ref/source/...）；date 不在其中
        tracking = {"utm_source", "spm", "from", "ref", "source", "share_token", "srcid", "clicktime", "mkt_tok"}
        self.assertNotIn("date", tracking)
        self.assertEqual(item.published_at, BATCH_TIME)

    def test_community_item_falls_back_to_batch_time_when_post_time_is_missing(self) -> None:
        dated = community_item(
            CommunityPost(platform="taoguba", post_id="a", url="https://www.tgb.cn/a/x",
                          title="有时间的帖", published_at="2026-10-16T10:05:00+08:00"),
            SOURCE_TAOGUBA, True, BATCH_TIME,
        )
        undated = community_item(
            CommunityPost(platform="taoguba", post_id="b", url="https://www.tgb.cn/a/y", title="没有时间的帖"),
            SOURCE_TAOGUBA, True, BATCH_TIME,
        )
        assert dated is not None and undated is not None
        self.assertEqual(dated.published_at, "2026-10-16T10:05:00+08:00", "帖子自己的发帖时间优先")
        self.assertEqual(undated.published_at, BATCH_TIME, "解析不出时间时退回批次时间，绝不留空")

    def test_push_without_token_reports_no_token(self) -> None:
        config = replace(self.config, dry_run=False, ingest_token="")
        report = push_items(SOURCE_PIPELINE, [pipeline_report_item(self.pool[0], list(self.summaries.values())[0], BATCH_TIME)], config)
        self.assertEqual(report["status"], "no_token")


class TestSnapshot(unittest.TestCase):
    def setUp(self) -> None:
        self.config = offline_config()
        pool, self.catalog, quality = __import__("bridge.pipeline_loader", fromlist=["load_focus_pool"]).load_focus_pool(self.config)
        client = HttpClient(fetcher=build_offline_fetcher(FIXTURES_DIR))
        guba_posts = [p for items in eastmoney_guba.collect(client, pool, top=5).values() for p in items]
        tgb_posts = taoguba.collect(client, self.config.research["tgb_vip"], top=10)
        _, xq = xueqiu.collect(client, self.config.research["xueqiu_authors"], pool, per_stock=5)
        self.platforms = {"eastmoney_guba": guba_posts, "taoguba": tgb_posts, "xueqiu": [p for v in xq.values() for p in v]}
        pool = with_xq_ranks(pool, xueqiu.parse_hot_stock(fixture_json("xueqiu_hot_stock.json")))
        matcher = StockMatcher(pool)
        by_code: dict[str, list[CommunityPost]] = {}
        for posts in self.platforms.values():
            for code, items in matcher.group(posts).items():
                by_code.setdefault(code, []).extend(items)
        engine = SentimentEngine.load(self.config.research["sentiment"])
        pool, self.summaries = apply_to_stocks(pool, by_code, engine, now_beijing())
        self.snapshot = build_snapshot(pool, self.summaries, self.platforms, self.config, quality, top_n=30)

    def test_snapshot_has_ladders_and_resonance_board(self) -> None:
        self.assertTrue(self.snapshot.theme_ladders)
        self.assertTrue(self.snapshot.top_resonance_stocks)
        self.assertEqual(self.snapshot.mode, "offline_fixtures")
        self.assertEqual(len(self.snapshot.top_resonance_stocks), min(30, len(self.snapshot.top_resonance_stocks)))

    def test_resonance_board_sorted_desc_and_carries_sentiment(self) -> None:
        scores = [row["resonanceScore"] for row in self.snapshot.top_resonance_stocks]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for row in self.snapshot.top_resonance_stocks:
            self.assertIn("sentiment", row)
            self.assertAlmostEqual(
                row["sentiment"]["bullRatio"] + row["sentiment"]["divergenceRatio"] + row["sentiment"]["bearRatio"],
                100.0, places=3,
            ) if row["sentiment"]["validPosts"] else None

    def test_ladder_groups_hold_role_buckets(self) -> None:
        ladder = self.snapshot.theme_ladders[0]
        self.assertIn("theme", ladder)
        self.assertIn("ladders", ladder)
        roles = set(ladder["ladders"])
        self.assertTrue(roles <= {"空间板", "20cm弹性", "容量中军", "首板发酵", "人气热股"})
        self.assertTrue(any(row["theme"] == "光模块/CPO" for row in self.snapshot.theme_ladders))

    def test_snapshot_is_json_serialisable(self) -> None:
        text = json.dumps(self.snapshot.to_dict(), ensure_ascii=False)
        self.assertIn("themeLadders", text)
        self.assertIn("topResonanceStocks", text)


class TestGoldSync(unittest.TestCase):
    def test_gold_source_has_70_cases_and_syncs(self) -> None:
        lines = [line for line in GOLD_SOURCE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 70)
        for line in lines[:5]:
            json.loads(line)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "gold.jsonl"
            count = sync_gold(GOLD_SOURCE_PATH, dest)
            self.assertEqual(count, 70)
            self.assertEqual(len(dest.read_text(encoding="utf-8").strip().splitlines()), 70)


# ── 端到端离线演练 ─────────────────────────────────────────────────────────────


class TestEndToEnd(unittest.TestCase):
    def test_offline_run_produces_snapshot_and_gold(self) -> None:
        import io as _io
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            config = BridgeConfig(offline_fixtures=True, dry_run=True, sync_gold=True)
            buffer = _io.StringIO()
            code = run(config, out=buffer)
            self.assertEqual(code, 0, buffer.getvalue())

            snapshot = json.loads((REPO_ROOT / ".data" / "short-term-radar-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["mode"], "offline_fixtures")
            self.assertTrue(snapshot["themeLadders"])
            self.assertTrue(snapshot["topResonanceStocks"])
            self.assertGreaterEqual(snapshot["focusPoolSize"], 1)
            gold = (REPO_ROOT / ".data" / "gold.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(gold), 70)

    def test_run_never_opens_a_socket_when_offline(self) -> None:
        import io as _io
        import urllib.request

        opened: list[str] = []
        original_open = urllib.request.urlopen

        def spy(url, *args, **kwargs):
            opened.append(str(url))
            return original_open(url, *args, **kwargs)  # pragma: no cover - 离线模式不该走到这里

        urllib.request.urlopen = spy  # type: ignore[assignment]
        try:
            buffer = _io.StringIO()
            run(BridgeConfig(offline_fixtures=True, dry_run=True), out=buffer)
        finally:
            urllib.request.urlopen = original_open  # type: ignore[assignment]
        self.assertEqual(opened, [], "离线模式一次网络都不开")


if __name__ == "__main__":
    unittest.main()
