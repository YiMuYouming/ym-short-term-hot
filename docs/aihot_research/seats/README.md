# seats/ 龙虎榜席位库（第四波，2026-10-16 台北时间）

## 文件
| 文件 | 内容 |
|-|-|
| quant_seats.json | 28 条：27 个量化/外资/PB 通道席位 + 1 条“机构专用量化假机构”识别模式 |
| youzi_seats.json | 37 条：主观游资 23 条（13 条有社区公认游资名、10 条是数据高活跃席位，用营业部代称）+ 散户大本营 8 + 一日游(数据识别) 3 + 交易所类席位 3 |
| fetch_lhb.py / lhb_operatedept_1y.json.gz | 东财 RPT_OPERATEDEPT_TRADE_DETAILS 近一年（2025-10-16 起）全量 131,091 条营业部明细 |
| fetch_org.py / org_trade_6m.json | 东财 RPT_ORGANIZATION_TRADE_DETAILS 近 6 个月 6,463 条“机构专用”明细 |
| seat_stats.py → stats_operatedept_6m.json / stats_institution_6m.json | 统计脚本和结果（窗口 2026-04-16~2026-10-16） |
| build_seats.py | 由统计结果生成两个 JSON |

## 接口（真实请求验证，HTTP 200）
- `https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_OPERATEDEPT_TRADE_DETAILS&columns=...&filter=(TRADE_DATE>='2025-10-16')&pageSize=500`
  - 字段：OPERATEDEPT_CODE, OPERATEDEPT_NAME, TRADE_DATE, SECURITY_CODE, SECURITY_NAME_ABBR, ACT_BUY, ACT_SELL, NET_AMT, D1/D2/D3/D5/D10_CLOSE_ADJCHRATE。
  - 不支持 like 查询（返回 code 9501），所以只能全量拉取后本地筛选。
- `reportName=RPT_ORGANIZATION_TRADE_DETAILS`（机构专用）：BUY_AMT, SELL_AMT, NET_BUY_AMT, BUY_TIMES, SELL_TIMES, FREECAP(亿), TURNOVERRATE, EXPLANATION, D1_CLOSE_ADJCHRATE。
- 其他可用：RPT_OPERATEDEPT_ACTIVE（营业部活跃度）、RPT_RATEDEPT_RETURNT_RANKING（营业部上榜后 1/2/3/5 日收益排行）、RPT_BILLBOARD_DAILYDETAILS、RPT_DAILYBILLBOARD_DETAILSNEW（个股上榜汇总，EXPLAIN 字段带“1家机构卖出，成功率x%”）。
- RPT_OPERATEDEPT_LIST 不存在（code 9501）。

## 核实口径
- **营业部全称、近一年上榜次数、最后上榜日**：全部来自上述接口实测。2025 年国泰君安与海通合并，现在名称是“国泰海通证券股份有限公司…”，旧名“国泰君安…”已不再出现。
- **游资—席位对应关系**：社区公认，未经官方确认。赵老哥、呼家楼、小鳄鱼、宁波桑田路(旧名)近 6 个月没有统计样本（上榜次数低于 3），score 为 null。
- **量化类型、盘中行为、兑现窗口、反制策略**：均为社区经验/推测，不断言是任何具体私募。
- **next_day_premium_bias.score**：取 clip(净买入记录次日收益均值/3, -1, 1)，是数据推导；playbook 口诀是主观的。

---
# 主观游资 vs 量化席位 vs 假机构：龙虎榜实战识别与次日溢价指南

## 1. 统计事实（近 6 个月）
| 群体（代表席位） | 双向占比 | 双向时 min/max 中位数 | 同日≥3股同板块天数占比 | 买入中位额(万) | 净买入次日均值 | 次日上涨率 |
|-|-|-|-|-|-|-|
| 外资/PB（高盛世纪大道） | 0.49 | 0.705 | 1.00 | 3460 | +0.29% | 48.6% |
| 外资/PB（摩根大通银城中路） | 0.28 | 0.786 | 0.92 | 3378 | -0.09% | 48.1% |
| 主观游资（章盟主·江苏路） | 0.59 | 0.086 | 0.65 | 1853 | +1.36% | 54.8% |
| 主观游资（新一·太平南路） | 0.63 | 0.009 | 0.29 | 3484 | +1.10% | 49.5% |
| 打板类（开源西安西大街） | 0.54 | 0.005 | 0.54 | 3097 | +1.23% | 51.7% |
| 散户（拉萨金融城南环路） | 0.72 | 0.686 | 0.99 | 1002 | -2.11% | 35.9% |

**机构专用**（6463 条）：

| 子集 | 样本数 | 次日均值 | 次日上涨率 |
|-|-|-|-|
| 全部净买入 | 3192 | +0.29% | 48.6% |
| 双向接近（min/max≥0.6） | 2763 | -0.06% | — |
| 纯买（卖出为 0） | 446 | +0.19% | — |
| 创业/科创 + 流通市值<50 亿 + 纯买 2000~4000 万 | 10 | -1.23% | — |
| 同条件，其他金额 | 35 | -6.39% | 25.7% |
| 买入次数≥3 的净买入 | 1281 | +0.44% | — |

“次日机构席位卖出≥80%”只能在次日该股再次上榜时观察到：25 例中有 3 例，只是下界估计。

**结论**：
- “双向”本身区分度不高，因为大部分记录都有一点点反向成交。真正有区分度的是双向时的金额接近度：min/max ≥ 0.5 是外资/PB/散户集合的特征，主观游资和打板类在 0.01~0.09。
- 散户集合也有高接近度，需要再用买入金额小（中位数约 1000 万以下）和次日收益显著为负来区分。

## 2. 实战口诀（主观）
- 外资/PB 席位：不是方向信号，剔除后再看剩余游资结构。
- 一线游资净买入、并且是独食（单席位占买一 50% 以上）：次日均值为正，但高开 5% 以上要防兑现。
- 拉萨系合计净买入占比高：散户接力，次日偏弱（数据：约 -2%）。
- 小市值 20cm 纯买机构专用：样本少，但次日均值为负，按一日游处理。

---
# 如何通过龙虎榜买卖结构，用算法自动区分“真机构 vs 量化假机构”、“格局游资 vs 打板量化”

字段名对应东财接口（O=RPT_ORGANIZATION_TRADE_DETAILS，D=RPT_OPERATEDEPT_TRADE_DETAILS，S=stats_operatedept_6m.json）。

| # | 判据 | 阈值 | 权重 | 字段 | 校准 |
|-|-|-|-|-|-|
| R1 | 双向金额接近 | min(BUY,SELL)/max ≥ 0.6 | 机构侧 -2（偏 T0/调仓，非方向） | O.BUY_AMT, O.SELL_AMT | 统计：次日均值 -0.06%，弱于纯买 +0.19% |
| R2 | 小市值 20cm 纯买 | SECURITY_CODE 前缀 30/68 且 FREECAP<50 且 SELL_AMT=0 | 假机构 +2 | O.FREECAP, O.SECURITY_CODE | 统计：次日均值 -1.23%~-6.39%（样本 45） |
| R3 | 单笔 2000~4000 万 | 2e7≤BUY_AMT≤4e7 且 BUY_TIMES=1 | 假机构 +1 | O.BUY_AMT, O.BUY_TIMES | 经验值（社区说法），本数据仅 10 例 |
| R4 | 多家机构共同买入 | BUY_TIMES≥3 | 真机构 +2 | O.BUY_TIMES | 统计：次日 +0.44%，优于单家 +0.20% |
| R5 | 次日机构专用卖出≥80% | 次日 O.SELL_AMT ≥ 0.8×前日 BUY_AMT | 事后标记假机构 +3 | O 次日记录 | 可观测率低（3/25） |
| R6 | 席位双向接近度 | S.two_way_min_max_ratio p50 ≥ 0.5 | 量化/通道 +2 | D.ACT_BUY, D.ACT_SELL | 外资 0.70~0.79，游资 ≤0.09 |
| R7 | 同日同板块铺开 | S.days_with_ge3_same_board ≥ 0.85 | 量化 +1 | D.TRADE_DATE, SECURITY_CODE | 外资 0.92~1.0，游资 0.29~0.65 |
| R8 | 买入中位额小且次日负 | median_buy_amt_wan<1200 且 next_day_ret_mean<-1 | 散户集合 +3 | S | 拉萨系 -1.4%~-2.1% |
| R9 | 单向大额且集中主板/创业 | ratio p50<0.1 且 median_buy≥1500万 | 主观游资/打板 +2 | S | 江苏路、太平南路、开源西安 |
| R10 | 格局 vs 打板量化：次日是否在卖方 | 次日同席位 ACT_SELL≥0.8×前日 ACT_BUY 的比例 >60% | 打板量化/一日游 +2 | D 次日记录 | 经验值，待用 D 数据回测 |

```python
def classify_seat(s):            # s = stats_operatedept_6m[name]
    r = (s["two_way_min_max_ratio_p25_p50_p75"] or [None, 0, None])[1] or 0
    if s["median_buy_amt_wan"] and s["median_buy_amt_wan"] < 1200 and (s["next_day_ret_mean_pct"] or 0) < -1:
        return "retail_camp"
    if r >= 0.5 and s["days_with_ge3_same_board"] >= 0.85:
        return "quant_or_pb"
    if r < 0.1 and (s["median_buy_amt_wan"] or 0) >= 1500:
        return "youzi_or_limitup_sweep"   # 再用 R10 区分格局 vs 打板量化
    return "unknown"

def institution_score(o, next_day=None):   # o = 一条 RPT_ORGANIZATION_TRADE_DETAILS
    b, s = o["BUY_AMT"] or 0, o["SELL_AMT"] or 0
    fake = 0
    if b and s and min(b, s) / max(b, s) >= 0.6: fake -= 2          # 调仓/T0，非方向
    if o["SECURITY_CODE"][:2] in ("30", "68") and (o["FREECAP"] or 999) < 50 and s == 0: fake += 2
    if 2e7 <= b <= 4e7 and o["BUY_TIMES"] == 1: fake += 1
    if (o["BUY_TIMES"] or 0) >= 3: fake -= 2
    if next_day and (next_day["SELL_AMT"] or 0) >= 0.8 * b: fake += 3
    return "fake_institution" if fake >= 3 else "real_institution" if fake <= -2 else "uncertain"
```

**局限**：
- 同板块是按交易所板块近似的，没有按行业。原计划接东财 push2 行业字段，但批量请求返回 502，未完成。
- R3、R10 的阈值是经验值，还需要回测。
- 所有统计只覆盖上榜样本，存在选择偏差。
