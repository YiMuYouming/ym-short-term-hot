# gold.jsonl：A股短线精选打分评测集（虚拟样本）
共 70 条，每行一个 JSON，字段严格按 AIHOT 要求的格式。**声明：本数据集全部 70 条都是模拟内容。** 公司名一律用 XX科技(30xxxx) 这类虚构名称，订单、公告、数字也都是虚构的，不对应任何真实公司，不构成投资建议。为了保持真实感，正文和标题里不再放任何“虚拟样本”标记，这条声明只写在 README 里。

## 校验结果（Python）
- 70 行都是合法 JSON；字段集合精确匹配；各字段枚举合法；caseId 唯一；bodyZh 最短 80 字（≥80）。
- 修订（2026-10-16 14:06 后）：第二版里有 12 条正文末尾补了凑字数的声明，这次全部去掉，按各自信源的文风重写扩写（030/036/044/048/050/052/054/056/057/059/060/066）。所有样本的标记也都删掉了；删掉后又有 10 条（012/027/038/042/043/047/049/058/067/068）不足 80 字，同样做了自然扩写。原有信息量和 gold.decision 都没变；短而硬核的 select 难例（043/048/058）只补了导语和过渡句，没有加新论点。
- 划分：development 49 / holdout 21（49/70 = 70%，21/70 = 30%，精确）。holdout 每个类别抽 3 条，判定分布 select 8 / reject 9 / either 4。

## 分布
- 类别：{'theme_catalyst': 10, 'dragon_move': 10, 'company_signal': 10, 'deep_logic': 10, 'youzi_review': 10, 'sentiment_pulse': 10, 'spam_noise': 10}
- 判定：{'select': 25, 'reject': 31, 'either': 14}
- 来源级别：{'T1': 10, 'T2': 36, 'T1_5': 24}
- 划分×判定：{('holdout', 'select'): 8, ('development', 'reject'): 22, ('development', 'select'): 17, ('development', 'either'): 10, ('holdout', 'reject'): 9, ('holdout', 'either'): 4}
- 类别×判定：{'company_signal/either': 2, 'company_signal/reject': 4, 'company_signal/select': 4, 'deep_logic/either': 2, 'deep_logic/reject': 3, 'deep_logic/select': 5, 'dragon_move/either': 2, 'dragon_move/reject': 3, 'dragon_move/select': 5, 'sentiment_pulse/either': 3, 'sentiment_pulse/reject': 4, 'sentiment_pulse/select': 3, 'spam_noise/either': 1, 'spam_noise/reject': 9, 'theme_catalyst/either': 2, 'theme_catalyst/reject': 4, 'theme_catalyst/select': 4, 'youzi_review/either': 2, 'youzi_review/reject': 4, 'youzi_review/select': 4}
- 难例：35/70 = 50%（要求 ≥40%）

## 规则引用核实
异动阈值引用的是《深圳证券交易所交易规则（2026年修订）》（2026-07-06 起施行）第 5.4.3/5.4.4 条：
- 主板连续 3 个交易日收盘价涨跌幅偏离值累计 ±20%、创业板 ±30%，构成异常波动；
- 连续 10 个交易日累计 +100%（-50%）、连续 30 个交易日累计 +200%（-70%），构成严重异常波动；
- 出现严重异常波动时公司要核查，可能停牌核查。

来源：szse.cn 规则原文 PDF。上交所对应条款本次没有逐条核对，样本里没有引用科创板的具体数值。龙虎榜“日涨幅偏离值达 7%”是常见上榜条件，没有逐条核对。

## 难例清单与标注理由
|caseId|类别|划分|判定|理由|
|-|-|-|-|-|
|ashare-002|theme_catalyst|development|reject|标题重磅但无订单/产能/客户任何可验证数据，典型吹票小作文|
|ashare-004|theme_catalyst|development|reject|无来源传闻+情绪喊单，零信息量|
|ashare-005|theme_catalyst|development|either|确认了技术可用性但明确无订单；题材首日可能被炒但信息有限，可选可不选|
|ashare-008|theme_catalyst|development|select|篇幅短但点出政策关键措辞差异和量化影响，高信息密度|
|ashare-009|theme_catalyst|holdout|reject|伪造“官宣”的内幕传闻，可能违法，必须拒绝|
|ashare-011|dragon_move|development|select|短但硬核，引用交易所严重异常波动规则点破连板风险|
|ashare-012|dragon_move|holdout|reject|喊板无依据，纯情绪|
|ashare-015|dragon_move|development|select|短文纠正创业板/主板异动阈值差异，规则准确且实用|
|ashare-016|dragon_move|development|either|情绪脉冲有统计信息量但结论偏弱，可选可不选|
|ashare-018|dragon_move|holdout|reject|庄托套话+确定性承诺|
|ashare-020|dragon_move|development|select|短文点破停牌核查后的交易风险，硬核提醒|
|ashare-021|company_signal|development|select|短但含“认证+批量供货+时间”实锤，select|
|ashare-022|company_signal|holdout|reject|公司套话回复，零信息量|
|ashare-024|company_signal|development|reject|未经证实的“朋友内部消息”|
|ashare-026|company_signal|holdout|select|简短但给出产能、送样对象和验证周期，有价值且诚实|
|ashare-029|company_signal|holdout|either|未否认也未确认，信息模糊，可选可不选|
|ashare-030|company_signal|development|reject|把常规资质认定包装为重大利好|
|ashare-032|deep_logic|development|reject|标题“深度”但全是空泛宏大叙事，无具体数据|
|ashare-035|deep_logic|development|select|虽短但用分部数据指出估值预期差，高价值|
|ashare-036|deep_logic|holdout|reject|堆砌“唯一正宗稀缺”标签无任何论证|
|ashare-039|deep_logic|development|either|汇总分歧有价值但无结论，可选可不选|
|ashare-042|youzi_review|development|reject|推广引流，无复盘内容|
|ashare-043|youzi_review|development|select|短但给出量化观察条件，信息密度高|
|ashare-047|youzi_review|development|reject|空泛口诀+引流|
|ashare-048|youzi_review|holdout|select|短但给出明确周期判断标准|
|ashare-049|youzi_review|holdout|either|有数据但常规罗列，可选可不选|
|ashare-051|sentiment_pulse|development|either|情绪数据有参考价值但结论弱，either|
|ashare-052|sentiment_pulse|development|reject|复读喊板噪声|
|ashare-053|sentiment_pulse|holdout|select|短但给出可回测的量化情绪指标与历史统计|
|ashare-056|sentiment_pulse|development|either|分歧脉冲有意义但信息有限|
|ashare-057|sentiment_pulse|holdout|reject|庄托式套话，无数据|
|ashare-058|sentiment_pulse|holdout|select|短但定量指出亏钱效应扩散|
|ashare-065|spam_noise|holdout|either|表面是模板，但“连板中机构首次净买入”对龙头有信号意义，either|
|ashare-067|spam_noise|development|reject|模板数据+庄托式解读，看似分析实为噪声|
|ashare-069|spam_noise|holdout|reject|形式像公告但内容全是套话|

## 全部样本标注理由
|caseId|类别|划分|判定|难例|标题|理由|
|-|-|-|-|-|-|-|
|ashare-001|theme_catalyst|holdout|select||某部委发布低空空域管理改革试点方案，首批6省份|官方政策+时间表+可映射产业链，题材首日催化信息量高|
|ashare-002|theme_catalyst|development|reject|是|重磅！固态电池即将颠覆一切，这三只票要翻十倍|标题重磅但无订单/产能/客户任何可验证数据，典型吹票小作文|
|ashare-003|theme_catalyst|development|select||海外龙头发布新一代1.6T光模块标准，国内送样窗口提前|海外一手产业事件明确映射A股光模块链，含时间节点|
|ashare-004|theme_catalyst|development|reject|是|商业航天要起飞了！！！|无来源传闻+情绪喊单，零信息量|
|ashare-005|theme_catalyst|development|either|是|XX电子(30xxxx)：公司产品可应用于人形机器人领域|确认了技术可用性但明确无订单；题材首日可能被炒但信息有限，可选可不选|
|ashare-006|theme_catalyst|development|select||国常会部署算电协同，提出新建智算中心绿电比例要求|高层级政策+量化指标，跨电力/算力两大题材|
|ashare-007|theme_catalyst|holdout|reject||今天又是被题材轮动打脸的一天|纯个人情绪吐槽，无催化信息|
|ashare-008|theme_catalyst|development|select|是|短评：这次的政策和上次本质不同|篇幅短但点出政策关键措辞差异和量化影响，高信息密度|
|ashare-009|theme_catalyst|holdout|reject|是|官宣！某巨头将收购本公司！内部消息|伪造“官宣”的内幕传闻，可能违法，必须拒绝|
|ashare-010|theme_catalyst|development|either||多地发布短剧扶持政策，单部最高补贴200万元|政策真实但力度一般，题材持续性存疑，可选可不选|
|ashare-011|dragon_move|development|select|是|提醒：XX传媒(60xxxx)已接近严重异常波动阈值|短但硬核，引用交易所严重异常波动规则点破连板风险|
|ashare-012|dragon_move|holdout|reject|是|龙头还有5个板！！！|喊板无依据，纯情绪|
|ashare-013|dragon_move|development|select||今日连板梯队与晋级率复盘|结构化连板数据+情绪判断，短线高价值|
|ashare-014|dragon_move|development|reject||今天龙头炸板了，好难受|个人亏损求助，无可提炼信息|
|ashare-015|dragon_move|development|select|是|创业板异动阈值提醒|短文纠正创业板/主板异动阈值差异，规则准确且实用|
|ashare-016|dragon_move|development|either|是|【评论汇总】XX传媒吧今日超七成评论喊加速|情绪脉冲有统计信息量但结论偏弱，可选可不选|
|ashare-017|dragon_move|development|select||空间龙断板后首阴反包复盘|具体时点、封单、板块联动，龙头辨识度分析有价值|
|ashare-018|dragon_move|holdout|reject|是|主力已经吸筹完毕明天必涨停|庄托套话+确定性承诺|
|ashare-019|dragon_move|holdout|either||7板龙头今日换手分析|有数据但观点常规，可选可不选|
|ashare-020|dragon_move|development|select|是|停牌核查≠利空出尽|短文点破停牌核查后的交易风险，硬核提醒|
|ashare-021|company_signal|development|select|是|XX精工(00xxxx)：公司已向某全球前三光模块厂商批量供货|短但含“认证+批量供货+时间”实锤，select|
|ashare-022|company_signal|holdout|reject|是|XX股份(60xxxx)：公司高度重视新技术发展|公司套话回复，零信息量|
|ashare-023|company_signal|development|select||XX电子(30xxxx)公告签订3.2亿元算力服务器订单|重大合同，金额占营收比例明确，select|
|ashare-024|company_signal|development|reject|是|公司马上就要和华为签大单了|未经证实的“朋友内部消息”|
|ashare-025|company_signal|development|either||XX科技(68xxxx)股东拟减持不超过2%|常规减持公告，对短线有影响但非重磅，可选可不选|
|ashare-026|company_signal|holdout|select|是|XX材料(30xxxx)：固态电解质中试线已向两家电池厂送样|简短但给出产能、送样对象和验证周期，有价值且诚实|
|ashare-027|company_signal|development|reject||这公司管理层太垃圾了|情绪吐槽，无新增信息|
|ashare-028|company_signal|development|select||XX机械(00xxxx)前三季度净利同比增长186%|业绩高增+驱动因素明确|
|ashare-029|company_signal|holdout|either|是|XX通信(60xxxx)：公司与相关方保持良好合作|未否认也未确认，信息模糊，可选可不选|
|ashare-030|company_signal|development|reject|是|重大利好！公司获得国家级认定！|把常规资质认定包装为重大利好|
|ashare-031|deep_logic|holdout|select||1.6T光模块里TEC用量与供需缺口测算|产业链量化测算，明确假设与局限|
|ashare-032|deep_logic|development|reject|是|深度！一文看懂AI算力十年大周期|标题“深度”但全是空泛宏大叙事，无具体数据|
|ashare-033|deep_logic|holdout|select||人形机器人丝杠环节价值量拆解|单台价值量拆解+瓶颈识别，深度逻辑|
|ashare-034|deep_logic|development|either||关于PCB涨价周期的一点思考|有一定逻辑但缺数据，可选可不选|
|ashare-035|deep_logic|development|select|是|预期差：市场把它当消费电子，其实一半收入已是服务器|虽短但用分部数据指出估值预期差，高价值|
|ashare-036|deep_logic|holdout|reject|是|正宗核心！唯一！稀缺！|堆砌“唯一正宗稀缺”标签无任何论证|
|ashare-037|deep_logic|development|select||存储涨价对模组厂毛利的传导测算|涨价传导机制+节奏判断，实用|
|ashare-038|deep_logic|development|reject||我对这个市场的理解|泛泛心灵鸡汤|
|ashare-039|deep_logic|development|either|是|CPO与可插拔之争：三种机构口径差一个量级|汇总分歧有价值但无结论，可选可不选|
|ashare-040|deep_logic|development|select||商业航天：火箭运力而非卫星才是当前瓶颈|供需测算定位瓶颈环节|
|ashare-041|youzi_review|holdout|select||10.16复盘：退潮末期，等待新周期确认|结构化情绪数据+可执行条件|
|ashare-042|youzi_review|development|reject|是|【红包】关注我，明天带你抓龙头|推广引流，无复盘内容|
|ashare-043|youzi_review|development|select|是|冰点三连后的一个信号|短但给出量化观察条件，信息密度高|
|ashare-044|youzi_review|development|reject||今天大盘又绿了|情绪吐槽|
|ashare-045|youzi_review|development|either||周复盘：主线不明，抱团锂电|常规周复盘，有一定价值但无独到观点|
|ashare-046|youzi_review|development|select||实盘交割单复盘：一进二失败原因|实盘+可复用规则总结|
|ashare-047|youzi_review|development|reject|是|十年游资心法，看懂这篇少亏十年|空泛口诀+引流|
|ashare-048|youzi_review|holdout|select|是|高度板压制4板第三天|短但给出明确周期判断标准|
|ashare-049|youzi_review|holdout|either|是|今日游资龙虎榜动向汇总|有数据但常规罗列，可选可不选|
|ashare-050|youzi_review|development|reject||跟着大神操作亏惨了|个人经历吐槽|
|ashare-051|sentiment_pulse|development|either|是|【评论汇总】光模块吧今日恐慌情绪飙升|情绪数据有参考价值但结论弱，either|
|ashare-052|sentiment_pulse|development|reject|是|还有5个板！还有5个板！|复读喊板噪声|
|ashare-053|sentiment_pulse|holdout|select|是|情绪一致性指标触及阈值|短但给出可回测的量化情绪指标与历史统计|
|ashare-054|sentiment_pulse|development|reject||大家今天赚钱了吗|无信息量闲聊|
|ashare-055|sentiment_pulse|development|select||情绪温度计：涨停家数与连板率双升|结构化情绪指标，高价值|
|ashare-056|sentiment_pulse|development|either|是|【评论汇总】XX智能吧：一边喊“格局”一边问“要不要跑”|分歧脉冲有意义但信息有限|
|ashare-057|sentiment_pulse|holdout|reject|是|散户都在跑，主力在进|庄托式套话，无数据|
|ashare-058|sentiment_pulse|holdout|select|是|注意：高标核按钮扩散|短但定量指出亏钱效应扩散|
|ashare-059|sentiment_pulse|development|reject||今天跌得我想哭|个人情绪宣泄|
|ashare-060|sentiment_pulse|development|either||雪球热股榜一日变动观察|有观察价值但证据有限|
|ashare-061|spam_noise|holdout|reject||XX科技：融资净买入1.2亿元，融资余额15.3亿元|东财自动生成融资融券模板句|
|ashare-062|spam_noise|development|reject||想要明天的涨停票吗？进群免费领|广告引流加群|
|ashare-063|spam_noise|development|reject||XX股份主力资金净流出2.1亿元|资金流向自动模板|
|ashare-064|spam_noise|development|reject||涨涨涨涨涨涨涨涨涨涨涨涨涨|复读灌水|
|ashare-065|spam_noise|holdout|either|是|XX传媒龙虎榜：机构专用席位净买入5000万元|表面是模板，但“连板中机构首次净买入”对龙头有信号意义，either|
|ashare-066|spam_noise|development|reject||万0.8佣金开户，扫码立领|开户广告|
|ashare-067|spam_noise|development|reject|是|XX电子股东户数减少8%，筹码趋于集中|模板数据+庄托式解读，看似分析实为噪声|
|ashare-068|spam_noise|development|reject||转发抽奖！关注+转发送iPhone|抽奖引流|
|ashare-069|spam_noise|holdout|reject|是|XX科技(00xxxx)：关于投资者关系活动记录表|形式像公告但内容全是套话|
|ashare-070|spam_noise|development|reject||XX股份盘中快速拉升，5分钟涨幅超2%|盘口异动自动生成模板|