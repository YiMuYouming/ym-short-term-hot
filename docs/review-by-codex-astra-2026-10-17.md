# V2 极简重构实际回读与优化评审

评审日期：2026-10-17。评审者：Codex 独立评审。范围：热门板块 ⇄ 热门股 Top 50、共用个股详情，以及支撑它们的 Python → JSON → TypeScript 链路。本次只交付报告，未修改业务代码、快照、配置和既有证据，未调用行情/社区服务、模型或推送接口。

**结论：双视角与共用抽屉的产品方向成立，但目前更接近“有真实数据的原型”，尚不宜把既有 PASS 理解为数据语义与日常看盘体验均已验收。** 最需要解决的不是增加卡片，而是缺失值被显示成事实、题材/事件混为板块、社区字段在序列化时丢失，以及截图、测试、当前运行快照不是同一批数据。优先修正这些，再压缩列表与抽屉的阅读成本。

## 0. 实际回读范围与证据基线

本轮完成三轮交叉回读：

1. 读取项目 `AGENTS.md`、`PROGRESS.md` 的当前摘要/队列/归档索引、V2 实施计划、LITE-01 与 LITE-02 开工单；对照两个阶段的 manifest，区分约定目标与实际交付。
2. 读取指定六个 bridge 文件、`contracts.ts`、`server.ts`，解析三个现存快照并统计字段；对 `mapSnapshot` 和情绪规则执行不联网、不落盘的最小探针。
3. 实际打开四张 PNG：`radar-view1-themes.png`、`radar-view2-stocks.png`、`radar-drawer-detail.png`、`radar-drawer-comments.png`，逐一与 `radar-route.tsx`、`app.css`、`home.tsx` 对照；补读 `useModal` 与现有测试，检查静态截图不能证明的交互。

### 0.1 三份 JSON 不是同一份运行证据

| 文件 | mode / generatedAt | 股池 / 榜单 / 板块 | SHA-256 |
| --- | --- | --- | --- |
| `docs/evidence/lite01-20261017/short-term-radar-snapshot.json` | live / 2026-10-17 11:09:26.718596 +08:00 | 50 / 50 / 115 | `b63038004633f25e4656055f8ee2c584d99157a8329e5cc31032003f42c2e673` |
| `.data/short-term-radar-snapshot.json` | offline_fixtures / 2026-10-17 14:14:10.203939 +08:00 | 50 / 30 / 23 | `ed100bbb18610101ab5996d5d9ae3e83389cb9b27e6608824fe166f187ca68af` |
| `docs/evidence/lite02-20261017/short-term-radar-snapshot.json` | offline_fixtures / 2026-10-17 12:32:24.609371 +08:00 | 50 / 30 / 23 | `4fe7e2c103987b6900b61de2876eee7257d670cf41783f0534850cb356d71f55` |

四张图片均为 2880×1840 像素，文件时间为 14:16；画面显示“实时 / 快照 11:09 / 共 50 只”，与 LITE-01 真实快照的股票、板块和帖子吻合，而非同目录 LITE-02 离线 JSON。图片没有附带浏览器视口/DPR/快照 SHA 关联记录，因此这里确认的是图像内容对应关系，不能认定已证明截图采集流程或当前服务器仍使用该批次。

**后文“真实批次”均专指 LITE-01 保存的 live JSON。** 其中市场交易日是 `20261016`；热榜和原因数据截至 10-16 15:00，盘中池截至 15:34:30。它是 10-17 生成的上一交易日数据，不能因 mode=live 就称为实时行情。本评审引用股票、新闻和帖子仅为检查本地产物，不对其中市场叙述作外部事实背书。

### 0.2 本轮量化结果

| 指标 | 真实批次结果 | 含义 |
| --- | --- | --- |
| 非空 whyHot / limitReason | 48/50、47/50 | 非空不等于有催化解释 |
| whyHot 类型 | 7 条较详细来源文本、23 条首板+涨停原因、14 条概念拼接、3 条词典题材归属、1 条只有首板、2 条空 | 前者识别口径为包含“行业原因”或换行“1、”；不能将 48 条都称为详细原因 |
| themes 非空 | 47/50 | “未归题材 0”隐藏了 3 只无归属股票 |
| 板块与成员 | 115 组、154 个股票—板块关系；96 组只有 1 只 | 单股板块占 83.5%，平均每只股票 3.08 个归属 |
| 单股 themes 数量 | 0/1/2/3/4/5/6 个分别为 3/3/6/22/10/3/3 只 | 多概念扩散而非少数有层次的主线 |
| boardCount | 29 只为 1；1 只为 3；1 只为 4；19 只为 0 | 0 的语义不可靠，见 A1 |
| sealTime / amountYi | 0/50、31/50 非空 | 31 只已记录板数，仍全无封板时间 |
| highlights | 47 只有条目，共 128 条，全部东财股吧 | 不是三社区精选覆盖 |
| highlights 字段 | 每条只有 platform/title/authorName/isVipYouzi/isDeepLogic/commentCount/url 七项 | 时间、正文、点赞、阅读、情绪与原始 ID 均未持久化 |
| 情绪样本 | total 364、valid 324、spam 40；方向样本 88（多62/空19/分歧7） | 236 条非水贴没有方向判断；40/364≈11.0% 是规则拦截率，非准确率 |
| 情绪标签 | 中性33、亢奋14、恐慌3；全部 posts15m=0 | 不能据此断言盘中讨论冷却 |
| 有效社区覆盖 | 49 只仅东财股吧，1 只无有效平台 | 雪球热榜名次存在，不代表雪球评论可用 |

## A. 实际数据问题：现象、根因与影响

### A1. 缺失封板/连板信息被转换成确定的否定事实（P0）

**直接证据：** 冰山冷热 `000530`，`boardCount=4`、`changePct=9.96`、`sealTime=""`；新华文轩 `601811`，`boardCount=3` 同样没有封板时间。详情截图中冰山冷热上方是“4 连板”，下方却是“封板时间：未封板/非涨停”。这不是数据源证明它没封板，而是 `StockDrawer` 第 467 行把任何空字符串写成了“未封板/非涨停”。

`FocusStock.board_count` 默认 0，`build_focus_pool.new_entry` 默认 0，读池失败/未覆盖也保持 0；抽屉再把 0 写成“未连板”。莱美药业 `300006` 的快照涨幅为 +19.93%、boardCount=0，仅有 ths/dc 来源，其高亮报道提及“五天三板”。不能从这条报道推导连续板数，也不能用涨幅证明封板，但当前“未连板”同样缺证据。`intraday.status=degraded` 且 61 行有数据，不能简单作全有/全无判断。

**改法：** 将“池成员身份”“连续涨停数量”“封板时间”拆开。缺失为 null；保留 `limitStatus=sealed|open|not_limit|unknown` 和字段质量。31 只池内股在时间缺失时显示“涨停池在列 · 封板时间未提供”；未覆盖股票显示“连板数据待补”，不能从报价阈值补板数。首板显示“首板”，而非机械的“1 连板”。

### A2. 115 个板块包含别名重复、产业层级和事件碎片（P0/P1）

`_merge_themes` 把词典归属、legacy reason 拆词、ths concept 混进同一个字符串数组；未命中字典就创建独立板块。LITE-01 明确允许保留原始概念，这是当前设计债，不能归咎于执行者偏离开工单。

真实例子：

| 样例 | 快照中可复核的表现 | 建议处理 |
| --- | --- | --- |
| CPO | “光模块/CPO”和“共封装光学(CPO)”成员完全相同：300394、300308、300502 | 主导航合并到同一稳定 ID，原概念保留作 alias/subtheme |
| 低空 | “低空经济/eVTOL”有16只；江淮汽车单独落在“飞行汽车(eVTOL)” | 该写法补别名；是否将江淮归当前主线仍需来源与日期，不靠同名推导当前催化 |
| PCB | “PCB/覆铜板”含沪电股份、生益科技；“PCB概念”又单列沪电股份 | 层级或别名归一，避免两次主导航入口 |
| 黄金 | “黄金/有色”和“黄金概念”均只有紫金矿业 | 归一呈现，同时保留“有色”与“黄金”上下位关系 |
| 冰山冷热 | 六个标签：冰雪工程、数据中心液冷、军工、冷热设备、冰雪产业、体育产业 | 当前催化/业务属性分开；冰雪工程与产业建立父子关系，不抹去液冷这条独立业务线 |
| 江淮汽车 | “三部门联合调查”“尊界V800”成为各一只股票的板块 | 前者是事件，后者是车型/产品，放入 catalystTags/productTags，不作为平级行业板块 |
| 新华传媒 | 传媒/AI短剧/影视、复牌、界面财联社重组、图书发行、AI语料、文化传媒概念 | “复牌”“重组”是事件；文化传媒合并；AI语料可保留次级概念 |
| 甘化科工 | 军工电源、光电成像、特种合金、参股锴威特半导体均被开成单股板块 | 最后一个是股权关系，其余用产业层级组织 |

不能把“机器人”“人形机器人”“工业机器人”一律合并：当前 `ThemeCatalog.normalize_theme("机器人")` 实际返回“人形机器人”，已存在从泛类缩窄到子类的问题。`无人机` 当前也直接归到“低空经济/eVTOL”，军事无人机不必然属于 eVTOL。应区分严格同义词、父子类、关联概念三个关系，机器只做明确 alias 的等价折叠。

题材顺序还有一个隐患：词典 `lookup(code)["themes"]` 是 set，`_merge_themes` 先将它转 list。主标签没有明确优先级，跨进程顺序可能变化；前端 `slice(0,3)` 恰好用此顺序决定哪些标签露出。应以当日归因优先、静态归属其次、稳定 ID 最后作为明确排序。

### A3. 板块涨停数的口径混用，别名计数直接相加不能证明去重家数（P0）

低空经济视图显示“16 只热门股 / 涨停16家 / 同花顺涨停原因统计17家”。后一个 17 来自 `build_theme_ladders` 将 `低空经济=11`、`飞行汽车=5`、`无人机=1` 相加。类似地，人形机器人为 `机器人=5 + 人形机器人=3 = 8`。

这些原始标签集合可能重叠。快照只保存汇总计数，无法证明相加后的 17/8 是互斥股票数。**本评审不认定实际重复了几只；认定的是代码把未去重的标签计数和标成“家”的唯一股票数混用了。** 而 `sealedCount` 只数焦点池成员，不是市场板块涨停全量；板块排序又优先取这个原始标签累计值，API `heatScore` 却重新定义为共振分之和，排序口径与字段含义不一致。

改法：`focusStockCount`、`focusLimitUpCount`、`marketLimitUpCount`、`sourceReasonCounts` 分离。市场家数只在有逐股成员集、相同交易日和覆盖证明时按代码去重；只有计数时保留原标签统计，不宣称合并家数。排序键显式输出 `rank/rankBasis`，UI 用“池内涨停”而非无范围限定的“涨停”。

### A4. “未归题材 0”不是全股覆盖，“为什么火非空”不是解释质量（P0/P1）

捷众科技 `920690`：themes=[]、limitReason空、whyHot仅“首板涨停”；广联航空 `300900`、泓博医药 `301230`：themes=[]、whyHot与limitReason均空。`build_theme_ladders` 直接跳过空 themes，所以板块里没有“未归题材”条目，但 3/50 股票仍失去板块入口。应以 `unassignedStockCount=3` 报告覆盖，而非用占位标签消失证明归属完成。

中际旭创 whyHot 仅“热门概念：共封装光学(CPO)+F5G概念”；药明康德仅“热门概念：CRO概念+创新药”；生益科技仅“题材归属：PCB/覆铜板”。这能说明关联领域，不能回答该批次“因什么事件而热”。生益科技高亮包含预增报道，值得作为候选证据，但不可自动把社区标题升格为核实的公告原因。

建议 `reason.kind=rank_reason|limit_reason|concept_only|taxonomy_only|missing`，列表按层级显示“上榜原因 / 涨停归因 / 关联概念 / 静态归属 / 原因待补”；详细正文保留原文出处和时间。不要继续把概念标签全部命名为 limitReason，更不能用 LLM 生成看似确定的当日原因来填空。

### A5. 三社区采集、归股与精选使用了不同链路（P0）

真实批次 128 条 highlights 全部是东财股吧；有效情绪样本的平台也只有东财。dataQuality 记录10条雪球失败样例，`run` 实际只保留 `failures[:10]`，所以“记录10条”不等于总共只失败10次；缺少总失败数和逐平台 coverage。

`run` 先用 `StockMatcher.group` 把帖子归股，再传给 `apply_to_stocks` 计算情绪；但 `build_snapshot` 重新遍历原始 `posts_by_platform`，仅接受 `post.code` 非空的帖子。**通过股票名/别名匹配而没有显式 code 的帖子可能参与情绪，却永远无法进入 highlights。** 本批次淘股吧 planned=20 仅证明推送计划有20条，不证明这20条命中本池；不能据此宣称遗漏了20条个股精选。结构缺陷成立，实际丢失规模需保存匹配中间结果后验证。

修复时共用一个 `postsByStock` 归属结果，保留 `matchMethod=explicit|name|alias` 和相关性依据。帖子按 `platform+postId` 去重；组合别名允许一帖多股，但各股统计与全局去重口径分开。平台 Tab 展示当前实际可读数和采集状态：无样本、请求失败、候选未通过质量筛选是三种不同空态。不可为了“每个平台都有”插入低质量或无关帖。

### A6. 高亮帖子字段严重裁剪，导致所有卡片假性“中性”（P0）

`CommunityPost` 已有 published_at/content/like_count/view_count/sentiment/sentiment_terms/post_id；`push_to_aihot.build_snapshot.highlights()` 只输出七个字段。`mapHighlight` 又将 excerpt=title、likeCount/readCount=0、无 sentiment 默认 neutral；`HighlightCard` 根本没有渲染 publishedAt。

截图中的冰山冷热评论“下周连续五个一字跌停。”标“中性”。本轮以同一标题调用现有 `score_post`，返回 `panic_bear_nuke`、命中“一字跌停”、分值 -3。说明至少这一处无需换模型即可修复：保留引擎结果即可。当前 JSON 没有帖子原始正文，不能把本轮标题探针当成历史完整帖子评分的复原。

应一次补通 Python 序列化 → FileHighlight → RadarHighlightPost → HighlightCard：原始 postId、时间、摘要、互动分量、情绪及命中词。没有评分是 unknown/未判定；不能标为 neutral/中性。点赞/阅读未知保留 null，不制造0。

### A7. 过滤广告不等于筛出了有价值的信息（P1）

真实精选中的反例包括：甘化科工“厉害”（4评论）；佳力奇“知行合一｜坚持分散风控，做好交易的落袋与守候”（19评论）、“慕晴实盘日记（关注每日更新）”（1评论）；旭升集团“这也能买到吗？”（9评论）。它们未必是垃圾或广告，但并不自动满足“高价值个股逻辑”的定位。英搏尔精选里“000420，午后直线涨停！A股这一概念，异动拉升！”主要点名另一只股票，可作为题材关联信息，不能不加说明地当作本股逻辑。

生益科技三个卡片分别为预增报道、预增公告标题和同事件盘后汇总，均来自资讯账户；这比无聊灌水有用，但占满三个槽位造成同事件重复。`highlights` 目前仅按 comment_count+like_count 排序取3条，没有正文/相关性/时效/事件重复/平台覆盖约束。

建议两道门：spam 只处理广告、引流、明显污染；quality 再按个股相关性、具体事实密度、可追溯出处、时间、事件新颖度筛选。高互动可作为加分，不能代替质量。默认提供“事件事实 + 有依据的不同观点”候选，允许少于3条；情绪喊话可在“更多讨论”保留，不强行删除观点或凑齐三平台。没有原始全量帖子与人工标签，本轮不能测算 spam precision/recall。

### A8. 情绪规则和统计展示会夸大小样本结论（P0/P1）

江淮汽车 validPosts=14，但只有2条方向帖，2/2看多被标“一致亢奋”；英搏尔 validPosts=2、方向2条，也显示整条纯红。冰山冷热80%实际为4/5，不是8条有效帖中的80%。UI 只提供“有效帖”，没有解释分母，容易把标题词典判断看成群体一致意见。

更直接的问题：对冰山冷热标题“我认为周一冰山无法继续涨停……”执行现有标题评分，得到 extreme_bull_consistent、命中“涨停”、+2。当前 `_longest_matches` 只有少量上下文配对，没有针对“无法继续/不会/不可能/别追”等句内否定处理。此探针证明规则缺陷，不证明历史总分应改成具体哪一个数。

兆易创新实际有1条分歧、1条看空，比例50/50、label=情绪中性；前端 `SentimentBar` 因 label 为中性直接隐藏整条比例，并写“方向样本不足”。这将“未达55%主导阈值”“方向不足”“真正中性”混成一个状态。广联航空1多1空也是同类问题。

改法：保存 directedPosts、neutralPosts、coverageRatio、labelReason、windowStart/windowEnd；比例显示“方向帖2/有效14，样本有限”，未判定也可见。小样本先使用“样本偏多/偏空”等克制标签。句内否定/引用/转述作为规则单测，再以金标集评估阈值，不能简单全局翻转一整篇长文。不要把负面观点当水贴过滤。

### A9. 榜单不是全候选集合的共振 Top 50（P1）

`build_focus_pool` 先按 ROLE_ORDER、ths名次、dc名次排序并截断50；后续才采集社区、计算共振、再次按共振排序。因此实际是“身位优先筛选的50只焦点股内部排名”，不能等同于热榜并集的全市场共振前50。静态词典 role 也参与优先级：天孚通信 -4.72%、中文在线 -4.43% 仍标20cm弹性；传媒板块截图甚至把 -3.67%的芒果超媒写成“领涨”。`leaderStock` 取的是身位+共振，并没有按涨幅选领涨。

当前先将文案改“代表股”“综合关注榜（候选池内）”，再明确入池策略。若要真正联合榜，先基于可用热榜排名融合产生候选、明确预算后采集，再排序；不建议为补排行无限扩张爬取。保留 `selectionBasis/rankScope/rankingVersion`。`_rank_decay` 对所有≥20名给同样0.25（注释却说之后不再加分），区分度不足且有大量并列，应明确分段与稳定 tie-break。榜单排名不能作为买入信号。

### A10. 映射、缓存和写入仍有可复现的数据工程缺陷（P0/P1）

- `mapStock` 用 `num(null)=0`：真实中际旭创 amountYi=null 映射为0；缺失 changePct 也变成0.00%。金额UI暂时用“—”遮住0，API仍丢失未知语义。
- `mapSnapshot` 对未进 top 的 ladder entry 仅逐项补少数字段，没有展开完整 entry，遗漏 changePct/amountYi/排名/nicknames 等。本轮构造仅有梯队的股票 changePct=3.14、amountYi=2.7，映射后均变0；这是可执行复现，不只是风险猜测。当前默认配置 top=30、pool=50，使这条路径现实存在；live top=50 恰好遮住它。
- `build_theme_ladders` 只存 FocusStock，不存情绪/精选；top以外股票就算修好价量映射，也仍拿不到社区详情。不能仅靠 `...entry` 修完后宣布闭环。
- `server.send` 的 ETag 是 URL前缀+JSON字符串长度。同一个URL下同长度的数值更新可以得到相同ETag、错误304。应使用内容hash或可靠 revision；这里只做源码推导，未对运行服务发请求。
- `write_snapshot` 直接 write_text，`run` 一轮写两遍。读取恰逢截断/半写时会被 `loadRadarSnapshot` 捕获并退成200空快照，还带60秒缓存；这是源码级竞态风险，本轮未制造故障。应同目录临时文件完整写入后原子替换，缺文件/坏JSON/未知schema分开记状态，保留最后有效快照并明确 stale。
- 成交额按 `>1e6` 猜单位，不等于明确的元/万元/亿元契约；后续按公共管道字段定义转换，测试边界数量级，不能用数值大小猜单位。

## B. 数据结构与契约的最小可持续改造

### B1. 分两步，避免一次重写所有消费者

第一步保持旧字段可读，补 nullable、quality、原因类型、社区元数据，修map与文案。第二步引入版本化实体结构，旧快照由 adapter 读取，前端只消费统一形状。不要让 packages/backend 理解短线题材；业务契约与适配仍放 `modules/short-term-radar/`，Python生产端仍在bridge。

下表是目标契约建议，不表示当前已经存在：

| 对象 | 最小字段 | 设计目的 |
| --- | --- | --- |
| Snapshot | schemaVersion、revision、generatedAt、tradeDate、dataAsOf、mode、quality、stocksByCode、themeGroups、ranking | 生成时间/市场时间/模式分离；唯一实体避免复制漂移 |
| Stock | code、exchange、name、nicknames、quote、limit、reason、themeRefs、ranks、community | 身份、行情、解释、讨论各有明确来源 |
| Quote | changePct:number\|null、amountYi:number\|null、asOf、source | null不变0；金额单位写进契约 |
| Limit | status、boardCount:number\|null、sealTime:string\|null、asOf、source、missingReason | 非涨停/未覆盖/时间未提供分开；不以涨幅估封板 |
| Reason | kind、summary、body、source、asOf、sourceUrl?、evidenceStatus | 概念兜底不伪装成当天因果；不编造原始链接 |
| ThemeRef | id、label、relation、origin、isPrimary、asOf | 区分同义/父子/关联，动态原因与静态归属分开 |
| ThemeGroup | id、label、memberCodes、rank、rankBasis、focusStockCount、focusLimitUpCount、marketLimitUpCount:null或number | 家数范围和排序可解释，无需解析summary字符串 |
| Community | sampledPosts、validPosts、spamPosts、directedPosts、neutralPosts、counts、labelReason、window、platformCoverage、highlightIds | 分母、时窗、样本覆盖都可读 |
| Post | id、platform、url、title、excerpt、author、publishedAt:null或string、engagement、sentiment、matchedTerms、qualityReason、matchedStocks | 只保留展示必需内容；未知与0分开；相关性可追溯 |

`engagement` 保留 reply/like/read三项，避免跨平台混成一个未经校准的“热度”。`sentiment` 至少区分 unknown、neutral、bull、bear、divergence。来源质量不要为每个数值铺复杂对象：quote、limit、reason块级元数据足够，个别异常用missingFields列举。

真实批次股票对象在top中出现50次、梯队中再出现154次，共204份对象。归一为 stocksByCode+memberCodes 能减少正文重复，修复同股不同视图事实漂移。平台帖子也按ID存一份；详情接口已有 `/radar/stock/:code`，P2可让列表只拿短摘要、打开抽屉再取详情，无需新建通用后台层。

### B2. 字段精简与保留原则

- `code` 用唯一规范值，symbol/bareCode可在一个边界派生，避免三套互相修正。
- `roleLabel` 作为附属描述保留给旧agent兼容，不再决定前台“领涨”和入池。静态role与当日board不可互相代替。
- turnoverRate/kplTag当前没有来源，不再用0/空串假装测量成功；未消费则从页面DTO移除，有消费者则nullable兼容迁移。
- `summary` 是展示文案，不能当统计容器；reasonStats原始值留诊断区，不继续混进板块“家数”。
- 原始reason/concept保留供回溯，不用名字字符串拼接承担主键、归类、因果和导航四种职责。
- `dataQuality.httpFailures` 面向用户只显示结构化平台状态；错误样例留诊断记录，记录total/truncated，避免样例数被当总数。提供每源asOf和missingFields。
- 只对明确别名做全角括号、空格、大小写等规范化；未知词先归为rawTag，不能无条件升级为一级板块，也不能删除原始证据。

### B3. 排名与社区选择的一致流水线

建议顺序：公共管道读取并保留元数据 → 统一交易日/单位 → 构建候选与选择依据 → 归一主题及事件标签 → 采集/归股/去重 → spam过滤 → 方向评分与quality评分分开 → 生成逐股摘要及各平台合格候选 → 排名/板块引用 → 校验不变量 → 原子发布快照。

关键不变量：所有memberCodes可解析；所有数值有限且单位明确；旧时间不冒充当前；unknown不转0；合并后市场家数必须可回溯唯一股票集；一只股票从板块/榜单/详情进入得到相同事实；帖子时间未知时不会用采集时间伪装发布时间。`community_item` 当前以批次时间兜底缺失发表时间，虽本次未推送，也应在后续契约整改保留 publishedAt 与 collectedAt 的区别。

## C. 视觉与看盘交互：基于四张真实截图

### C1. 页面入口与整体层级

优点：涨红跌绿清楚；两个核心Tab易理解；同一抽屉避免往返；股票/代码有识别层次，现有主题token可继续使用。问题是左侧仍有精选、全部、热点榜、日报、主题、收藏及更多导航，主看盘动作处于旧资讯站第七个入口；`home.tsx` 仍渲染Timeline，未成为雷达首页。LITE-02 manifest诚实记录未做，但V2总目标“打开即看盘”仍未完成。

建议通过 `site/` 身份/导航配置确定默认入口，`home.tsx` 对纯首页进雷达，原资讯入口保留独立路由，并单独处理旧搜索参数兼容。不要全局删除框架通用资讯功能，也不要因旧首页测试断言就长期保留产品目标偏差。

页头由“实时 + 快照生成时间 + 三个成功徽章”改成一条可扫读的信息：“10-16 收盘数据 · 10-17 11:09 更新 · 封板时间缺失”；点击展开逐源状态。休市最近交易日数据可以正常用于复盘，重要的是标签准确。legacy来源和社区失败应纳入状态，不必常驻一排工程字段。

### C2. 热门板块视角

截图一左侧每行三层文字、右侧每只股圆角卡片+标签+说明+全宽情绪条，首屏只露出约8只股；低空16只需明显下滚。115个板块在一个窄滚动区中寻找，单靠“按热度排序”无法快速定位熟悉主线。

具体改法：

1. 先治理主题结构，再把默认主线控制为热度前若干组（例如12～20组，作为可调展示数），其余通过“全部板块/本地检索”访问。不是从数据删除弱主题。是否恢复轻量检索属于新迭代：上阶段砍搜索是明确选择，不应假装它已是原需求。
2. `ThemePicker` 每行主名称+池内热股数，第二行只保留池内涨停/最高已知板数；代表股可只显示选中项。选中状态增加左边线/字重，不只依赖浅青背景。
3. `ThemeStockRow` 改两行紧凑行，目标桌面约56～64 CSS px：第一行名称、代码、涨幅、首板/连板；第二行一条当前原因和社区“方向帖n/采样n”。成交额和封板时间可放固定列或详情，不堆在名称后。
4. 去掉全宽灰色情绪进度条。它在零方向样本时占空间，在英搏尔2条看多时却产生强烈“满格”视觉。情绪可作为右侧80～96px微条+数字，样本不足仅写“样本少”。
5. `leaderStock` 现算法改名 representativeStock/代表股；若另做领涨，严格按同时间、有效changePct取最大，列出排序依据。截图里“领涨 芒果超媒 -3.67%”不能继续沿用。
6. 主次布局保持约220～250px导航+剩余股票列表；内外层取消重复背景与双重卡片边框，行分隔线足够。保留独立导航滚动，但补 overscroll-behavior:contain，选中项自动滚入可见范围。

### C3. Top 50 表格

截图二总体比卡片清晰，但“所属板块”占了大段横向面积，内容与“为什么火”重复；排名列还承载两行10px小字ths/dc；别名徽章抢占股票辨识空间。当前table为auto布局、min-width:880px，原因列只有max-width:280px，没有行数限制。内容更长或视口更窄时，行高/列宽会由文本挤压，截图当前未严重截断不能证明所有宽度正常。

建议固定主要列尺寸（示意，不是本轮已测定最优值）：排名56、股票168、涨幅/板数112、主线176、原因剩余宽度、讨论112；约960px表格起点。`table-layout:fixed`+colgroup；原因摘要最多2行，展开全文通过抽屉，不依赖hover title。主线只露主标签+1个次标签，剩余“+N”；别名最多一个弱文本，其余详情可见。ths/dc排名在股票第二行合并为“同花顺20 / 东财35”，同时保留完整accessible名称。

表头固定、股票列在窄屏横滚时固定；数值右对齐并继续使用tabular-nums。至少支持“综合关注/同花顺/东财”排序，清楚区分来源榜和融合榜；排序后抽屉上下只沿当前可见列表移动。表格标题用实际数量 `Top {length}`，当前30行不再标Top50。50行不需要先引入虚拟列表依赖。

### C4. 共用个股详情抽屉

截图三中冰山冷热长文占据绝大部分首屏；硬数据网格在其下，社区评论要滚到截图四才看到。当前正文整个段落使用font-medium且混合标题、编号、首行标签；同一标签串又以“一句话原因”重复一次。460 CSS px最大宽度下长文本更显拥挤。评论没有时间、摘要，统一“中性”，平台Tab不能传达实际可读数。

建议顺序：股票头（名称/涨幅/数据日期）→ 一行关键事实（已知板数/成交额/封板时间状态）→ 2～3行摘要 → “展开来源全文” → 社区评价。行业/公司原因按来源原有结构分段，正文14px/1.65、正常字重，标题加粗即可。保留全文而非丢弃，用可访问的details/summary折叠，不让全文挡住所有讨论。大屏抽屉可用 `width:min(100vw,560px)`；具体宽度须后续用真实截图复验。

评论卡顶部为平台、时间、内容类型（公告转述/观点/复盘）；未知时间明确“时间未提供”。正文摘要3行、原帖链接、评论/点赞等真实互动，不显示伪0。方向标签未评分就不冒充中性。平台Tab显示可读条目数量，失败时解释缺口；先按平台保留合格候选再过滤，不能先全局取3条后期待每个平台都有内容。

`StockDrawer` 的platform state不会随stock变化重置；用户在A股选雪球后打开只有东财的B股，会误以为B无评论。切换股票时归“全部”或显式保留并提示所选过滤，两者应作产品决定并测试。补“上一只/下一只”，沿当前列表、到边界禁用；保持板块选择和主列表滚动位置。

### C5. 响应式、键盘与样式细节

四张现有截图仅证明同一大尺寸浅色场景，**没有手机、深色、200%缩放或键盘操作的实际验收证据**。以下依据源码提出：

- 小屏当前板块选择仍占最多300px高度，之后才出现股票；用当前主线选择按钮打开可搜索列表sheet，关闭后直接回股票。不能将115个主题都改成横向chips。
- 小屏表格880px最小宽度会横滚；优先“股票+涨幅+原因”的紧凑行，来源名次/讨论在次行。若保留表格，固定股票列并提供可见滚动提示。
- 抽屉用100dvh、安全区bottom padding、固定头+单内容滚动区；遵循961px的项目lg断点，避免只按默认1024设布局。
- `StockTable` 当前点击绑定在tr，tr不可键盘聚焦；加入真正的股票详情button/link作为焦点入口，保留板块button，避免整行嵌套button。Enter/Space打开，Esc由现有useModal处理。
- 已核对useModal：有Esc、Tab圈定、滚动锁与焦点恢复；不应把这些已存在能力列为缺失。需要补的是可聚焦的行入口，以及背景对辅助技术的隔离验收；本轮未实际做屏幕阅读器测试。
- URL update统一replace，使浏览器后退不能还原逐次开/关抽屉；打开股票可push、关闭按来源安全回退，快速筛选replace。直接深链接进入时关闭不能误退离站。
- 可提供1/2切视角、上下选股等可选快捷键，但输入框、弹层内按钮及组合键场景不劫持；显示快捷键帮助。非必要不增加复杂命令面板。
- `SentimentBar` 需文字描述和可访问标签，颜色不承担全部语义；成功状态和下跌都用了ok绿色，建议在雷达局部建立up/down/status token别名，保留A股红涨绿跌，避免全站改色。
- `app.css` 未定义 `--page-max-board`，而RadarRoute使用它；补模块局部最大宽度变量或引用已有明确token，不让声明失效。`Presence` 使用fadeIn/fadeOut，但已读CSS定义的是aihot-fade-in/out；复用已有anim-fade-in/out，并保留prefers-reduced-motion支持。

可落地的局部CSS方向（仅示意；建议放模块web目录的样式文件并由路由导入，不把短线特例扩散到全站）：

```css
.radar-shell { --radar-max: 1440px; max-width: var(--radar-max); margin-inline: auto; }
.radar-table { table-layout: fixed; width: 100%; min-width: 960px; }
.radar-table th { position: sticky; top: var(--bar-h); background: var(--surface); }
.radar-reason { display: -webkit-box; -webkit-box-orient: vertical;
  -webkit-line-clamp: 2; overflow: hidden; overflow-wrap: anywhere; }
.radar-picker { overscroll-behavior: contain; scrollbar-width: thin; }
.radar-drawer { width: min(100vw, 560px); height: 100dvh; }
.radar-drawer-body { min-height: 0; overflow-y: auto;
  padding-bottom: max(16px, env(safe-area-inset-bottom)); }
```

表头sticky必须结合实际滚动容器验证，不能只加一行position就宣称完成。字体、字号、行高与布局密度应在CSS像素与DPR明确的后续截图中评估。

## D. 改造清单与验收门槛

### P0：先修会误导用户的事实与证据链

| 编号 | 具体位置与改法 | 验收案例 |
| --- | --- | --- |
| P0-1 缺失语义 | `bridge/schema.py:FocusStock`、`pipeline_loader.py:build_focus_pool`、`contracts.ts:mapStock`、`radar-route.tsx:Change/StockDrawer`：nullable行情/板数，补limit质量；不把未知写成否定 | 冰山冷热4板+空时间显示“时间未提供”；null涨幅显示—；真实0显示0.00%；莱美不推断板数 |
| P0-2 数据时间 | `schema.py:RadarSnapshot`、`pipeline_loader.py:load_pipeline`、`contracts.ts:sourceBadges`、`RadarRoute`页头：tradeDate/dataAsOf与generatedAt分离；live改“真实采集” | 本批明确10-16行情；旧快照无论何时加载都不显示“实时”；显示legacy/社区缺口 |
| P0-3 社区透传 | `push_to_aihot.py:build_snapshot.highlights`、`contracts.ts:FileHighlight/mapHighlight`、`HighlightCard`：保留时间/摘要/互动/情绪/ID，unknown不显示中性 | 现有看空标题保留引擎看空结果；128条旧数据用未判定；日期缺失不造时间 |
| P0-4 股票映射一致 | `contracts.ts:mapSnapshot` 合并完整entry与base；`run_bridge.py/build_snapshot` 让全池共享社区实体，不仅top携带 | tail探针3.14/2.7保持原值；top30/pool50时同股三入口价量/评论一致 |
| P0-5 家数与标签 | `run_bridge.py:build_theme_ladders`、`contracts.ts:RadarThemeLadder/sealedCount`、`ThemePicker`：源标签加权统计与唯一家数分开；增加unassignedStockCount | 11+5+1不自动标17个去重股票；3只无归属显式记账；“领涨”先改代表股 |
| P0-6 方向统计透明 | `schema.py:SentimentSummary`、`sentiment_engine.py:summarize`、`mapSentiment/SentimentBar`：方向分母与labelReason；小样本提示，未知不做判断 | 江淮显示2/14方向样本；兆易50/50仍可见；无方向和无采集不同状态 |
| P0-7 证据可复现 | `bridge/config.py`、`run_bridge.py` 输出路径参数；模块tests与page tests改读独立临时fixture，不要求覆盖.data；后续manifest关联截图SHA/快照SHA/viewport | 不改.data也能运行测试；截图与JSON可一一匹配；标题与实际榜单数量一致 |

P0不要求重新实时抓全量数据即可先完成：可用现有封存快照、离线样本及最小畸形输入覆盖。任何补源动作继续走YM-data-pipeline公共契约，不能为了时间字段另写行情爬虫。

### P1：提升真实信息质量与复盘效率

| 编号 | 文件/函数与具体改法 | 验收标准 |
| --- | --- | --- |
| P1-1 主题治理 | `ThemeCatalog.load/normalize_theme/_merge_themes`、题材词典的明确别名/父子关系；事件词单独字段 | CPO同名成员集合归一；飞行汽车括号别名归一；泛机器人不强制等于人形；原标签可追溯 |
| P1-2 板块导航 | `ThemePicker/ThemeStockRow` + 模块样式：主线默认收敛、全部可查、两行股票行、去全宽空情绪条 | 用户能快速找到任一真实主线；16股不被大卡片无谓拉长；不靠删除长尾改善指标 |
| P1-3 原因层级 | `_why_hot_of`、schema/contracts、`whyHotSummary/StockDrawer`：reason.kind+来源、摘要/原文分层 | 中际概念兜底明确写“关联概念”；冰山先见硬数据与摘要，全文可展开 |
| P1-4 归股与精选 | `run`统一postsByStock；`build_snapshot`质量筛选、按平台候选与事件去重 | code-less命中帖可进入对应股；“厉害”不占逻辑精选；生益同事件最多一个默认槽，原帖仍可访问 |
| P1-5 情绪规则 | `score_post/_longest_matches` 句内否定与引用规则；扩充现有金标回归 | “无法继续涨停”不判看多；保留正常“涨停”上下文；报告分类质量而非只报拦截数 |
| P1-6 入池与排序 | `build_focus_pool`、`score_resonance/_rank_decay`、`BridgeConfig/build_parser`：明确候选范围与名次融合，默认top与UI一致 | 输出selectionBasis与版本；并列稳定；不宣称全市场最强；30/50配置均匹配文案 |
| P1-7 表格与可访问性 | `StockTable` colgroup+摘要2行+详情按钮；`StockDrawer`平台重置、上一只/下一只；URL状态策略 | 键盘能打开每股；标签点击不误开抽屉；返回后滚动/选中不丢；小屏股票身份不被横滚藏住 |
| P1-8 首页与壳 | `site/`导航/默认入口、`apps/web/app/routes/home.tsx`：雷达成为默认入口，旧资讯有明确独立入口 | 直接打开/进入雷达；旧搜索与资讯路由兼容，架构测试同步真实产品契约 |
| P1-9 存储/缓存 | `write_snapshot`原子替换；`server.ts:loadRadarSnapshot/send` 内容hash ETag、保留最后有效快照和错误类别 | 同长不同内容不会304；半写不污染读端；坏JSON明确降级且不伪装为成功空结果 |

### P2：进阶打磨，避免重新长成复杂资讯站

| 编号 | 改造 | 边界与验收 |
| --- | --- | --- |
| P2-1 版本化归一实体 | schema v2、stocksByCode/postsById/memberCodes、legacy adapter | 同一事实只存一次；旧文件仍能读取；schemaVersion未知明确报错 |
| P2-2 按需详情 | `server.ts`既有详情接口+`StockDrawer`延迟加载完整正文/帖子 | 列表payload减小；慢响应有状态；换股时旧请求不覆盖新股 |
| P2-3 热度解释 | 加排名分量、sourceCoverage、有限窗口趋势与版本 | 没有历史快照不画趋势；不把采集量/来源缺失当人气变化 |
| P2-4 键盘与个性偏好 | 快捷键、紧凑/舒适密度、本地记忆选中主线 | 输入框不抢键；刷新/分享URL语义明确；不引入新的交易动作 |
| P2-5 视觉回归 | 375/768/1440 CSS px，浅/深、200%缩放、长中文、null与全失败状态 | 每张图记录数据hash/viewport/DPR；键盘和触摸另测，截图不替代交互 |

## E. 推荐下一张工单的范围与验证方式

建议先单独签“数据语义与社区透传修复”工单覆盖P0，完成后再签“主线归一与阅读密度”工单。不要把主题本体、排名算法、首页重定向、CSS重写一次混在一个diff中。每一步以封存输入做前后对照，不需要以新的线上随机结果证明改动正确。

最少应补的离线用例：

1. 空/0/负值、缺少池覆盖、4板无时间，三端（JSON/API/UI）保真。
2. 同一股票只在梯队/只在榜单/同时存在、top30与top50，价量、情绪与详情一致。
3. 2/14方向样本、0方向、50/50分歧、缺平台，不再被同一label盖掉。
4. 不带code但通过别名归股的帖子、有明确否定的标题、无发布时间、重复资讯，保留事实链。
5. 主题alias合并的成员去重、父子不误合并、事件不升级主线、3只未归股有明确计数。
6. 交易日与生成日不同、同长度内容更新、损坏快照、读写交错；旧数据不假装实时。
7. 真正的键盘打开/关闭/平台切换/切股/回板块，不再仅用SSR中出现字符串证明交互通过。

本轮没有重跑需要构建、数据库或覆盖.data的整套测试，也没有新建浏览器会话；本任务要求的四张已有真实渲染图已全部实际查看。已有manifest的65/65、17/17、build通过仅作为历史记录，未冒充本轮重跑结果。当前SSR测试检查标签出现而不检查数据分母、来源时间或键盘路径，正是上述问题仍能与既有PASS共存的原因。

### 可复核的本轮探针

以下命令只读文件或执行纯函数，不生成行情快照、不触发推送：

```sh
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
p = Path('docs/evidence/lite01-20261017/short-term-radar-snapshot.json')
d = json.loads(p.read_text())
s = d['topResonanceStocks']
t = d['themeLadders']
h = [p for x in s for p in x['highlights']]
print(len(s), len(t), sum(sum(map(len, x['ladders'].values())) == 1 for x in t))
print({k: sum(bool(x.get(k)) for x in s) for k in ('whyHot','limitReason','sealTime','themes','highlights')})
print(len(h), Counter(p['platform'] for p in h))
print([(x['code'], x['name']) for x in s if not x['themes']])
PY

node --input-type=module - <<'JS'
import {mapSnapshot} from './modules/short-term-radar/contracts.ts';
const x = mapSnapshot({themeLadders:[{theme:'review',ladders:{人气热股:[
  {code:'600000',exchange:'sh',changePct:3.14,amountYi:2.7}
]}}]});
console.log(x.themeLadders[0].stocks[0].changePct, x.themeLadders[0].stocks[0].amountYi);
// 本轮实际结果：0 0；预期修复后：3.14 2.7。
JS
```

报告的交付边界：只新增本文件；未推进任何实施阶段，未改动live-dashboard或使用其端口，未执行commit/push/部署。以上市场内容只引用已存在的本地快照；未来是否补齐原始数据、调整主题语义与排名参数，由后续明确工单落实。
