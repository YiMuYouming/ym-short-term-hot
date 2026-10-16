# AIHOT 社区舆情源调研报告（2026-10-16 台北时间）

## 补充更新（2026-10-16 13:40 后）
- 雪球作者从 18 位补到 23 位（新增题材逻辑资金、zhuigaohuiyisheng、干货逻辑预期差，另有 2 位 ID 已核实、昵称待核实）。
- 淘股吧：逐个抓取 33 人主页的帖子标题来佐证风格，31 人改为“已核实/部分核实”；把 2 条按昵称推断的标签改正了（超短小妖女是赛事账号，涨停诗人没有打板证据）；作手新一的“首阴反包”删掉了；定力、镀金梦想、超短小妖女、淘股吧实盘标为赛事数据源，不算交易大V。
- 东财：sorttype 0=按发帖时间，1~8=按最后回复时间，没有热度排序；默认列表=按回复时间，`,f`=按发帖时间，分页写法 `_页码`；`,99` 是约 3.8 万条的子集；帖子详情页和移动端都测过了。
- 淘股吧：没有独立的 24 小时热帖榜（/hot、/hotTopic 都回退到首页）；替代方案是移动端 XHR `m.tgb.cn/getMZh?pageNo=`；精华分页是 `/jinghua/{页}-{排序}`。
- 雪球：并入浏览器实测结果（cookie 要求、4 个 JSON 接口及字段）。

## 1. 淘股吧（33位）
|昵称|ID/主页|风格|佐证|状态|
|-|-|-|-|-|
|炒股养家|[134434](https://www.tgb.cn/blog/134434)|情绪/交易心法(历史)|主页精华《养家心法论股市》(2012)；近年无新主帖（主页 2026-10-16 抓取）|已核实(主页帖子)|
|赵老哥|[154034](https://www.tgb.cn/blog/154034)|游资传奇(历史)|主页精华《八年一万倍》(2015)；之后无新主帖，风格标签依外部口碑（主页 2026-10-16 抓取）|部分核实|
|作手新一|[827264](https://www.tgb.cn/blog/827264)|龙虎榜游资(历史)|主页《第一次——龙虎榜买一》(2017)；最后主帖2017；首阴反包等标签未佐证，已删除（主页 2026-10-16 抓取）|部分核实|
|职业炒手|[4223](https://www.tgb.cn/blog/4223)|社区老ID/转载|近年主帖多为转载/社区话题(2023)（主页 2026-10-16 抓取）|已核实(主页帖子)|
|柏拉爱空|[252069](https://www.tgb.cn/blog/252069)|每日复盘、板块轮动|每日短复盘：10月15日众生皆苦、AI漫剧持续强势等（主页 2026-10-16 抓取）|已核实(主页帖子)|
|十万起家|[138280](https://www.tgb.cn/blog/138280)|盘中情绪观察|每日多帖盘口/竞价观察（主页 2026-10-16 抓取）|已核实(主页帖子)|
|龙飞虎|[103830](https://www.tgb.cn/blog/103830)|历史账号(套利)|主页《低风险套利模式之600991》(2011)，已不活跃（主页 2026-10-16 抓取）|已核实(主页帖子)|
|延边刺客|[5894557](https://www.tgb.cn/blog/5894557)|每日复盘/实盘(高人气)|每日精华帖以日期命名(1015/1014…)，单帖浏览8万~15万（主页 2026-10-16 抓取）|已核实(活跃度)；具体战法待核实|
|玫瑰抓龙头|[7826561](https://www.tgb.cn/blog/7826561)|龙头战法、连板空间龙接力、情绪周期|10.12复盘:新华继续加速晋级十板；系列《龙头战法第八课:龙头连板换手板》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|作手阿意|[13126346](https://www.tgb.cn/blog/13126346)|情绪周期推演、老龙反抽|系列《情绪流选手教你看盘》:定义周期、老龙反抽玩法（主页 2026-10-16 抓取）|已核实(主页帖子)|
|南山游龙|[8919260](https://www.tgb.cn/blog/8919260)|大盘/情绪周期、退潮规避|《退潮三部曲》、弱势混沌期低位试错（主页 2026-10-16 抓取）|已核实(主页帖子)|
|zarili|[2577911](https://www.tgb.cn/blog/2577911)|周期节点、手动量化|《分享一些手动量化的内容》、震荡磨底试错（主页 2026-10-16 抓取）|已核实(主页帖子)|
|杭城小七哥|[15145153](https://www.tgb.cn/blog/15145153)|情绪盘眼|小七哥每日复盘：盘眼思维（主页 2026-10-16 抓取）|已核实(主页帖子)|
|战神只做龙头|[13110396](https://www.tgb.cn/blog/13110396)|最强板块跟随、1进2|《1进2就解锁市场最高楼的审美》；帖子带推广性质（主页 2026-10-16 抓取）|已核实(主页帖子)|
|小土堆爆金币|[9259508](https://www.tgb.cn/blog/9259508)|结构底/反预期、情绪载体二分套利|土帅训练营：结构底、识别反预期、二分套利情绪载体；带训练营推广性质（主页 2026-10-16 抓取）|已核实(主页帖子)|
|ttt小韭菜|[11157763](https://www.tgb.cn/blog/11157763)|每日复盘|按日期发帖(1014/1013…)（主页 2026-10-16 抓取）|已核实(活跃度)；战法待核实|
|骚年凌云志|[8704352](https://www.tgb.cn/blog/8704352)|—|主页未解析出帖子列表（主页 2026-10-16 抓取）|待核实|
|小宝1105|[9239701](https://www.tgb.cn/blog/9239701)|大盘见底判断、硬科技共振|10.15护盘的底能成为铁底吗？等，单帖浏览2~4万（主页 2026-10-16 抓取）|已核实(主页帖子)|
|酒馆老李|[15114043](https://www.tgb.cn/blog/15114043)|首板挖掘、低位新龙(三板内)|《从首板就发掘九阳这类龙头》《想抓三板以内的低位新龙》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|朱雀路作手|[7105646](https://www.tgb.cn/blog/7105646)|连板接力、1进2|《缩量…接力的天堂来了》《今天到了关注一进二的节点》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|主升龙头空空龙|[13186975](https://www.tgb.cn/blog/13186975)|情绪周期、炸板率/情绪先锋|复盘提到情绪盟主、炸板率、情绪先锋金健（主页 2026-10-16 抓取）|已核实(主页帖子)|
|冰点破局人ViTa|[13899761](https://www.tgb.cn/blog/13899761)|情绪周期(新周期确认)、龙空龙|《以情绪为发令枪的三步确认法》《龙空龙关键时间窗口》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|连板龙头作手|[13987504](https://www.tgb.cn/blog/13987504)|连板接力、高度板|《高度压制重回3板》，持有新华传媒/九阳（主页 2026-10-16 抓取）|已核实(主页帖子)|
|悟空一战成名|[2721689](https://www.tgb.cn/blog/2721689)|—|主页未解析出帖子列表（主页 2026-10-16 抓取）|待核实|
|多维辩证交易体系|[12401099](https://www.tgb.cn/blog/12401099)|题材/抱团、周期节点|《抱团极致》《题材纷争…谁能走出来》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|海氏战法|[14403453](https://www.tgb.cn/blog/14403453)|20cm创业板一进二套利、盘前策略|《模式三：20cm一进二模式战法》《创业板一进二套利模式开启》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|定力|[301502](https://www.tgb.cn/blog/301502)|实盘赛组织者(非交易者)|帖子均为梦想杯实盘赛年榜（主页 2026-10-16 抓取）|已核实—建议作为赛事数据源而非大V|
|镀金梦想|[6532082](https://www.tgb.cn/blog/6532082)|实盘赛组织者(非交易者)|镀金梦想百万杯赛事帖（主页 2026-10-16 抓取）|已核实—赛事源|
|超短小妖女|[5677554](https://www.tgb.cn/blog/5677554)|实盘赛组织者(非交易者)|赢家e万杯验证贴；原先据昵称推断的『超短』有误，已更正（主页 2026-10-16 抓取）|已核实—赛事源|
|西门口欠雪|[9086925](https://www.tgb.cn/blog/9086925)|每日实盘晒单|10.16实盘，极致纠错等；浏览量较低(数百)（主页 2026-10-16 抓取）|已核实(主页帖子)|
|涨停诗人|[12336535](https://www.tgb.cn/blog/12336535)|大资金风控/交易反思|《聊聊大资金的风控与节奏》；原『打板』推断无佐证，已更正（主页 2026-10-16 抓取）|已核实(主页帖子)|
|深圳超短炒家|[13307557](https://www.tgb.cn/blog/13307557)|龙头信仰、明牌买卖点|《龙头信仰，永不缺席》《给你们看我辽能的买卖点》（主页 2026-10-16 抓取）|已核实(主页帖子)|
|淘股吧实盘|[1032877](https://www.tgb.cn/blog/1032877)|官方实盘赛账号|官方赛事/验证贴（主页 2026-10-16 抓取）|已核实—赛事源|

## 2. 雪球（23位）
|昵称|ID|擅长|状态|
|-|-|-|-|
|投机风清扬|[5311792678](https://xueqiu.com/u/5311792678)|AI算力产业链拆解：HBM/先进封装/光互联/PCB/液冷/供配电|已核实(搜索引擎收录的雪球主页)|
|DinX-解构|[2503188652](https://xueqiu.com/u/2503188652)|AI硬件与国产替代、存储(长鑫/海力士)、英伟达/博通供应链|已核实(搜索引擎收录的雪球主页)|
|山竹一人|[2715675448](https://xueqiu.com/u/2715675448)|PCB、散热、先进封装、封测、ABF载板|已核实(搜索引擎收录的雪球主页)|
|小丫投资记|[3853112689](https://xueqiu.com/u/3853112689)|硅基半导体材料/设备、光电子、低空经济产业链|已核实(搜索引擎收录的雪球主页)|
|BOM拆解师|[kevinshen](https://xueqiu.com/u/kevinshen)|BOM拆解(内容未抓取到—待核实)|已核实(搜索引擎收录的雪球主页)|
|重组逻辑研究|[6160618134](https://xueqiu.com/u/6160618134)|并购重组；简介称短线情绪分析|已核实(搜索引擎收录的雪球主页)|
|stardingsue|[8785356683](https://xueqiu.com/u/8785356683)|商业航天：火箭、卫星、千帆星座产业链|已核实(搜索引擎收录的雪球主页)|
|用户3105890754|[3105890754](https://xueqiu.com/u/3105890754)|固态电池(电解质、量产进展)|已核实(搜索引擎收录的雪球主页)|
|商业航天大火箭|[7456417652](https://xueqiu.com/u/7456417652)|商业航天交易观点(偏讨论，质量待评估)|已核实(搜索引擎收录的雪球主页)|
|dahui118|[5436902724](https://xueqiu.com/u/5436902724)|商业航天/铂力特(偏个股看多，质量待评估)|已核实(搜索引擎收录的雪球主页)|
|丁生说交易|[8514651885](https://xueqiu.com/u/8514651885)|光模块/NPO/CPO、半导体材料、人形机器人清单|已核实(搜索引擎收录的雪球主页)|
|机器人与人工智能AI|[1866014742](https://xueqiu.com/u/1866014742)|人形机器人、AI产业链中报追踪|已核实(搜索引擎收录的雪球主页)|
|雪浪无痕|[7237263461](https://xueqiu.com/7237263461)|主题方向总结(AI/电力/芯片/机器人/航天)|ID已核实(来自其雪球帖子URL)|
|luke_zhu|[6646095823](https://xueqiu.com/6646095823)|光模块产能/需求测算转述|ID已核实(来自其雪球帖子URL)|
|(昵称待核实)|[1795173592](https://xueqiu.com/1795173592)|光模块TEC用量与产能测算(富信科技)|ID已核实(来自其雪球帖子URL)；昵称待核实|
|(昵称待核实)|[2237153088](https://xueqiu.com/2237153088)|《CPO设备先行系列》CPO价值量测算|ID已核实(来自其雪球帖子URL)；昵称待核实|
|(昵称待核实)|[1390418887](https://xueqiu.com/1390418887)|特斯拉Optimus供应链(丝杠/减速器/轴承)|ID已核实(来自其雪球帖子URL)；昵称待核实|
|可爱的金小黄|[3877983699](https://xueqiu.com/3877983699)|特斯拉Optimus审厂/T链标的|ID已核实(来自其雪球帖子URL)|
|题材逻辑资金|[4286242955](https://xueqiu.com/u/4286242955)|短线题材/连板生态与资金逻辑|已核实(雪球主页搜索收录)|
|zhuigaohuiyisheng|[7785369046](https://xueqiu.com/u/7785369046)|题材埋伏日历、预期博弈|已核实(雪球主页搜索收录)|
|干货逻辑预期差|[1639935160](https://xueqiu.com/u/1639935160)|个股预期差/题材正宗性(盛科通信、瑞丰高材等)|已核实(雪球主页搜索收录)|
|(昵称待核实)|[5672579962](https://xueqiu.com/5672579962)|预期差方法论 + PCB/覆铜板个股案例|ID已核实(帖子URL)；昵称待核实|
|(昵称待核实，发布『雪球专刊』)|[3746414875](https://xueqiu.com/3746414875)|AI硬件专题汇编：HBM/PCB/液冷电源|ID已核实(帖子URL)；昵称待核实|

## 3. X 账号（28个，全部经 X API 核实）
|handle|name|tier|focus|
|-|-|-|-|
|@DeItaone|*Walter Bloomberg|T1|7x24宏观/个股快讯|
|@FirstSquawk|First Squawk|T1|7x24快讯|
|@LiveSquawk|LiveSquawk|T1_5|7x24快讯|
|@Newsquawk|Newsquawk|T1_5|7x24快讯|
|@WalterBloomberg|Walter Bloomberg|T1_5|快讯(DeItaone同源备号)|
|@zerohedge|zerohedge|T2|宏观/市场情绪|
|@unusual_whales|unusual_whales|T1_5|美股异动/期权流|
|@ChinaBizWatch|China Business Watch|T2|中国商业新闻|
|@nvidia|NVIDIA|T1|英伟达官方→算力/光模块/PCB/液冷|
|@Tesla|Tesla|T1|特斯拉官方→汽车/机器人链|
|@elonmusk|Elon Musk|T1|特斯拉/Optimus/SpaceX/xAI→机器人、商业航天|
|@Figure_robot|Figure|T1_5|人形机器人|
|@SawyerMerritt|Sawyer Merritt|T1_5|特斯拉/SpaceX新闻聚合|
|@Teslarati|TESLARATI|T2|特斯拉新闻|
|@OpenAI|OpenAI|T1|大模型→AI应用/算力|
|@sama|Sam Altman|T1|OpenAI动态→算力需求|
|@SemiAnalysis_|SemiAnalysis|T1|半导体/算力深度拆解→光模块、CPO、HBM|
|@dylan522p|Dylan Patel|T1|SemiAnalysis创始人，算力供应链|
|@mingchikuo|郭明錤｜Ming-Chi Kuo|T1|苹果/AI硬件供应链→消费电子链|
|@trendforce|TrendForce|T1_5|存储/面板/晶圆价格→存储、半导体|
|@jukan05|Jukan|T1_5|韩台半导体/存储供应链传闻|
|@kakashiii111|Kakashii|T2|半导体/AI供应链评论|
|@firstadopter|tae kim|T2|科技股/英伟达评论|
|@IanCutress|Dr. Ian Cutress|T2|芯片技术分析|
|@techinsightsinc|TechInsights|T2|芯片拆解|
|@ServeTheHome|STH|T2|服务器/数据中心硬件|
|@PatrickMoorhead|Patrick Moorhead|T2|半导体/数据中心分析|
|@BrianRoemmele|Brian Roemmele|T2|AI/科技(观点激进，噪声较大)|

剔除：@Jukanlosreve、@Optimus_Tesla（查无此账号）。

## 4. 接口（完整 endpoints.json）
```json
{
 "eastmoney_guba": {
  "list_default": {
   "url": "https://guba.eastmoney.com/list,{code}.html",
   "test": "200 实测",
   "note": "按最后回复时间排序(第2页 list,{code}_2.html 实测 post_last_time 倒序)；第1页前几条为置顶/推荐帖；页面内嵌 var article_list={...}"
  },
  "list_f": {
   "url": "https://guba.eastmoney.com/list,{code},f.html",
   "paging": "list,{code},f_{page}.html",
   "test": "实测：f_2 按发帖时间倒序 → f=按发帖时间",
   "note": "第1页置顶帖与默认页相同"
  },
  "list_99": {
   "url": "https://guba.eastmoney.com/list,{code},99.html",
   "paging": "list,{code},99_{page}.html",
   "test": "实测 count=37999(总帖977480的子集)，99_2 时间倒序",
   "note": "是精选/资讯类子集，具体含义待核实；不是『最热』"
  },
  "api_articlelist": {
   "url": "https://gbapi.eastmoney.com/webarticlelist/api/Article/Articlelist",
   "params": {
    "code": "600519",
    "sorttype": "实测：0=按发帖时间倒序(post_publish_time)；1~8 结果一致=按最后回复时间倒序(post_last_time)。无『最热』取值",
    "ps": "每页条数",
    "p": "页码",
    "from": "CommonBaPost",
    "deviceid": "任意",
    "version": "200",
    "product": "Guba",
    "plat": "Web"
   },
   "test": "200 无需cookie；sorttype 0~8 逐一实测 2026-10-16；count=977480(600519)",
   "top_keys": [
    "re",
    "count",
    "bar_name",
    "bar_code",
    "bar_info",
    "rc",
    "me",
    "time"
   ],
   "post_fields": [
    "post_id",
    "post_title",
    "stockbar_code",
    "stockbar_name",
    "user_id",
    "user_nickname",
    "post_click_count",
    "post_forward_count",
    "post_comment_count",
    "post_publish_time",
    "post_last_time",
    "post_type",
    "post_has_pic",
    "post_ip",
    "bullish_bearish",
    "art_unique_url"
   ]
  },
  "post_detail": {
   "url": "https://guba.eastmoney.com/news,{code},{post_id}.html",
   "test": "200 实测；页面内嵌 var post_article={...}，含 post_content"
  },
  "mobile": {
   "list": "https://mguba.eastmoney.com/mguba/list/{code} 200 实测(约300KB，内嵌含 post_content 的 JSON)",
   "article": "https://mguba.eastmoney.com/mguba/article/0/{post_id} 200 但只有 6KB 壳页(SPA)，正文接口待核实",
   "alt": "https://guba.eastmoney.com/o/list,{code}.html 200"
  },
  "list_1_f": {
   "url": "list,{code},1,f.html",
   "test": "count=5000，含义待核实"
  },
  "hot_note": "未发现按热度排序的 URL 或 sorttype；热度要自己用 post_click_count / post_comment_count 排"
 },
 "taoguba": {
  "domain": "www.tgb.cn (旧域 taoguba.com.cn 仍被引用)",
  "jinghua": {
   "url": "https://www.tgb.cn/jinghua/",
   "paging": "实测：/jinghua/{page}-{sort}，例如 2-1=第2页(title含『第2页』)，1-1、1-2=第1页的两种排序(1-1 按发帖日期；1-2 内容为旧帖，推测按热度/回复排序，待核实)；/jinghua/2 返回404",
   "money_rank": "/jinghua/topTopicMoney?stageNum={n}"
  },
  "newIndex": {
   "url": "https://www.tgb.cn/newIndex/{page}",
   "test": "200 实测(首页信息流)",
   "note": "/newIndex/2 的标题是『股票复盘』频道"
  },
  "post": {
   "url": "https://www.tgb.cn/a/{短码}",
   "example": "/a/2vUNIn9W0UH",
   "test": "从精华页提取"
  },
  "user": {
   "url": "https://www.tgb.cn/blog/{userId}"
  },
  "stock_bar": {
   "url": "https://www.tgb.cn/quotes/{sz002343|sh600869}",
   "test": "200 实测",
   "note": "帖子DOM待细化"
  },
  "other": [
   "https://www.tgb.cn/spmatch/index/ 实盘比赛",
   "https://www.tgb.cn/weblive/liveList?pageNo=1 直播",
   "https://shuo.tgb.cn/newsFlash/ 快讯",
   "https://www.tgb.cn/feeds/qryFeedsViewPointView 观点",
   "https://www.tgb.cn/stock/moreStockInfo 热股(未实测内容)",
   "https://www.tgb.cn/user/getMoreListAction 302需登录"
  ],
  "dom": {
   "post_row": "div.Nbbs-tiezi-lists",
   "title": "div.middle-list-tittle > a[href^='/a/'] (含[精]标记, title属性)",
   "reply_view": "div.middle-list-talk 文本『回复 / 浏览』",
   "last_time": "div.middle-list-reply",
   "author": "a[href^='/blog/'][data-user-id][data-topic-id][data-last-reply-date]",
   "home_weekup": "a.defaultContainerRight-weekUp-userName",
   "home_hotstock": "div.defaultContainerRight-stock-item / -stock-name / -stock-Rate / -stock-7discuss"
  },
  "24h_hot": {
   "result": "没有找到独立的 24 小时热帖榜 URL",
   "tested": {
    "/hot": "200 但内容就是首页(回退)",
    "/hot/": "404",
    "/hotTopic": "200 首页回退",
    "m.tgb.cn": "200，首页信息流由 XHR /getMZh?pageNo={n} 加载"
   },
   "best_substitute": "移动端 XHR https://m.tgb.cn/getMZh?pageNo=1 (实测返回 JSON：dto.indexList.listData[]{userID,userName,topicID,newTopicID,subject,subinfo…}，是首页推荐流)；另有 /ticai/ranking (题材淘金，200)、首页『热门研股』模块"
  }
 },
 "xueqiu": {
  "status": "浏览器已实测 2026-10-16（父代理提供）",
  "cookie": "访问 xueqiu.com 会跳到 www.xueqiu.com。未登录也会设置 xq_a_token/xq_r_token/xq_id_token/xqat/acw_tc/device_id；在浏览器里没有遇到 WAF。纯 curl 会被阿里云 WAF 拦截(本代理实测)，所以服务端要先用浏览器访问首页拿 cookie",
  "hot_stock": {
   "url": "https://stock.xueqiu.com/v5/stock/hot_stock/list.json?size=8&_type=10&type=10",
   "fields": "data.items[]: type,code,name,value,increment,rank_change,symbol,percent,current,chg,exchange,stock_type,sub_type,ad",
   "curl_no_cookie": "400 / 400016"
  },
  "symbol_status_new": {
   "url": "https://www.xueqiu.com/query/v1/symbol/search/status.json?count=10&comment=0&symbol=SH600519&hl=0&source=all&sort=time&page=1&q=&type=11",
   "note": "个股页『新帖』真实 XHR",
   "fields": "about,count,key,list[]: id,created_at(ms),timeBefore,source,target(/uid/id),like_count,reply_count,retweet_count,fav_count,description/text,user{id,city,followers_count…}"
  },
  "symbol_status_hot": {
   "url": "同上，sort=alpha",
   "note": "推测对应『热帖』(切换时的 XHR 未抓到)；多 excellent_comments[]{id,likeCount,text,pic,statusId,time_before}"
  },
  "hot_timeline": {
   "url": "https://www.xueqiu.com/statuses/hot/listV2.json?since_id=-1&max_id=-1&size=15",
   "fields": "next_max_id, items[]{id,category,original_status{id,user_id,source,created_at,fav_count,type,description,user{screen_name,followers_count}}}"
  },
  "stock_tabs": "全部讨论/交易/资讯/公告；新帖/热帖",
  "other_xhr": [
   "/statuses/interview/search.json?symbol=&count=3",
   "stock.xueqiu.com/v5/stock/quote.json?symbol=&extend=detail",
   "/v5/stock/realtime/pankou.json",
   "/v5/stock/chart/minute.json?period=1d",
   "/v5/stock/history/trade.json",
   "/v5/stock/quote/relevant.json",
   "/v5/stock/event/entry.json"
  ],
  "user_page": "https://xueqiu.com/u/{uid}"
 }
}
```
