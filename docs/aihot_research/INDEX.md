# aihot_research 目录索引（2026-10-16，台北时间）
## 第一波：社区信息源调研
- `report.md`：总报告（淘股吧 33 人 / 雪球 23 人 / X 28 个账号 / 接口规律），含“补充更新”一节
- `tgb.json`：淘股吧主理人（ID、主页、风格标签、佐证、核实状态）
- `xueqiu.json`：雪球拆解作者（ID、擅长方向、核实状态）
- `x_accounts.json`：X 账号（handle/name/tier/focus，已用 X 接口核实）
- `endpoints.json`：东财股吧 / 淘股吧 / 雪球的 URL 与 JSON 接口实测结果（雪球部分为浏览器实测）
## 第二波：A股超短线词典（`dict/`）
- `dict/themes.json`：28 个题材、74 只代表股（代码和名称已用东财接口核对），附黑话
- `dict/sentiment_dict.json`：三类情绪词（56/53/60 个）+ 14 条垃圾/噪声正则（已自测）
- `dict/README.md`：用法、核实状态、不确定点
## 第三波：精选打分评测集（`gold/`）
- `gold/gold.jsonl`：70 条虚拟评测样本（development 49 / holdout 21）
- `gold/README.md`：分布统计、校验结果、规则核实、难例与每条标注理由
