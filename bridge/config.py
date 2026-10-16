"""桥接的配置：路径、数据管道入口、AIHOT 接口、配额与超时。

全部可用环境变量覆盖，默认值指向本机的 canonical checkout 与本地实例。
这里不读 .env：桥接是命令行程序，密钥只从环境或命令行传入。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# 仓库根（bridge/ 的上一级）
REPO_ROOT = Path(__file__).resolve().parents[1]

# 谷米在 Grok 实测中合入的调研资产：接口规范、游资名录、题材与情绪词典、金标集
RESEARCH_DIR = REPO_ROOT / "docs" / "aihot_research"
ENDPOINTS_PATH = RESEARCH_DIR / "endpoints.json"
TGB_VIP_PATH = RESEARCH_DIR / "tgb.json"
XUEQIU_AUTHORS_PATH = RESEARCH_DIR / "xueqiu.json"
THEMES_PATH = RESEARCH_DIR / "dict" / "themes.json"
SENTIMENT_DICT_PATH = RESEARCH_DIR / "dict" / "sentiment_dict.json"
GOLD_SOURCE_PATH = RESEARCH_DIR / "gold" / "gold.jsonl"

# 本地运行产物（.data 已在 .gitignore 中）
DATA_DIR = REPO_ROOT / ".data"
SNAPSHOT_PATH = DATA_DIR / "short-term-radar-snapshot.json"
GOLD_PATH = DATA_DIR / "gold.jsonl"

# 离线样本：测试与 --offline-fixtures 的唯一数据源
FIXTURES_DIR = REPO_ROOT / "bridge" / "tests" / "fixtures"
PIPELINE_FIXTURE = FIXTURES_DIR / "pipeline_sample.json"

# YM-data-pipeline 的 canonical checkout（正式公共入口 `from ym_stock_data import query`）
DEFAULT_PIPELINE_ROOT = Path(
    os.environ.get("YM_PIPELINE_ROOT", "/Users/yimu/Projects/YM_Capital/YM-data-pipeline")
)

# AIHOT 本机实例（SH-01 已把默认端口固定为 3088，避开 live-dashboard 的 8088）
DEFAULT_AIHOT_BASE_URL = os.environ.get("AIHOT_BASE_URL", "http://127.0.0.1:3088")

# 四个信源 id 与 industry/sources.json 严格一致；push 时按此分轨
SOURCE_PIPELINE = "external-ym-pipeline"        # editorial：题材催化与龙头异动战报
SOURCE_TAOGUBA = "external-taoguba-hot"       # editorial：游资复盘与深度博弈帖
SOURCE_XUEQIU = "external-xueqiu-hot"          # editorial：个股深度逻辑拆解
SOURCE_GUBA = "external-eastmoney-guba"        # hot_signal：股吧情绪脉冲，只算热度不算精选

# POST /api/ingest/items 的单批上限（后端 MAX_ITEMS=50，超过返回 413）
INGEST_BATCH_SIZE = 50


@dataclass(frozen=True)
class BridgeConfig:
    """一次运行的全部可调项；默认值即本机开发态。"""

    offline_fixtures: bool = False
    dry_run: bool = True
    push: bool = False
    sync_gold: bool = False
    live_smoke: bool = False
    max_stocks: int = 0  # 0 = 不限；--live-smoke --max-stocks 3 时只取 3 只
    focus_limit: int = 50
    top_resonance_limit: int = 30
    posts_per_stock: int = 50
    aihot_base_url: str = DEFAULT_AIHOT_BASE_URL
    ingest_token: str = ""
    pipeline_root: Path = DEFAULT_PIPELINE_ROOT
    request_timeout: float = 12.0
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    )
    research: dict[str, Path] = field(
        default_factory=lambda: {
            "endpoints": ENDPOINTS_PATH,
            "tgb_vip": TGB_VIP_PATH,
            "xueqiu_authors": XUEQIU_AUTHORS_PATH,
            "themes": THEMES_PATH,
            "sentiment": SENTIMENT_DICT_PATH,
        }
    )

    @property
    def mode(self) -> str:
        return "offline_fixtures" if self.offline_fixtures else "live"

    def resolve_token(self) -> str:
        """推送令牌：命令行 > 环境变量 INGEST_TOKEN。空串表示未配置（dry-run 下允许）。"""
        return self.ingest_token or os.environ.get("INGEST_TOKEN", "")


def load_json(path: Path) -> object:
    """读一个 JSON 文件；不存在或损坏时抛出带路径的错误（不静默吞掉词典）。"""
    import json

    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:  # 词典缺失会让情绪打分悄悄失真，必须显式失败
        raise FileNotFoundError(f"缺少调研资产：{path}（应由 docs/aihot_research 提供）") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"调研资产不是合法 JSON：{path}（{exc}）") from exc
