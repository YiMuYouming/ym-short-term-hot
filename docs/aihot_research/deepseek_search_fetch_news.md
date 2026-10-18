# DeepSeek Search / Fetch API 上线：官方公告与媒体报道汇总

> 整理时间：2026-10-17 16:40（北京时间）。只做调研，代码和配置都没改。
> 标记说明：**已核对原文** 表示本次打开了原页面，核对过文中原话；**待核实** 表示只看到二手转述，或者原文的时间、时区不明确。
> 时间：除特别注明外，都已换算成北京时间（UTC+8）。

## 一、结论速览

- **官方渠道只有 API 文档：** 这次上线由 DeepSeek API 文档的「网页搜索与抓取」指南和「更新日志」（2026-10-17 条目「开放自研搜索 API」）公布。官方 X 账号 @deepseek_ai 和微信公众号都**未找到**单独公告。
- **社区最早的讨论时间：** 2026-10-16 晚。locdd 论坛帖子发于 10-16 21:15，帖子里已经贴出文档链接。所以文档大概在 10-16 晚上已经能访问，更新日志写的日期是 10-17。
- **核心要点：** 定价、接口地址、限速、只对成功请求收费，各家报道和官方文档一致。
- **主要分歧在“免费”的说法上：**
  - 官方文档：只有在 DeepSeek Harness、Claude Code、Codex 里通过服务端工具调用产生的 Search/Fetch 请求暂不收费，北京时间 2026-11-01 00:00 起按次收费。自己直接调接口，现在就收费。
  - 部分媒体和帖子写成“限时免费窗口”“前两周免费”，或者只提 Search，这些说法不准确。

## 二、官方渠道

| 渠道 | 是否有公告 | 发布时间（北京时间） | 状态 |
| --- | --- | --- | --- |
| API 文档「网页搜索与抓取」<br>https://api-docs.deepseek.com/zh-cn/guides/search/ | 有 | 页面上没有写时间。社区最早在 10-16 21:15 引用 | 已核对原文 |
| API 文档「更新日志」<br>https://api-docs.deepseek.com/zh-cn/updates | 有，条目名「开放自研搜索 API」 | 页面写「时间: 2026-10-17」，没有具体时刻 | 已核对原文 |
| X @deepseek_ai | **未找到** | 最新一条发于 2026-10-02 15:00，内容是 Harness 桌面版。10-15 之后没有新帖 | 已核对（X API 拉取） |
| 微信公众号「DeepSeek」 | **未找到**（没有被搜索引擎收录） | — | 待核实（可以在微信里直接看） |
| deepseek.com 官网新闻 | **未找到** | — | 待核实 |

### 2.1 更新日志原文摘录（2026-10-17）

> 「开放自研搜索 API：DeepSeek 网页端与 API 端的搜索能力均由自研 DeepSeek 搜索引擎提供底层支持，稳定处理每天来自全球各地的数亿次搜索请求。DeepSeek 搜索是 AI 原生的通用搜索引擎，索引了全球千亿级网页，支持多语言搜索，实时返回高相关、高权威、高时效的优质结果。针对 SEO 作弊、GEO 操纵和低质 AIGC，我们通过严格的识别机制进行过滤……使用方式请参考网页搜索与抓取指南。」

同一天的日志还有一条「DeepSeek-V4.1-Flash-1017 更新」：调用方式和价格不变，仍然用 `deepseek-flash`。

### 2.2 指南原文要点

全部已核对原文。

- **定位，即 Agent/RAG 场景：** 「Search 接口和 Fetch 接口为 Agent 与 RAG 应用提供实时网页内容」。官方明确提到了 Agent 和 RAG。
- **接口：**
  - Search 是 `POST https://api.deepseek.com/v1/tools/search`，由 DeepSeek 自研搜索引擎支持。
  - Fetch 是 `POST https://api.deepseek.com/v1/tools/fetch`，抓取单个网页，返回 Markdown。
  - 两者都用和 DeepSeek API 相同的 Bearer 鉴权。
- **Search 参数和返回：**
  - `query` 长度 1～128 字符。
  - `count` 取 1～50，默认 10。
  - 支持的搜索语法：`site:`、`-site:`、`-`、`"..."`、`lang:`、`after:`、`before:`。
  - 每条结果包含 rerank_score（0～3）、title、url、snippet、summary、content、date 和 authority（0～4）。
- **计费：**
  - Search、Fetch 各自按「每 1,000 次成功请求 5 元」收费。
  - 「请求失败、搜索无结果或超时不计费」，`count` 不影响单价。
- **限速：**
  - 每个账号 Search、Fetch 各 5 QPS，「分别独立限速」，按账号计，与用哪个 API Key 无关。
  - Fetch 另外对目标域名有 QPS 限制。
  - 超出限制返回 429。
- **服务端工具调用的收费时间：** 原文是「当前用户在 DeepSeek Harness/Claude Code/Codex 中使用 DeepSeek API 时，已经会通过 Server 端工具调用访问到 Search/Fetch 接口，这部分 Search/Fetch 接口调用目前未计费，并将于北京时间 2026 年 11 月 1 日 00:00 起按次收取调用费用。」

## 三、媒体报道

| 来源 | 发布时间 | 和官方要点是否一致 | 备注 | 状态 |
| --- | --- | --- | --- | --- |
| IT之家《DeepSeek 上线网页搜索与抓取 API、API 短暂出现 V4.1 Flash-1017 快照、Harness v0.2.1-rc1 发布》<br>https://www.ithome.com/1/014/291.htm | 2026-10-17 14:36（页面时间，按北京时间理解） | 定价、限速、鉴权、只收成功请求、Agent/RAG 定位都一致 | 写的是「Search API 上线后的前两周内（2026 年 11 月 1 日之前），通过 Claude Code 的 Web Search 工具或 Codex 的 web_search 功能触发的搜索不收取 Search 费用」。只提了 Search，没提 Fetch 和 DeepSeek Harness | 已核对原文 |
| Pandaily《DeepSeek Adds Standalone Search and Fetch APIs for Agents, Priced at 5 Yuan per 1,000 Calls》<br>https://pandaily.com/deepseek-api-search-fetch-endpoints-5-yuan-per-1000-requests-5-qps-agents-rag | 2026-10-17。PulseAugur 标的是 02:09，时区不明，如果是 UTC 就是北京时间 10:09 | 接口路径、参数、定价、限速都一致。也提到「agent and RAG applications」 | 写的是「first two weeks after the Search API launch」不收 Search 费，还说「will announce the exact billing start date separately」。现在官方文档已经写明 11-01 00:00，所以这篇报道可能基于文档的早期版本 | 已核对原文（时刻待核实） |
| DoNews 快讯<br>https://www.donews.com/news/detail/8/6744126.html | 2026-10-17 14:41 | 一致：5 元/千次、每秒 5 次、独立计数、面向 Agent 和 RAG | 很短，没提服务端工具调用的收费时间 | 已核对原文 |
| AI热报（转载 Pandaily）<br>https://airebao.com/item/46042 | 2026-10-17 | 一致 | 只是转述 | 已核对（搜索摘要） |
| AGI Hunt（转述 X 用户 @teortaxesTex）<br>https://agihunt.info/p/1a146480e52f07e7b4fb36eedc0 | 2026-10-17 | 一致，折算约 0.70 美元/千次 | 只是转述 | 已核对（搜索摘要） |
| PulseAugur 聚合<br>https://pulseaugur.com/cluster/305128-deepseek-launches-new-search-and-fetch-apis-for-ai-agents | 2026-10-17 | 一致 | 只收录了 Pandaily 这一个来源 | 已核对（搜索摘要） |
| ModelPriceLab | — | — | 这次没搜到具体页面 | 待核实 |

## 四、社区讨论

时间都是北京时间。

- **locdd 论坛《更新搜索计费》** https://www.locdd.com/t/topic/100968
  - 发帖时间是 **2026-10-16 21:15**（原文 13:15 UTC），是目前找到最早的讨论。
  - 争论的焦点是“这算涨价，还是把原来就有的收费公开了”：
    - 一方认为以前只收搜索结果占用的 token，现在是额外收费。
    - 另一方说以前在 DeepSeek Harness 里用搜索也扣过费，只是不透明。
  - 也有人拿腾讯元宝、智谱的搜索价格比较，认为这个价格不算贵。
  - 状态：已核对原文。
- **X @MingTian685474** https://x.com/MingTian685474/status/2111107062587592808
  - 发于 10-16 22:48。
  - 拿同类服务比价：Brave 每千次 3～5 美元，Tavily 5～8 美元，Exa 7 美元。认为 DeepSeek 便宜，但限速低。
  - 状态：已核对原文。
- **X @zane_os** https://x.com/zane_os/status/2111120520896995599
  - 发于 10-16 23:42，被广泛转发，约 270 个赞。
  - 重点提到限速是按账号算，而不是按 API Key 算。
  - 状态：已核对原文。
- **X @NFT_Chen**《🔥重磅！DeepSeek Search/Fetch API 正式上线……》 https://x.com/NFT_Chen/status/2111359389324156996
  - 发于 10-17 15:31，就是用户转发的那段文字的原帖。
  - 里面写了「限时免费窗口……11月1日前不收费」，这个说法不准确，见第五节。
  - 状态：已核对原文。
- **X @realNyarime** https://x.com/realNyarime/status/2111370119813476434
  - 发于 10-17 16:13。
  - 写的是 11-01 起对 Harness、Claude Code、Codex 用户按次计费，这个说法和官方文档一致。
  - 状态：已核对原文。
- **其他背景**
  - 创锋一号《DeepSeek Harness 初体验……》 http://www.cf-1.com/news/4036275/
  - 文章说，DeepSeek Harness 内置的 web_search 原来是通过 Anthropic 兼容端点调用模型，在服务端搜索，按 token 计费。这可以解释论坛里“以前也收费”的说法。
  - 状态：待核实，是新接口上线前的旧文章。

## 五、分歧和需要注意的地方

1. **「限时免费窗口」不准确。**
   - 官方文档里，不收费的只有在 DeepSeek Harness、Claude Code、Codex 中通过服务端工具调用产生的 Search/Fetch 请求，北京时间 2026-11-01 00:00 起收费。
   - 直接调 `/v1/tools/search` 和 `/v1/tools/fetch`，现在就按 5 元/千次收费。
2. **「前两周 / 只免 Search」的说法和官方文档不一致。**
   - IT之家和 Pandaily 写的是 Claude Code 的 Web Search、Codex 的 web_search「不收 Search 费用」。
   - 官方文档写的是「Search/Fetch」，而且把 DeepSeek Harness 也列进去了。
   - Pandaily 还说收费日期「另行公布」，现在的文档已经写明 11-01。官方文档可能在发布后修改过，**以官方文档为准**。
3. **美元价格是换算出来的。**
   - X 上「$0.75/千次」「~$0.70」都是按汇率折算的，官方只写了人民币 5 元。
4. **发布时间。**
   - 更新日志写的是 10-17，但社区 10-16 晚上就在讨论文档了。
   - 准确的上线时刻，官方没有公布，**待核实**。
5. **同时发生的其他事。**
   - V4.1-Flash-1017 更新：官方日志在 10-17 已确认。上午 IT之家发稿时还写着“尚未说明”。
   - DeepSeek Harness v0.2.1-rc1 发布。
   - 不少报道把这几件事放在一起写，引用时要分开。

## 六、未找到

- @deepseek_ai 在 X 上关于 Search/Fetch API 的帖子。
- 微信公众号「DeepSeek」的公告文章，搜索引擎里没有收录。
- deepseek.com 官网新闻页的公告。
- 官方公布的准确上线时刻，以及指南页面的修改记录。
- ModelPriceLab 的具体报道链接。
