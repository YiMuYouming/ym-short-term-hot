"""焦点股池与题材底座：把 YM-data-pipeline 的热榜/涨跌停池/涨停原因归因，与 60 个短线题材词典合成 Top N 焦点股。

三条输入（LITE-01 起，全部走 `YM-data-pipeline` 公共入口 `from ym_stock_data import query`）：
1. `market_hot_rank`（`source="ths"`/`"dc"`）：热榜 Top N，ths 行带 `ts_code`/`ts_name`/`pct_change`、
   `concept`（JSON 数组字符串）与 `rank_reason`（完整的「行业原因 + 公司原因」，直接回答为什么火）；
2. `market_intraday_state`：涨停池 `limit_up`（`board` 连板数、`pct`、`industry`、`seal_time`）与 `trade_date`；
3. `legacy_hot_rank`：同花顺热点股的涨停原因归因（`reason` 按 `+` 拆题材）与当日 `reason_stats`
   （涨停原因板块统计，如 `{"低空经济": 11}`，热门板块真实热度的来源）。

题材词典为 `docs/aihot_research/dict/themes_v2.json`（Grok 第六波核验：60 题材 / 191 只代表股 / 别名表），
拆解 `reason`/`concept` 时命中别名归一到标准题材名，未命中保留原始概念名作为独立板块。

实测提醒（2026-10-16，本机）：沙箱内 `market_intraday_state`/`legacy_hot_rank` 自述
`degraded`、`market_hot_rank(dc)` 无参常返 `empty`（带 `trade_date` 重试即成功），
所以取数策略是「先盘中状态拿 `trade_date`，热榜无参空时按日期重试一次」，
所有降级都如实记进 `dataQuality`，再用题材底座兜底，而不是静默产出空快照。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from .config import BridgeConfig, PIPELINE_FIXTURE, load_json
from .schema import (
    ROLE_ELASTIC_20CM,
    ROLE_FIRST_BOARD,
    ROLE_MID_CAP,
    ROLE_POPULAR,
    ROLE_SPACE,
    FocusStock,
)

# 题材词典里代表股已给出的身位（离线或管道无数据时直接沿用）
DICT_ROLE_MAP = {
    ROLE_SPACE: ROLE_SPACE,
    ROLE_ELASTIC_20CM: ROLE_ELASTIC_20CM,
    ROLE_MID_CAP: ROLE_MID_CAP,
    ROLE_FIRST_BOARD: ROLE_FIRST_BOARD,
}

# 20cm 弹性：创业板 30x / 科创板 688
ELASTIC_PREFIXES = ("300", "301", "302", "688")


def exchange_of(code: str) -> str:
    """六位代码 → 市场。题材词典里唯一需要跨平台 symbol 的地方。"""
    if code.startswith(("600", "601", "603", "605", "688", "900")):
        return "sh"
    if code.startswith(("000", "001", "002", "003", "300", "301", "302")):
        return "sz"
    if code.startswith(("4", "8", "92")):
        return "bj"
    return "sh" if code.startswith("6") else "sz"


# 个股事件/公告/财务/股权词（LITE-03）：回答「为什么火」时保留在 limit_reason/why_hot，
# 但不进 stock.themes——「三部门联合调查」「参股锴威特」是一只票的事件，不是全市场板块。
EVENT_TAG_KEYWORDS: tuple[str, ...] = (
    "联合调查", "调查", "复牌", "停牌", "重组", "参股", "控股", "收购", "实控人",
    "增持", "减持", "回购", "扭亏", "预增", "季报", "年报", "分红", "摘帽",
)
# 特定车型/产品型号（如「尊界V800」）：窄匹配，避免误伤「800G」「M9」等合法概念别名
PRODUCT_MODEL_PATTERN = re.compile(r"[A-Za-z一-龥]+界\s*[Vv]\d+")


def is_event_or_company_tag(raw_tag: str) -> bool:
    """这个原始标签是不是「个股事件/公司/产品词」——是则不进 themes（防单股伪板块）。"""
    text = str(raw_tag or "").strip()
    if not text:
        return False
    if any(keyword in text for keyword in EVENT_TAG_KEYWORDS):
        return True
    return bool(PRODUCT_MODEL_PATTERN.search(text))


def _alias_candidates(text: str) -> Iterator[str]:
    """别名查找候选：原词 → 去括号后缀（全角/半角，「共封装光学(CPO)」→「共封装光学」）→ 小写变体。"""
    yield text
    stripped = re.sub(r"[（(][^）)]*[）)]\s*$", "", text).strip()
    if stripped and stripped != text:
        yield stripped
        lowered = stripped.lower()
        if lowered != stripped:
            yield lowered
    lowered = text.lower()
    if lowered != text:
        yield lowered


@dataclass
class ThemeCatalog:
    """themes_v2.json 的索引：代码 → 题材/黑话/身位，黑话 → 代码，别名 → 标准题材名。"""

    themes: tuple[str, ...] = ()
    by_code: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_nickname: dict[str, tuple[str, ...]] = field(default_factory=dict)
    stocks_by_theme: dict[str, tuple[str, ...]] = field(default_factory=dict)
    by_alias: dict[str, str] = field(default_factory=dict)
    by_alias_folded: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path) -> "ThemeCatalog":
        raw = load_json(path)
        entries = raw if isinstance(raw, list) else []
        by_code: dict[str, dict[str, Any]] = {}
        nickname_map: dict[str, set[str]] = {}
        by_theme: dict[str, list[str]] = {}
        alias_map: dict[str, str] = {}
        themes: list[str] = []
        for theme in entries:
            name = str(theme.get("standard_name") or "").strip()
            if not name:
                continue
            themes.append(name)
            # 标准名自身也是别名；主题别名（「飞行汽车」→「低空经济/eVTOL」）先到先得，冲突保留首个
            alias_map.setdefault(name, name)
            for alias in theme.get("aliases") or []:
                alias = str(alias or "").strip()
                if alias:
                    alias_map.setdefault(alias, name)
            for stock in theme.get("representative_stocks") or []:
                code = str(stock.get("code") or "").strip()
                if not code:
                    continue
                nicknames = tuple(
                    str(item.get("term") or "").strip()
                    for item in stock.get("nicknames") or []
                    if str(item.get("term") or "").strip()
                )
                entry = by_code.setdefault(
                    code,
                    {
                        "name": str(stock.get("name") or code),
                        "themes": set(),
                        "nicknames": set(),
                        "role": None,
                    },
                )
                entry["themes"].add(name)
                # 「易中天」这样的组合黑话挂在每只代表股上，索引时反向聚合
                entry["nicknames"].update(nicknames)
                role = DICT_ROLE_MAP.get(str(stock.get("role") or ""))
                if role and entry["role"] is None:
                    entry["role"] = role
                by_theme.setdefault(name, []).append(code)
                for nickname in nicknames:
                    nickname_map.setdefault(nickname, set()).add(code)
        return cls(
            themes=tuple(themes),
            by_code=by_code,
            by_nickname={key: tuple(sorted(value)) for key, value in nickname_map.items()},
            stocks_by_theme={key: tuple(dict.fromkeys(value)) for key, value in by_theme.items()},
            by_alias=alias_map,
            by_alias_folded={key.lower(): value for key, value in alias_map.items()},
        )

    def lookup(self, code: str) -> dict[str, Any]:
        entry = self.by_code.get(code)
        if not entry:
            return {"name": "", "themes": set(), "nicknames": set(), "role": None}
        return entry

    def resolve_nickname(self, nickname: str) -> tuple[str, ...]:
        """「易中天」→「300502 / 300308 / 300394」；未收录返回空。"""
        return self.by_nickname.get(nickname, ())

    def normalize_theme(self, name: str) -> str:
        """别名 → 标准题材名；未命中保留原始概念名。

        拆解 `legacy_hot_rank.reason` 或 `ths_hot.concept` 时逐个 token 过这里：
        命中别名归一到标准题材（含括号后缀与大小写变体：「共封装光学(CPO)」「cpo」「PCB概念」），
        未命中（如「卫星通信芯片」）直接作为独立板块，绝不丢进「未归题材」。
        """
        text = str(name or "").strip()
        if not text:
            return ""
        for candidate in _alias_candidates(text):
            hit = self.by_alias.get(candidate) or self.by_alias_folded.get(candidate.lower())
            if hit:
                return hit
        return text

    def infer_themes(self, text: str, limit: int = 3) -> tuple[str, ...]:
        """从自由文本（rank_reason / 股票名 + 原因）推断标准题材归属，长别名优先。

        板块归属兜底链的一环：当日归因与概念都为空时，用上榜原因正文里的行业关键词
        把股票拉回标准板块；仍推断不出才归「其他热点」。
        """
        body = str(text or "")
        if not body:
            return ()
        hits: list[tuple[int, str]] = []
        for alias, standard in self.by_alias.items():
            if len(alias) < 2 or alias not in body:
                continue
            hits.append((-len(alias), standard))
        themes: list[str] = []
        for _weight, standard in sorted(hits):
            if standard not in themes:
                themes.append(standard)
            if len(themes) >= limit:
                break
        return tuple(themes)

    @property
    def base_codes(self) -> tuple[str, ...]:
        """题材底座的全部代表股代码（管道无数据时的兜底候选）。"""
        return tuple(self.by_code)


@dataclass
class PipelineData:
    """管道原始数据。字段全部容错解析，缺失即为空列表而不是抛错。"""

    ths_hot: list[dict[str, Any]] = field(default_factory=list)
    dc_hot: list[dict[str, Any]] = field(default_factory=list)
    intraday: dict[str, Any] = field(default_factory=dict)
    legacy_hot: list[dict[str, Any]] = field(default_factory=list)  # legacy_hot_rank.items：涨停原因归因
    reason_stats: dict[str, int] = field(default_factory=dict)     # 当日涨停原因板块统计（题材 → 家数）
    trade_date: str = ""                                           # 最近实际交易日 YYYYMMDD

    @property
    def has_hot(self) -> bool:
        return bool(self.ths_hot or self.dc_hot)

    def pool_rows(self) -> list[dict[str, Any]]:
        """盘中状态里的涨停池：不同来源字段名不同，按已知形状逐个认。"""
        for key in ("limit_up_pool", "zt_pool", "pools", "limit_up", "up_pool"):
            value = self.intraday.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        pools = self.intraday.get("pools")
        if isinstance(pools, dict):
            for key in ("limit_up", "zt", "up"):
                value = pools.get(key)
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
        return []


def _first(row: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return default


def _int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_code(value: Any) -> str:
    """从 `600519`、`SH600519`、`600519.SH`、`000530.SZ` 等形状里取六位代码。"""
    text = str(value or "").strip().upper()
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits[:6] if len(digits) >= 6 else ""


def _unwrap(payload: Any) -> Any:
    """管道响应外层是 `{"_meta": ..., "data": {...}}`；离线样本的 items 在顶层。两者都认。"""
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload


def _concepts(value: Any) -> list[str]:
    """`concept` 字段：同花顺给 JSON 数组字符串（`'["冰雪产业", "体育产业"]'`），东财常为 null。"""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return [text]
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [str(parsed).strip()] if str(parsed).strip() else []


def _trade_date_of(*values: Any) -> str:
    """`20261016` / `2026-10-16` / `2026-10-16T…` → `YYYYMMDD`；取不到返回空串。"""
    for value in values:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if len(digits) >= 8:
            return digits[:8]
    return ""


def parse_hot_rank(payload: Any, limit: int) -> list[dict[str, Any]]:
    """热榜 items → [{code, name, rank, change_pct, amount_yi, concept, rank_reason}]，rank 从 1 开始。

    兼容管道真实形状（`data.items`，字段 `ts_code`/`ts_name`/`pct_change`/`concept`/`rank_reason`）
    与离线样本（`items` 在顶层，旧字段 `code`/`zdpct`）。
    """
    body = _unwrap(payload)
    rows = body.get("items") if isinstance(body, dict) else body
    out: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return out
    for index, row in enumerate(rows[:limit], start=1):
        if not isinstance(row, dict):
            continue
        code = _normalize_code(_first(row, "code", "stock_code", "symbol", "secu_code", "ts_code"))
        if not code:
            continue
        amount = _float(_first(row, "amount", "turnover", "deal_amount"))
        out.append(
            {
                "code": code,
                "name": str(_first(row, "name", "stock_name", "stockName", "ts_name", default=code)),
                "rank": _int(_first(row, "rank", "index", "order")) or index,
                "change_pct": _float(_first(row, "change_pct", "chg", "zdpct", "changePct", "pct_change")),
                "amount_yi": amount / 1e8 if amount is not None and amount > 1e6 else amount,
                "concept": _concepts(row.get("concept")),
                "rank_reason": str(row.get("rank_reason") or "").strip(),
            }
        )
    return out


def parse_legacy(payload: Any) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """`legacy_hot_rank`（同花顺热点 + 涨停原因归因）→ (items, reason_stats)。

    items 行含 `code`/`name`/`zhangfu`/`reason`（`+` 分隔题材串）/`chengjiaoe`（成交额，万元）；
    `reason_stats` 是当日涨停原因的板块统计（`{"低空经济": 11}`），热门板块真实热度的来源。
    """
    body = _unwrap(payload)
    if not isinstance(body, dict):
        return [], {}
    rows = [row for row in body.get("items") or [] if isinstance(row, dict)]
    stats: dict[str, int] = {}
    raw_stats = body.get("reason_stats")
    if isinstance(raw_stats, dict):
        for key, value in raw_stats.items():
            count = _int(value)
            if count is not None:
                stats[str(key).strip()] = count
    return rows, stats


def parse_intraday(payload: Any) -> dict[str, Any]:
    """盘中状态：保留 indicators（宽度/涨停数等）与涨停池行，供身位与宽度引用。"""
    if not isinstance(payload, dict):
        return {}
    body = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    indicators = body.get("indicators") if isinstance(body.get("indicators"), dict) else {}
    merged: dict[str, Any] = {"indicators": indicators}
    for key in ("limit_up_pool", "zt_pool", "pools", "limit_up", "trade_date"):
        if key in body:
            merged[key] = body[key]
    return merged


def _queryer(config: BridgeConfig) -> Callable[..., dict[str, Any]] | None:
    """加载 YM-data-pipeline 的公共入口；不可用时返回 None（调用方记降级）。"""
    root = str(config.pipeline_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from ym_stock_data import query  # type: ignore
    except Exception:  # noqa: BLE001 - 环境缺依赖或未安装时统一按「管道不可用」处理
        return None
    return query


def load_pipeline(config: BridgeConfig, query: Callable[..., dict[str, Any]] | None = None) -> tuple[PipelineData, dict[str, Any]]:
    """取管道数据。返回 (数据, 质量记录)；`quality.sources[name].status` 如实反映管道自述。

    在线顺序（LITE-01）：先 `market_intraday_state` 拿 `trade_date` → 两路热榜无参取实时榜、
    为空且已知日期时按 `trade_date` 重试一次（dc 实时榜常返 empty，带日期即成功）→
    `legacy_hot_rank` 拿涨停原因归因与当日板块热度统计。
    离线模式只读 `bridge/tests/fixtures/pipeline_sample.json`，不碰外网也不碰付费配额。
    """
    quality: dict[str, Any] = {"mode": config.mode, "sources": {}, "warnings": []}

    if config.offline_fixtures:
        fixture = load_json(PIPELINE_FIXTURE) or {}
        data = PipelineData(
            ths_hot=parse_hot_rank(fixture.get("ths_hot"), 100),
            dc_hot=parse_hot_rank(fixture.get("dc_hot"), 100),
            intraday=parse_intraday(fixture.get("intraday")),
        )
        data.legacy_hot, data.reason_stats = parse_legacy(fixture.get("legacy_hot_rank"))
        data.trade_date = _trade_date_of(
            data.intraday.get("trade_date"),
            *(row.get("trade_date") for row in data.legacy_hot),
        )
        quality["sources"] = {
            "ths_hot": {"status": "fixture", "rows": len(data.ths_hot)},
            "dc_hot": {"status": "fixture", "rows": len(data.dc_hot)},
            "intraday": {"status": "fixture", "rows": len(data.pool_rows())},
            "legacy_hot_rank": {
                "status": "fixture",
                "rows": len(data.legacy_hot),
                "reasonStats": len(data.reason_stats),
            },
        }
        quality["tradeDate"] = data.trade_date
        quality["hotAvailable"] = data.has_hot
        return data, quality

    resolve = query or _queryer(config)
    if resolve is None:
        quality["warnings"].append(f"YM-data-pipeline 公共入口不可用：{config.pipeline_root}")
        quality["sources"] = {
            name: {"status": "unavailable"}
            for name in ("ths_hot", "dc_hot", "intraday", "legacy_hot_rank")
        }
        quality["hotAvailable"] = False
        return PipelineData(), quality

    data = PipelineData()

    # 1) 盘中状态优先：拿到最近实际交易日（ths 热榜的 rank_reason 只有带 trade_date 才稳定返回）
    try:
        response = resolve("market_intraday_state")
        meta = response.get("_meta") or {} if isinstance(response, dict) else {}
        data.intraday = parse_intraday(response)
        quality["sources"]["intraday"] = {
            "status": meta.get("status") or ("ok" if data.intraday else "empty"),
            "provider": meta.get("provider"),
            "data_as_of": meta.get("data_as_of"),
            "rows": len(data.pool_rows()),
        }
        if not data.pool_rows():
            quality["warnings"].append("market_intraday_state 无涨停池，连板身位只能靠词典标注")
    except Exception as exc:  # noqa: BLE001
        quality["sources"]["intraday"] = {"status": "error", "error": str(exc)[:200]}
    data.trade_date = _trade_date_of(data.intraday.get("trade_date"))

    # 2) 两路热榜：先无参取实时榜；为空且已知 trade_date 时按日期重试一次
    for name, source in (("ths_hot", "ths"), ("dc_hot", "dc")):
        attempts: list[dict[str, Any]] = [{}]
        if data.trade_date:
            attempts.append({"trade_date": data.trade_date})
        rows: list[dict[str, Any]] = []
        meta: dict[str, Any] = {}
        error = ""
        for extra in attempts:
            try:
                response = resolve("market_hot_rank", source=source, limit=100, **extra)
            except Exception as exc:  # noqa: BLE001 - 单个意图失败不应让整池崩掉
                error = str(exc)[:200]
                continue
            meta = response.get("_meta") or {} if isinstance(response, dict) else {}
            rows = parse_hot_rank(response, 100)
            if rows:
                break
        setattr(data, name, rows)
        quality["sources"][name] = {
            "status": meta.get("status") or ("ok" if rows else "empty"),
            "provider": meta.get("provider"),
            "data_as_of": meta.get("data_as_of"),
            "rows": len(rows),
        }
        if error:
            quality["sources"][name]["error"] = error
        if not rows:
            quality["warnings"].append(f"{name} 无数据（_meta.status={meta.get('status')}），焦点股池将退回题材底座")

    # 3) 涨停原因归因 + 当日热门板块统计（热门板块真实热度的来源）
    try:
        response = resolve("legacy_hot_rank")
        meta = response.get("_meta") or {} if isinstance(response, dict) else {}
        data.legacy_hot, data.reason_stats = parse_legacy(response)
        quality["sources"]["legacy_hot_rank"] = {
            "status": meta.get("status") or ("ok" if data.legacy_hot else "empty"),
            "provider": meta.get("provider"),
            "data_as_of": meta.get("data_as_of"),
            "rows": len(data.legacy_hot),
            "reasonStats": len(data.reason_stats),
        }
        if not data.legacy_hot:
            quality["warnings"].append("legacy_hot_rank 无数据，涨停原因与板块热度统计缺失")
        if not data.trade_date:
            data.trade_date = _trade_date_of(*(row.get("trade_date") for row in data.legacy_hot))
    except Exception as exc:  # noqa: BLE001
        quality["sources"]["legacy_hot_rank"] = {"status": "error", "error": str(exc)[:200]}

    quality["tradeDate"] = data.trade_date
    quality["hotAvailable"] = data.has_hot
    return data, quality


def _role_of(code: str, board_count: int, change_pct: float | None, amount_yi: float | None,
             dict_role: str | None) -> str:
    """当日身位优先，管道无数据时退回题材词典的标注。"""
    if board_count >= 3:
        return ROLE_SPACE
    if code.startswith(ELASTIC_PREFIXES) and ((change_pct or 0) >= 9.8 or board_count >= 1):
        return ROLE_ELASTIC_20CM
    if (amount_yi or 0) >= 50 or dict_role == ROLE_MID_CAP:
        return ROLE_MID_CAP
    if board_count == 1:
        return ROLE_FIRST_BOARD
    if dict_role:
        return dict_role
    return ROLE_POPULAR


_ROLE_RANK = {ROLE_SPACE: 0, ROLE_ELASTIC_20CM: 1, ROLE_MID_CAP: 2, ROLE_FIRST_BOARD: 3, ROLE_POPULAR: 4}


def _merge_themes(entry: dict[str, Any], catalog: ThemeCatalog, info: dict[str, Any]) -> tuple[str, ...]:
    """合并题材归属：词典命中 → legacy reason 拆分 → ths concept → 兜底链（LITE-03）。

    动态来源（涨停原因拆词、概念标签）先过 `is_event_or_company_tag`：事件/公司/产品词
    只留在 limit_reason/why_hot，不建板块；词典静态归属已核实，不过滤。
    每个候选过 `catalog.normalize_theme`（别名归一到标准题材，未命中保留原始概念名），保序去重。
    仍为空时依次尝试 industry → rank_reason 行业关键词 → 名称与原因文本推断 → 「其他热点」，
    保证焦点股 100% 有板块归属（unassigned_stock_count == 0）。
    """
    candidates: list[str] = list(info["themes"])
    reason = str(entry.get("legacy_reason") or "").strip()
    if reason:
        candidates.extend(
            part.strip()
            for part in reason.split("+")
            if part.strip() and not is_event_or_company_tag(part.strip())
        )
    concepts = [tag for tag in (entry.get("concepts") or []) if not is_event_or_company_tag(tag)]
    candidates.extend(concepts)
    themes: list[str] = []
    for candidate in candidates:
        name = catalog.normalize_theme(candidate)
        if name and name not in themes:
            themes.append(name)
    if themes:
        return tuple(themes)

    # 兜底链：industry → rank_reason 行业关键词 → 名称+原因文本推断 → 其他热点
    industry = str(entry.get("industry") or "").strip()
    if industry and not is_event_or_company_tag(industry):
        return (catalog.normalize_theme(industry),)
    if entry.get("rank_reason"):
        inferred = catalog.infer_themes(str(entry["rank_reason"]))
        if inferred:
            return inferred
    text = " ".join(part for part in (entry.get("name"), reason, "+".join(concepts)) if part)
    return catalog.infer_themes(text) or ("其他热点",)


def _why_hot_of(entry: dict[str, Any], themes: tuple[str, ...] = ()) -> tuple[str, str]:
    """合成 (limit_reason, why_hot)：为什么火的一句话标签与详细正文。

    `limit_reason`（层层兜底不落空）：涨停原因串（`卫星通信芯片+低空经济`）→ 概念组合
    → 所属行业 → 题材归属（词典核实的标准题材名）；
    `why_hot`：优先同花顺 `rank_reason`（行业原因 + 公司原因全文，截掉末尾免责声明），
    其次「连板/封板 + 涨停原因」，再次「连板/封板 + 热门概念」，最后「连板/封板 + 题材归属」，
    皆无时只留连板/封板描述——每一层都是真实数据，不编造。
    """
    reason = str(entry.get("legacy_reason") or "").strip()
    concepts = list(dict.fromkeys(entry.get("concepts") or []))
    industry = str(entry.get("industry") or "").strip()
    board = entry.get("board_count") or 0
    seal = str(entry.get("seal_time") or "").strip()

    limit_reason = reason or "+".join(concepts) or industry or "+".join(themes[:2])

    position: list[str] = []
    if board >= 2:
        position.append(f"{board} 连板")
    elif board == 1:
        position.append("首板涨停")
    if seal:
        position.append(f"{seal} 封板")
    position_text = "；".join(position)

    rank_reason = str(entry.get("rank_reason") or "").replace("\\n", "\n").strip()
    if rank_reason:
        rank_reason = rank_reason.split("（免责声明")[0].strip()
    if rank_reason:
        head = "；".join(part for part in (limit_reason, position_text) if part)
        return limit_reason, f"{head}\n{rank_reason}" if head else rank_reason
    if reason:
        head = "；".join(part for part in (position_text, f"涨停原因：{reason}") if part)
        return limit_reason, head
    line = ""
    if concepts:
        line = f"热门概念：{'+'.join(concepts)}"
    elif themes and not industry:
        line = f"题材归属：{'+'.join(themes[:3])}"
    head = "；".join(part for part in (position_text, line) if part)
    return limit_reason, head


def build_focus_pool(
    data: PipelineData,
    catalog: ThemeCatalog,
    limit: int = 50,
) -> list[FocusStock]:
    """合成焦点股池：热榜决定「今天谁热」，涨停原因与概念定题材，盘中池补连板身位。

    整合 `ths_hot`/`dc_hot`/`legacy_hot_rank`/`intraday.limit_up` 四个真实来源，题材按
    「词典命中 → 涨停原因拆分 → 概念 → 行业兜底」合并，并合成 `limit_reason`/`why_hot`。
    管道无数据时用题材底座代表股兜底（`sources` 标 `theme_base`，快照里可分辨）。
    """
    boards: dict[str, dict[str, Any]] = {}
    for row in data.pool_rows():
        code = _normalize_code(_first(row, "code", "stock_code", "symbol", "secu_code", "ts_code"))
        if code:
            boards[code] = row

    def new_entry(code: str, name: str, sources: list[str]) -> dict[str, Any]:
        return {
            "code": code,
            "name": name,
            "change_pct": None,
            "amount_yi": None,
            "board_count": 0,
            "sources": list(sources),
            "hot_rank_ths": None,
            "hot_rank_dc": None,
            "hot_rank_xq": None,
            "concepts": [],
            "rank_reason": "",
            "legacy_reason": "",
            "industry": "",
            "seal_time": "",
        }

    merged: dict[str, dict[str, Any]] = {}

    def absorb(rows: list[dict[str, Any]], tag: str, rank_field: str) -> None:
        for row in rows:
            code = row["code"]
            entry = merged.setdefault(code, new_entry(code, row.get("name") or code, []))
            entry["sources"].append(tag)
            if row.get("name") and row["name"] != code:
                entry["name"] = row["name"]
            if entry[rank_field] is None:
                entry[rank_field] = row.get("rank")
            for key in ("change_pct", "amount_yi"):
                if entry[key] is None and row.get(key) is not None:
                    entry[key] = row[key]
            entry["concepts"].extend(row.get("concept") or [])
            if row.get("rank_reason") and not entry["rank_reason"]:
                entry["rank_reason"] = row["rank_reason"]

    absorb(data.ths_hot, "ths", "hot_rank_ths")
    absorb(data.dc_hot, "dc", "hot_rank_dc")

    # legacy_hot_rank：涨停原因归因（reason 串）；chengjiaoe 成交额为万元
    for row in data.legacy_hot:
        code = _normalize_code(_first(row, "code", "stock_code", "symbol", "secu_code", "ts_code"))
        if not code:
            continue
        entry = merged.setdefault(code, new_entry(code, str(row.get("name") or code), []))
        if "legacy" not in entry["sources"]:
            entry["sources"].append("legacy")
        name = str(row.get("name") or "").strip()
        if name and (not entry["name"] or entry["name"] == code):
            entry["name"] = name
        if entry["change_pct"] is None:
            entry["change_pct"] = _float(row.get("zhangfu"))
        if entry["amount_yi"] is None:
            amount = _float(row.get("chengjiaoe"))
            if amount is not None:
                entry["amount_yi"] = amount / 1e4
        reason = str(row.get("reason") or "").strip()
        if reason and not entry["legacy_reason"]:
            entry["legacy_reason"] = reason

    # 涨停池：连板数 / 涨跌幅 / 所属行业 / 封板时间
    for code, row in boards.items():
        entry = merged.setdefault(
            code, new_entry(code, str(_first(row, "name", "stock_name", default=code)), ["intraday"])
        )
        if "intraday" not in entry["sources"]:
            entry["sources"].append("intraday")
        entry["board_count"] = max(
            entry["board_count"],
            _int(_first(row, "board", "boards", "board_count", "lbc", "limit_up_type")) or 0,
        )
        if entry["change_pct"] is None:
            entry["change_pct"] = _float(_first(row, "pct", "zdpct", "change_pct", "chg"))
        if entry["amount_yi"] is None:
            amount = _float(_first(row, "amount", "turnover"))
            if amount is not None:
                entry["amount_yi"] = amount / 1e8 if amount > 1e6 else amount
        industry = str(row.get("industry") or "").strip()
        if industry and not entry["industry"]:
            entry["industry"] = industry
        seal = str(row.get("seal_time") or "").strip()
        if seal:
            entry["seal_time"] = seal

    # 题材底座补齐：管道空池时也要有可用候选，且都标 theme_base 以便分辨来源
    for code in catalog.base_codes:
        if len(merged) >= limit:
            break
        if code in merged:
            continue
        merged[code] = new_entry(code, catalog.lookup(code)["name"] or code, ["theme_base"])

    pool: list[FocusStock] = []
    for code, entry in merged.items():
        info = catalog.lookup(code)
        role = _role_of(code, entry["board_count"], entry["change_pct"], entry["amount_yi"], info["role"])
        themes = _merge_themes(entry, catalog, info)
        limit_reason, why_hot = _why_hot_of(entry, themes)
        pool.append(
            FocusStock(
                code=code,
                name=entry["name"],
                exchange=exchange_of(code),
                themes=themes,
                nicknames=tuple(sorted(info["nicknames"])),
                role_label=role,
                board_count=entry["board_count"],
                change_pct=entry["change_pct"],
                amount_yi=entry["amount_yi"],
                hot_rank_ths=entry.get("hot_rank_ths"),
                hot_rank_dc=entry.get("hot_rank_dc"),
                sources=tuple(dict.fromkeys(entry["sources"])),
                limit_reason=limit_reason,
                why_hot=why_hot,
                seal_time=entry["seal_time"],
            )
        )

    pool.sort(key=lambda stock: (_ROLE_RANK.get(stock.role_label, 9), stock.hot_rank_ths or 999, stock.hot_rank_dc or 999, stock.code))
    return pool[:limit]


def load_focus_pool(config: BridgeConfig) -> tuple[list[FocusStock], ThemeCatalog, dict[str, Any]]:
    """S3 对外入口：一次拿到焦点股池、题材词典与数据质量记录。

    `quality["reasonStats"]` 是当日涨停原因板块统计（热门板块梯队真实热度的排序依据），
    随快照 `dataQuality` 落盘，前端与复盘都能对账。
    """
    catalog = ThemeCatalog.load(config.research["themes"])
    data, quality = load_pipeline(config)
    pool = build_focus_pool(data, catalog, config.focus_limit)
    quality["focusPoolSize"] = len(pool)
    quality["hotAvailable"] = data.has_hot
    quality["reasonStats"] = dict(data.reason_stats)
    return pool, catalog, quality


class StockMatcher:
    """把社区帖子归到焦点股：帖子自带 code 优先，否则按代码/股票名/社区黑话扫描全文。

    社区语境里「易中天」比股票名更好用（没人写全称），所以黑话别名与代码同级；
    一条帖命中多只（组合黑话）时全部归属，不猜「最像的那只」。
    """

    def __init__(self, stocks: list[FocusStock]) -> None:
        self.by_code = {stock.code: stock for stock in stocks}
        self._needles: list[tuple[str, tuple[str, ...]]] = []
        for stock in stocks:
            needles = [stock.name, *stock.nicknames]
            if stock.name and stock.name not in needles:
                needles.append(stock.name)
            codes = tuple(dict.fromkeys(needle for needle in needles if needle and len(needle) >= 2))
            if codes:
                self._needles.append((stock.code, codes))

    def match(self, post) -> tuple[str, ...]:
        """帖子 → 命中的股票代码（空元组表示泛题材帖，不强行归属）。"""
        explicit = getattr(post, "code", None)
        if explicit and explicit in self.by_code:
            return (explicit,)
        text = post.text
        hits: list[str] = []
        for code, needles in self._needles:
            if any(needle in text for needle in needles):
                hits.append(code)
        return tuple(hits)

    def group(self, posts) -> dict[str, list]:
        """一批帖子 → {code: 帖子列表}，保持帖子原始顺序。"""
        out: dict[str, list] = {}
        for post in posts:
            for code in self.match(post):
                out.setdefault(code, []).append(post)
        return out
