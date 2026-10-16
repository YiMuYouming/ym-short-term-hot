// 这个行业的分类体系：类别、标签词表、平台与监管机构（主体）名录，以及防止张冠李戴的身份词典。
// 模型按这里的词表打标签，主题页（topics.json）按标签归类，筛选栏按类别分组。
// 换行业时：类别的 key 会出现在网址里（/all?category=…），上线后就不要再改；标签和名录可以随时增减。

/**
 * 网页上的类别（筛选栏、卡片角标、RSS 分类订阅）。key 是网址和接口里的身份，上线后不要改。
 * section 是日报里的分节标题（几个类别可以共用一节，按这里的顺序排）；guide 告诉结构抽取模型这一类收什么、
 * 和相邻类别的边界在哪（总的归类原则写在 prompts/structure.md 里）。
 * commentary 标出评论类（复盘、观点、舆情脉冲）：日报写过的事又有评论类的后续报道，只占一行快讯（报道它的信源够多时除外）。
 * 没归上类的资料在日报里放进第一个 key 为 industry 的类别所在的节（没有就放最后一节）。
 * feedLabel 是分类 RSS 标题里的名字（不写就用 label）。公开接口、RSS 和 MCP 里要把一类并进另一类发布，写在站点设置里（site/site.ts 的 PUBLIC_CATEGORIES）。
 */
export const CATEGORIES = [
  { key: "theme-catalyst", label: "题材", feedLabel: "题材催化", section: "主线题材与催化", guide: "引发板块异动或新题材发酵的政策文件、行业重磅消息、产业订单突破、技术实锤或选股宝/财联社级主线催化。重点是能驱动板块效应的事件。" },
  { key: "dragon-move", label: "龙头", feedLabel: "龙头异动", section: "龙头晋级与异动", guide: "市场高标连板股、容量中军、20cm弹性龙头的涨停归因、连板晋级、断板反包、炸板大面或跨平台热榜飙升。" },
  { key: "company-signal", label: "实锤", feedLabel: "互动与龙虎榜", section: "公司实锤与席位", guide: "上市公司董秘在互动易（上证e互动/深证易互动）的业务实锤回复、异动公告、监管函、减持/增持公告，以及龙虎榜知名游资与机构席位买卖明细。" },
  { key: "deep-logic", label: "逻辑", feedLabel: "深度逻辑", section: "产业逻辑与拆解", commentary: true, guide: "雪球、社区或研报对具体标的题材正宗性、产业链上下游传导、产能订单弹性、业绩预期的深度拆解与基本面预期差分析。" },
  { key: "youzi-review", label: "复盘", feedLabel: "游资复盘", section: "游资复盘与博弈", commentary: true, guide: "淘股吧等短线社区实盘高手对当日情绪周期（冰点/发酵/高潮/退潮）、连板接力梯队、明日竞价弱转强或分歧延续的复盘推演与操作思考。" },
  { key: "sentiment-pulse", label: "舆情", feedLabel: "社区舆情", section: "游资复盘与博弈", commentary: true, guide: "东方财富股吧、淘股吧、雪球评论区围绕热门股产生的多空激烈交锋、散户一致性亢奋预警或恐慌核按钮情绪脉冲。" },
] as const satisfies ReadonlyArray<{ key: string; label: string; feedLabel?: string; section: string; guide: string; commentary?: true }>;

/**
 * 这个行业最受关注的一类发布（A 股短线是主线催化）：日报报头的“N 个主线催化”、改分类后修订已出的报告都按它数。
 * category 是类别，tag 是标签，两者都对上才算；unit 接在数字后面。
 * 没有这样一类的行业设成 null，报头就不显示这个数。
 */
export const RELEASE: { category: string; tag: string; unit: string } | null = { category: "theme-catalyst", tag: "主线催化", unit: "个主线催化" };

/** 周报月报的总述可以直接写、不必在报道里找到出处的行业通用词（小写）。站名会自动算进去。 */
export const PLAIN_TERMS: readonly string[] = ["a股", "st", "etf", "ipo", "pe", "pb", "tgb", "kpl", "20cm", "10cm", "t+1"];

/**
 * 内容理解一步给每篇资料判的“内容类型”（写在 prompts/content-understanding.md 里，改了类型要同步改那份提示词）。
 * 评分提示词（prompts/selection-score.md）按类型给五个维度不同的权重。
 */
export const ITEM_TYPES = ["theme_catalyst", "dragon_move", "company_signal", "deep_logic", "youzi_review", "sentiment_pulse", "market_rule"] as const;

// ── 标签词表 ────────────────────────────────────────────────────────────────────────────

/** 每篇资料的第一个标签必须是这些“分类标签”之一。 */
export const CATEGORY_TAGS = [
  "主线催化", "龙头异动", "连板晋级", "互动易实锤", "龙虎榜席位", "深度逻辑", "游资复盘", "多空分歧", "一致亢奋", "风险/监管", "公告/业绩", "其他",
] as const;

/** 可选的主题标签（题材方向与短线战法）。 */
export const TOPIC_TAGS = [
  "空间板", "20cm弹性", "容量中军", "首板发酵", "弱转强", "分歧转一致", "断板反包", "核按钮预警", "算力/光模块", "AI应用", "半导体/芯片", "机器人/具身", "低空/商业航天", "新能源/固态电池", "消费/医药", "大金融/并购重组",
] as const;

/** 可选的实体标签（社区平台、交易所与监管机构）。 */
export const ENTITY_TAGS = ["东方财富", "同花顺", "淘股吧", "雪球", "开盘啦", "财联社", "上交所", "深交所", "证监会"] as const;

/** 模型常写的近义词，统一成词表里的写法。 */
export const TAG_SYNONYMS: Readonly<Record<string, string>> = {
  // 分类标签近义词
  题材: "主线催化", 主线: "主线催化", 催化: "主线催化", 政策: "主线催化", 板块异动: "主线催化", 涨停原因: "主线催化", 题材发酵: "主线催化",
  龙头: "龙头异动", 异动: "龙头异动", 涨停: "龙头异动", 炸板: "龙头异动", 断板: "龙头异动", 高标: "龙头异动", 飙升: "龙头异动",
  连板: "连板晋级", 晋级: "连板晋级", 空间板: "连板晋级", 反包: "连板晋级",
  互动易: "互动易实锤", "e互动": "互动易实锤", 董秘: "互动易实锤", 实锤: "互动易实锤", 调研: "互动易实锤",
  龙虎榜: "龙虎榜席位", 席位: "龙虎榜席位", 游资席位: "龙虎榜席位", 机构席位: "龙虎榜席位",
  深度: "深度逻辑", 逻辑: "深度逻辑", 拆解: "深度逻辑", 产业链: "深度逻辑", 预期差: "深度逻辑",
  复盘: "游资复盘", 实盘: "游资复盘", 情绪周期: "游资复盘", 接力: "游资复盘",
  分歧: "多空分歧", 多空: "多空分歧", 交锋: "多空分歧", 博弈: "多空分歧",
  亢奋: "一致亢奋", 一致性: "一致亢奋", 一致: "一致亢奋", 过热: "一致亢奋",
  监管: "风险/监管", 风险: "风险/监管", 问询: "风险/监管", 处罚: "风险/监管", 监控: "风险/监管",
  减持: "公告/业绩", 增持: "公告/业绩", 公告: "公告/业绩", 业绩: "公告/业绩", 财报: "公告/业绩", 异动公告: "公告/业绩", 定增: "公告/业绩",
  // 主题标签近义词
  空间龙: "空间板", 高度板: "空间板", "20cm": "20cm弹性", 弹性: "20cm弹性", 中军: "容量中军", 权重中军: "容量中军",
  首板: "首板发酵", 发酵: "首板发酵", 弱转强: "弱转强", 转一致: "分歧转一致", 一致转分歧: "分歧转一致",
  核按钮: "核按钮预警", 核吸: "核按钮预警",
  算力: "算力/光模块", 光模块: "算力/光模块", cpo: "算力/光模块", 光通信: "算力/光模块",
  ai: "AI应用", 人工智能: "AI应用", 大模型: "AI应用",
  芯片: "半导体/芯片", 半导体: "半导体/芯片", 集成电路: "半导体/芯片",
  机器人: "机器人/具身", 具身: "机器人/具身", 人形机器人: "机器人/具身",
  低空: "低空/商业航天", 商业航天: "低空/商业航天", 卫星: "低空/商业航天",
  固态电池: "新能源/固态电池", 新能源: "新能源/固态电池", 锂电: "新能源/固态电池", 储能: "新能源/固态电池",
  医药: "消费/医药", 消费: "消费/医药", 创新药: "消费/医药",
  大金融: "大金融/并购重组", 并购: "大金融/并购重组", 重组: "大金融/并购重组", 券商: "大金融/并购重组",
};

// ── 平台与监管主体 ──────────────────────────────────────────────────────────────────────

/**
 * 主题页的主体：id → 显示名、卡片上显示的标签（null 表示只用 entity:<id> 归类）、别名。
 * aliases 给结构抽取模型看；otherNames 是平台自己的其他称呼（官方账号名、子品牌），
 * 把事实的主体对到发布方时也认它们。
 */
export const ENTITIES: Record<string, { name: string; displayTag: string | null; aliases: string[]; otherNames?: string[] }> = {
  eastmoney: { name: "东方财富", displayTag: "东方财富", aliases: ["东方财富", "东财", "股吧"], otherNames: ["东方财富股吧", "eastmoney"] },
  ths: { name: "同花顺", displayTag: "同花顺", aliases: ["同花顺", "ths", "10jqka"], otherNames: ["同花顺热榜", "同花顺问财"] },
  taoguba: { name: "淘股吧", displayTag: "淘股吧", aliases: ["淘股吧", "tgb"], otherNames: ["淘股吧社区"] },
  xueqiu: { name: "雪球", displayTag: "雪球", aliases: ["雪球", "xueqiu"], otherNames: ["雪球社区"] },
  kaipanla: { name: "开盘啦", displayTag: "开盘啦", aliases: ["开盘啦", "kpl"], otherNames: ["开盘啦题材"] },
  cls: { name: "财联社", displayTag: "财联社", aliases: ["财联社", "cls", "选股宝"], otherNames: ["财联社社"] },
  sse: { name: "上交所", displayTag: "上交所", aliases: ["上交所", "SSE"], otherNames: ["上海证券交易所", "上证e互动"] },
  szse: { name: "深交所", displayTag: "深交所", aliases: ["深交所", "SZSE"], otherNames: ["深圳证券交易所", "深证易互动"] },
  csrc: { name: "证监会", displayTag: "证监会", aliases: ["证监会", "CSRC"], otherNames: ["中国证监会"] },
};

/**
 * 身份词典：摘要和标题里出现的平台或监管机构，必须在原文里也出现过，否则退回原标题、丢掉摘要（防止模型张冠李戴）。
 * 社区平台名高频出现，这条守卫在本行业依然有用。
 */
export const IDENTITY_LEXICON: ReadonlyArray<{ id: string; name: string; patterns: RegExp[] }> = [
  { id: "eastmoney", name: "东方财富", patterns: [/东方财富|东财|股吧|eastmoney/i] },
  { id: "ths", name: "同花顺", patterns: [/同花顺|10jqka|\bths\b/i] },
  { id: "taoguba", name: "淘股吧", patterns: [/淘股吧|\btgb\b/i] },
  { id: "xueqiu", name: "雪球", patterns: [/雪球|xueqiu/i] },
  { id: "kaipanla", name: "开盘啦", patterns: [/开盘啦|\bkpl\b/i] },
  { id: "cls", name: "财联社", patterns: [/财联社|选股宝|\bcls\b/i] },
  { id: "sse", name: "上交所", patterns: [/上交所|上证e互动|\bsse\b/i] },
  { id: "szse", name: "深交所", patterns: [/深交所|深证易互动|\bszse\b/i] },
  { id: "csrc", name: "证监会", patterns: [/证监会|\bcsrc\b/i] },
];

/** 这些域名上的文章，发布方就是对应的机构（社区 UGC 平台不算发布方）。 */
export const PUBLISHER_DOMAINS: ReadonlyArray<{ entityId: string; domains: readonly string[] }> = [
  { entityId: "cls", domains: ["cls.cn"] },
];

/** 原文里的这些写法也算提到了对应机构。 */
export const IDENTITY_CONTEXT_ALIASES: ReadonlyArray<{ entityId: string; pattern: RegExp }> = [];
