# A股超短线词典（System 1 规则清洗 / AIHOT industry/taxonomy.ts）
生成时间：2026-10-16 台北时间

## 文件
- `themes.json`：28 个题材，每个有 standard_name、aliases、representative_stocks（code/name/role/nicknames），共 74 只股票。
- `sentiment_dict.json`：一致看多 56 词、分歧博弈 53 词、恐慌看空 60 词（weight 范围 -3~+3，附释义）；垃圾/噪声正则 14 条。

## 核实状态
- **代码与名称**：74/74 用东财 suggest 接口逐一核对一致（科创板 Classify=23 也已确认）。
- **角色（人气老龙/容量中军/20cm弹性）**：主观归类，已标 role_note。注意 20cm 只适用于 300/688 代码；“人气老龙”反映的是 2026-10 社区热度（如新华传媒、九阳股份在淘股吧复盘中高频出现），会过时，要定期更新。
- **黑话**：18 处标注全部在东财股吧标题抽样中出现过（易中天、寒王、宁王、茅子、旭创、胜宏、沪电、东财等）。单字“易”“寒”“北方”误伤高，只建议在对应股吧内使用。
- **抽样**：用 Articlelist 接口（sorttype=0）取 58 个股吧各最新 100 帖，共 7401 条标题。每个情绪词都记了命中数 guba_hits_7401_titles；为 0 的标了“待核实”。
- **正则**：14 条全部用 Python 编译通过并命中自带示例；股吧命中数和样例都写在 JSON 里。融资融券模板句命中 70 次（如“光迅科技：融资净偿还1.42亿元，融资余额33.88亿元”）。

## 用法示例
```python
import json,re
d=json.load(open('sentiment_dict.json'))
spam=[re.compile(p['regex']) for p in d['spam_noise_patterns']]
def score(t):
    if any(r.search(t) for r in spam): return None   # 丢弃
    s=0
    for k in ('extreme_bull_consistent','divergence_gaming','panic_bear_nuke'):
        for w in d[k]:
            if not w['context_dependent'] and w['term'] in t: s+=w['weight']
    return s
```
建议用 Aho-Corasick 做长词优先匹配（“一字跌停”要压过“一字”，“天地板”要压过“地天板”和“跌停”）。题材匹配：aliases 加股票名加 nicknames 都映射到 standard_name。

## 不确定点
- 加微信、加群、老师类正则（ad_contact/ad_group/ad_teacher）和盘口异动模板（tmpl_auto_quote）在本次抽样中命中为 0：东财标题中这类内容可能已被审核过滤，或多出现在正文/评论里，要用正文语料再验证。上一版 ad_contact 把“叠加卫星”误判为广告，已修正。
- 龙虎榜/资金流向正则也会命中普通讨论（如“涨进龙虎榜”），建议和“XX：”开头的格式或数字金额一起判断。
- 情绪权重是主观值，还没用涨跌数据校准；“面”“T”“核”“躺”这类词标了 context_dependent，默认不计分。
- 题材成分股只放了代表股，不是完整成分；各题材龙头会轮动，要按周维护。
