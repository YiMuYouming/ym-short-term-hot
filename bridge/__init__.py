"""YM-HOT 数据管道桥接：结构化行情 + 三大短线社区靶向采集 → AIHOT 双轨推送。

分层约定（每一层都能单独离线测试，不碰外网）：

- `pipeline_loader`：从 YM-data-pipeline 公共入口取热榜与涨跌停池，与题材词典合成焦点股池；
- `collectors/*`：三社区采集器，**解析是纯函数、HTTP 可注入**，因此测试 100% 走 fixture；
- `sentiment_engine`：零 Token 的反水贴过滤、三类情绪打分与跨平台共振计算；
- `push_to_aihot` / `run_bridge`：双轨转换、雷达快照落盘与 CLI。

硬边界：本包只做「取数 → 判情绪 → 推送」，不做分析、不调付费模型、不写前端页面。
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
