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

## 进度日志（第四~六波）
- 2026-10-16 第四波 seats/ 完成
- 2026-10-16 第五波 jiuyan_cls/ 完成
- 2026-10-16 第六波 global_mapping/ 与 dict/themes_v2.json 完成
- 2026-10-16 18:48 并入第五波浏览器实测结果（jiuyan_cls/fast_news_endpoints.json 增至 27 条、README 追加）；打包 aihot_research_v2.tar.gz

## 第四波：龙虎榜席位（seats/）
- seats/quant_seats.json：27 个量化/外资/PB 席位 + 1 条假机构识别模式
- seats/youzi_seats.json：37 条游资/散户/一日游/交易所类席位
- seats/README.md：识别指南与算法判据
- seats/fetch_lhb.py、fetch_org.py、seat_stats.py、build_seats.py：采集、统计、生成脚本
- seats/lhb_operatedept_1y.json.gz、org_trade_6m.json、stats_operatedept_6m.json、stats_institution_6m.json：原始数据和统计结果
## 第五波：韭研公社与快讯（jiuyan_cls/）
- jiuyan_cls/fast_news_endpoints.json、jiuyan_authors.json、README.md、collect_authors.py、authors_raw.json、probe_log_partial.md
## 第六波：海外映射与题材 v2（global_mapping/、dict/）
- global_mapping/overseas_to_ashare.json、README.md、chains_src.py、extra_src.json
- dict/themes_v2.json、themes_v2_src.py、verify_codes.py、build_v2.py（dict/README.md 已追加说明）
- logs/code_verify_log.json、logs/excluded_codes.json

## 本次新增/修改文件清单（相对路径）
新增：seats/quant_seats.json, seats/youzi_seats.json, seats/README.md, seats/fetch_lhb.py, seats/fetch_org.py, seats/seat_stats.py, seats/build_seats.py, seats/lhb_operatedept_1y.json.gz, seats/org_trade_6m.json, seats/stats_operatedept_6m.json, seats/stats_institution_6m.json, jiuyan_cls/fast_news_endpoints.json, jiuyan_cls/jiuyan_authors.json, jiuyan_cls/README.md, jiuyan_cls/collect_authors.py, jiuyan_cls/authors_raw.json, jiuyan_cls/probe_log_partial.md, global_mapping/overseas_to_ashare.json, global_mapping/README.md, global_mapping/chains_src.py, global_mapping/extra_src.json, dict/themes_v2.json, dict/themes_v2_src.py, dict/verify_codes.py, dict/build_v2.py, logs/code_verify_log.json, logs/excluded_codes.json
修改：INDEX.md, dict/README.md

修改（浏览器结果合并）：jiuyan_cls/fast_news_endpoints.json, jiuyan_cls/README.md, INDEX.md
