"""焦点股池与题材底座：把 YM-data-pipeline 的热榜/涨跌停池，与 28 个短线题材词典合成 Top N 焦点股。

两条输入：
1. `YM-data-pipeline` 公共入口（`from ym_stock_data import query`）的热榜与盘中状态；
2. `docs/aihot_research/dict/themes.json` 的题材归属、社区黑话与身位标注（28 题材 / 74 只代表股）。

实测提醒（2026-10-16，本机）：`market_hot_rank` 与 `market_intraday_state` 在沙箱内返回
`status=empty/degraded`（StockToday 鉴权 + 外网受限），所以**在线取不到数据是常态**，
必须如实记进 `dataQuality`，再用题材底座兜底出一条可用的焦点股池，而不是静默产出空快照。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Callable

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


@dataclass
class ThemeCatalog:
    """themes.json 的索引：代码 → 题材/黑话/身位，黑话 → 代码。"""

    themes: tuple[str, ...] = ()
    by_code: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_nickname: dict[str, tuple[str, ...]] = field(default_factory=dict)
    stocks_by_theme: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @classmethod
    def load(cls, path) -> "ThemeCatalog":
        raw = load_json(path)
        entries = raw if isinstance(raw, list) else []
        by_code: dict[str, dict[str, Any]] = {}
        nickname_map: dict[str, set[str]] = {}
        by_theme: dict[str, list[str]] = {}
        themes: list[str] = []
        for theme in entries:
            name = str(theme.get("standard_name") or "").strip()
            if not name:
                continue
            themes.append(name)
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
        )

    def lookup(self, code: str) -> dict[str, Any]:
        entry = self.by_code.get(code)
        if not entry:
            return {"name": "", "themes": set(), "nicknames": set(), "role": None}
        return entry

    def resolve_nickname(self, nickname: str) -> tuple[str, ...]:
        """「易中天」→「300502 / 300308 / 300394」；未收录返回空。"""
        return self.by_nickname.get(nickname, ())

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
    """从 `600519`、`SH600519`、`600519.SH` 等形状里取六位代码。"""
    text = str(value or "").strip().upper()
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits[:6] if len(digits) >= 6 else ""


def parse_hot_rank(payload: Any, limit: int) -> list[dict[str, Any]]:
    """热榜 items → [{code, name, rank, change_pct, amount_yi}]，rank 从 1 开始。"""
    rows = payload.get("items") if isinstance(payload, dict) else payload
    out: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return out
    for index, row in enumerate(rows[:limit], start=1):
        if not isinstance(row, dict):
            continue
        code = _normalize_code(_first(row, "code", "stock_code", "symbol", "secu_code"))
        if not code:
            continue
        amount = _float(_first(row, "amount", "turnover", "deal_amount"))
        out.append(
            {
                "code": code,
                "name": str(_first(row, "name", "stock_name", "stockName", default=code)),
                "rank": _int(_first(row, "rank", "index", "order")) or index,
                "change_pct": _float(_first(row, "change_pct", "chg", "zdpct", "changePct")),
                "amount_yi": amount / 1e8 if amount is not None and amount > 1e6 else amount,
            }
        )
    return out


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

    离线模式只读 `bridge/tests/fixtures/pipeline_sample.json`，不碰外网也不碰付费配额。
    """
    quality: dict[str, Any] = {"mode": config.mode, "sources": {}, "warnings": []}

    if config.offline_fixtures:
        fixture = load_json(PIPELINE_FIXTURE)
        data = PipelineData(
            ths_hot=parse_hot_rank((fixture or {}).get("ths_hot"), 100),
            dc_hot=parse_hot_rank((fixture or {}).get("dc_hot"), 100),
            intraday=parse_intraday((fixture or {}).get("intraday")),
        )
        for name in ("ths_hot", "dc_hot", "intraday"):
            quality["sources"][name] = {
                "status": "fixture",
                "rows": len(data.ths_hot if name == "ths_hot" else data.dc_hot if name == "dc_hot" else data.pool_rows()),
            }
        quality["hotAvailable"] = data.has_hot
        return data, quality

    resolve = query or _queryer(config)
    if resolve is None:
        quality["warnings"].append(f"YM-data-pipeline 公共入口不可用：{config.pipeline_root}")
        quality["sources"] = {name: {"status": "unavailable"} for name in ("ths_hot", "dc_hot", "intraday")}
        quality["hotAvailable"] = False
        return PipelineData(), quality

    data = PipelineData()
    for name, source in (("ths_hot", "ths"), ("dc_hot", "dc")):
        try:
            response = resolve("market_hot_rank", source=source, limit=100)
        except Exception as exc:  # noqa: BLE001 - 单个意图失败不应让整池崩掉
            quality["sources"][name] = {"status": "error", "error": str(exc)[:200]}
            continue
        meta = response.get("_meta") or {} if isinstance(response, dict) else {}
        rows = parse_hot_rank(response, 100)
        setattr(data, name, rows)
        quality["sources"][name] = {
            "status": meta.get("status") or ("ok" if rows else "empty"),
            "provider": meta.get("provider"),
            "data_as_of": meta.get("data_as_of"),
            "rows": len(rows),
        }
        if not rows:
            quality["warnings"].append(f"{name} 无数据（_meta.status={meta.get('status')}），焦点股池将退回题材底座")

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
        if not data.intraday:
            quality["warnings"].append("market_intraday_state 无数据，连板身位只能靠词典标注")
    except Exception as exc:  # noqa: BLE001
        quality["sources"]["intraday"] = {"status": "error", "error": str(exc)[:200]}
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


def build_focus_pool(
    data: PipelineData,
    catalog: ThemeCatalog,
    limit: int = 50,
) -> list[FocusStock]:
    """合成焦点股池：热榜决定「今天谁热」，题材词典补题材与黑话，盘中池补连板身位。

    管道无数据时用题材底座代表股兜底（`sources` 标 `theme_base`，快照里可分辨）。
    """
    boards: dict[str, dict[str, Any]] = {}
    for row in data.pool_rows():
        code = _normalize_code(_first(row, "code", "stock_code", "symbol", "secu_code"))
        if code:
            boards[code] = row

    merged: dict[str, dict[str, Any]] = {}

    def absorb(rows: list[dict[str, Any]], tag: str, rank_field: str) -> None:
        for row in rows:
            code = row["code"]
            entry = merged.setdefault(
                code,
                {
                    "code": code,
                    "name": row.get("name") or code,
                    "change_pct": None,
                    "amount_yi": None,
                    "board_count": 0,
                    "sources": [],
                    "hot_rank_ths": None,
                    "hot_rank_dc": None,
                    "hot_rank_xq": None,
                },
            )
            entry["sources"].append(tag)
            if row.get("name") and row["name"] != code:
                entry["name"] = row["name"]
            if entry[rank_field] is None:
                entry[rank_field] = row.get("rank")
            for key in ("change_pct", "amount_yi"):
                if entry[key] is None and row.get(key) is not None:
                    entry[key] = row[key]

    absorb(data.ths_hot, "ths", "hot_rank_ths")
    absorb(data.dc_hot, "dc", "hot_rank_dc")
    for code, row in boards.items():
        entry = merged.setdefault(
            code,
            {"code": code, "name": str(_first(row, "name", "stock_name", default=code)), "change_pct": None,
             "amount_yi": None, "board_count": 0, "sources": ["intraday"],
             "hot_rank_ths": None, "hot_rank_dc": None, "hot_rank_xq": None},
        )
        if "intraday" not in entry["sources"]:
            entry["sources"].append("intraday")
        entry["board_count"] = max(entry["board_count"], _int(_first(row, "boards", "board_count", "lbc", "limit_up_type")) or 0)
        if entry["change_pct"] is None:
            entry["change_pct"] = _float(_first(row, "zdpct", "change_pct", "chg"))
        if entry["amount_yi"] is None:
            amount = _float(_first(row, "amount", "turnover"))
            if amount is not None:
                entry["amount_yi"] = amount / 1e8 if amount > 1e6 else amount

    # 题材底座补齐：管道空池时也要有可用候选，且都标 theme_base 以便分辨来源
    for code in catalog.base_codes:
        if len(merged) >= limit:
            break
        if code in merged:
            continue
        merged[code] = {
            "code": code,
            "name": catalog.lookup(code)["name"] or code,
            "change_pct": None,
            "amount_yi": None,
            "board_count": 0,
            "sources": ["theme_base"],
            "hot_rank_ths": None,
            "hot_rank_dc": None,
            "hot_rank_xq": None,
        }

    pool: list[FocusStock] = []
    for code, entry in merged.items():
        info = catalog.lookup(code)
        role = _role_of(code, entry["board_count"], entry["change_pct"], entry["amount_yi"], info["role"])
        pool.append(
            FocusStock(
                code=code,
                name=entry["name"],
                exchange=exchange_of(code),
                themes=tuple(sorted(info["themes"])),
                nicknames=tuple(sorted(info["nicknames"])),
                role_label=role,
                board_count=entry["board_count"],
                change_pct=entry["change_pct"],
                amount_yi=entry["amount_yi"],
                hot_rank_ths=entry.get("hot_rank_ths"),
                hot_rank_dc=entry.get("hot_rank_dc"),
                sources=tuple(dict.fromkeys(entry["sources"])),
            )
        )

    pool.sort(key=lambda stock: (_ROLE_RANK.get(stock.role_label, 9), stock.hot_rank_ths or 999, stock.hot_rank_dc or 999, stock.code))
    return pool[:limit]


def load_focus_pool(config: BridgeConfig) -> tuple[list[FocusStock], ThemeCatalog, dict[str, Any]]:
    """S3 对外入口：一次拿到焦点股池、题材词典与数据质量记录。"""
    catalog = ThemeCatalog.load(config.research["themes"])
    data, quality = load_pipeline(config)
    pool = build_focus_pool(data, catalog, config.focus_limit)
    quality["focusPoolSize"] = len(pool)
    quality["hotAvailable"] = data.has_hot
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
