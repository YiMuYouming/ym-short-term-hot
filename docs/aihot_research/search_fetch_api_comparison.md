# 开发者网页搜索 + 抓取 API 对比（对标 DeepSeek Search/Fetch）

- 日期：2026-10-17（台北时间）。用途：aihot（A 股短线热点）项目的接入调研，只写调研，不改代码。
- 状态标记：**官方** = 官方文档/官网核对；**实测** = 真实请求验证（注明日期）；**社区** = 第三方实测或文章，未经官方确认；**待核实** = 没查到或无法确认。
- 价格按各家公布的币种和单位原样写，**没有做汇率换算**。我没有调用任何付费接口，也没有使用任何 API key。

## 1. 总览表

| 产品 | 搜索 / 抓取是否分开 | 公布价格（原币种） | 域名过滤 / site: | 时间过滤 | 结构化字段（搜索） | 状态 |
|---|---|---|---|---|---|---|
| **DeepSeek** Search/Fetch（基准） | 分开：`/v1/tools/search`、`/v1/tools/fetch` | 各 ¥5 / 1000 次成功请求，失败、空结果、超时不收费 | `site:` 语法 | `after:` | 标题、URL、摘要、长摘要、发布时间、权威分 | 官方（详见 deepseek_search_fetch_integration.md） |
| **Tavily** | 分开：`/search`、`/extract`（另有 crawl、map） | 按 credit 计：PAYG $0.008/credit，包月 $0.0075–0.005/credit，每月免费 1000 credit。basic 搜索 1 credit，advanced 2 credit；extract 每 5 个成功 URL 1 credit（advanced 2），失败不收费 | `include_domains`（≤300）、`exclude_domains`（≤150） | `time_range`（day/week/month/year）或 `start_date`/`end_date` | title、url、content、score，可选 published_date、raw_content | 官方 |
| **Serper** | 搜索为主；网页抓取接口 `scrape.serper.dev` 只见第三方文档 | 预付：$50/5 万次（$1.00/1k）到 $3,750/1250 万次（$0.30/1k），额度 6 个月有效，新号送 2,500 次，只扣成功请求 | 走 Google 语法，`site:` 写在 q 里 | Google `tbs`（社区资料） | organic（title、link、snippet、date、position）等 Google 结果 | 价格：官方；site/tbs：社区；scrape 价格：待核实 |
| **Brave Search API** | 搜索 `/web/search`；`/llm/context` 返回抽取好的正文片段，不能抓指定 URL | Search $5/1k 请求（50 QPS）；Answers $4/1k + $5/百万 token（2 QPS） | q 里写 `site:`、`lang:` 等运算符；Goggles 自定义站点集和重排 | `freshness`：pd/pw/pm/py 或 `YYYY-MM-DDtoYYYY-MM-DD` | title、url、description、age/page_age、extra_snippets | 官方 |
| **Exa** | 分开：`/search`、`/contents` | search instant $4/1k，fast/auto $7/1k（含 10 条结果，第 11 条起每 1k 条 $1）；contents $1/1k 页（按内容类型分别计）；每月免费 $10 | `includeDomains`、`excludeDomains` | `startPublishedDate`、`endPublishedDate` | title、url、publishedDate、author、text/highlights/summary | 官方 |
| **Firecrawl** | 分开：`/v2/search`、`/scrape`（另有 crawl、map） | credit 制：搜索每 10 条结果 2 credit，scrape 每页 1 credit；免费每月 1000 credit；Hobby $19/月（年付 $16）含 5000 credit。scrape 无结果不收费，但返回 403/404 仍收 1 credit | query 里写 `site:`；另有 includeDomains/excludeDomains（来自搜索摘要，待核实） | `tbs`（qdr:h/d/w/m/y，自定义日期区间） | 搜索结果可直接附带 scrape 出的 markdown | 价格：官方（2026-09-04 起生效）；参数：搜索摘要指向官方文档，未逐条打开 |
| **Jina** Reader `r.jina.ai` / Search `s.jina.ai` | 分开 | 按 token 计费：Reader 按输出 token，Search 每次固定从 10,000 token 起。token 包单价页面没渲染出来 | `X-Site` 请求头或 `?site=` | 待核实 | Search 默认返回前 5 条，含 url、title、content | 计费方式和限流：官方；token 单价：待核实 |
| **博查 Bocha** | 只有搜索：Web Search `/v1/web-search`、AI Search；没查到独立抓取接口（`summary` 返回长摘要） | Web Search 目录价 ¥0.036/次（¥36/千次），AI Search ¥0.06/次；按调用量阶梯定价 | `include`、`exclude`（多个域名用 `\|` 或 `,` 分隔） | `freshness`（如 oneDay、oneWeek、oneYear） | name、url、snippet、summary、siteName、datePublished（UTC+8） | 价格：官方产品文档 PDF（华为云市场托管）；套餐包价格（¥3.6/千次体验包等）：社区 |
| **秘塔 Metaso** | 分开：`/api/v1/search`、`/api/v1/reader`（另有问答接口） | 搜索 ¥0.03/次（官方公众号公告）；reader 价格：待核实 | 待核实（参数有 scope：网页/文库等） | 待核实 | 待核实 | 官方公告 + 社区教程 |
| **Perplexity Search API** | 只有搜索 `POST /search`，可附带页面正文片段 | $5/1k 成功请求；`search_type:"fast"` 为 $1/1k；一次请求最多带 5 个 query，按 1 次计费；失败、限流不收费，空结果照收 | `search_domain_filter`（≤20 个域名，前缀 `-` 表示排除，可带路径） | `search_recency_filter`（day/week/month/year）、日期区间 | title、url、snippet、date | 官方 |
| **阿里云 IQS**（补充） | 搜索 | 社区报告：Generic ¥30/千次，LiteAdvanced ¥12/千次 | 待核实 | TimeRange（社区） | 带发布时间的 markdown（社区） | 社区，待核实 |

## 2. 中文社区站点覆盖（淘股吧 tgb.cn、雪球 xueqiu.com、东方财富股吧 guba.eastmoney.com）

- **没有一家**在官方文档里公布这三个站点的收录情况。下面每一家对这三个站的覆盖都是**待核实**。
- **社区**：threetwoa 的博客在 2026-08-08 用真实 key 测过。结论是中文时效性 Bocha > 阿里云 IQS > Tavily > Exa；Tavily 搜中文多返回聚合页；Exa 能命中官方来源，但正文常被 WAF 截断。测的是天气这类通用中文查询，不是股吧，只能参考。
- **实测（2026-10-17，box 网络）**：
  - 直接 curl：淘股吧首页、东财股吧 `list,600519.html` 都返回 200，HTML 正常。雪球首页返回 200，但内容是**阿里云 WAF 的 JS 挑战页**（`aliyun_waf`、`renderData`），没有正文。所以任何不执行 JS 的抓取方式拿雪球都会失败。
  - Jina Reader 匿名请求（`r.jina.ai/<url>`）：三个站都返回 **401 AuthenticationRequiredError**，原因是 box 出口 ASN（AS54113）信誉差，被拒绝匿名访问。所以 Jina 能不能读这三个站，这次**没测出来，待核实**（需要免费 key，或换个网络）。
- 推断（未验证）：自建国内索引的博查、秘塔、DeepSeek 收录这三个站的可能性比海外厂商大。海外厂商（Brave、Exa、Tavily）对雪球这种有 WAF 的站，正文抓取大概率受限。要用同一组股票关键词实测后才能下结论。

## 3. 反爬与延迟

- **Brave**（官方，数据引自 AIMultiple）：平均延迟 Brave 669ms、Tavily 998ms、Exa 1.2s、Firecrawl 1.335s、Perplexity 11s。这是 Brave 自己引用的数据，有利益相关，算参考。Brave 用的是自有索引，不回落到 Google 或 Bing。
- **Serper**（官方 FAQ）：一般 1–2 秒，需要重试时 2–4 秒，实时查 Google，不缓存。Ultimate 档 300 QPS。
- **Jina Reader**（官方）：平均延迟 Reader 7.9s、Search 2.5s。官方明确表示**不绕过反爬**，付费 key 也不能多访问被封的网站。支持 `X-Engine`（direct 或浏览器渲染）、`X-Set-Cookie` 转发 cookie、`X-Proxy-Url` 走自己的代理，同一 URL 5 分钟内走缓存。无 key 限 20 RPM。
- **Firecrawl**（官方）：按套餐限制并发浏览器数和 RPM（免费档 2 个并发浏览器、10 次/分钟）。scrape 遇到 403 也收费，对强 WAF 站点要注意成本。
- **Exa**（社区）：中文官方站点的正文常被 WAF 截断。
- **博查**（社区）：没充值的账号限 1 QPS、30 QPM、每天 1000 次。
- **DeepSeek**：每个账号每秒 5 次，Fetch 对目标域名另有限速（官方）。

## 4. 各家简评

- **Tavily**：搜索和抽取分开，domain 和日期过滤都齐全（官方），中文偏弱（社区）。适合英文和 X 相关的补充。
- **Serper**：标价最便宜的 Google SERP（$0.30–1.00/1k），`site:` 语法直接可用。只给链接和摘要，正文要另外抓。依赖 Google，合规和长期可用性有风险，算推断。
- **Brave**：自有索引，延迟低，Goggles 能定制站点集合。中文覆盖没有数据，待核实。
- **Exa**：语义搜索强，contents 每 1k 页 $1，是抓取里最便宜的之一。中文和 WAF 站点表现差（社区）。
- **Firecrawl**：抓取能力最全（渲染、crawl、交互），搜索可以顺带抓正文，但每 10 条结果 2 credit，加上 scrape，成本要叠加算。
- **Jina**：Reader 适合把已知 URL 转成 Markdown，可以转发 cookie 和走代理。`s.jina.ai` 每次至少 1 万 token，按 token 计费，单价待核实。
- **博查**：中文最常被推荐，字段里有 datePublished、siteName，有 include 域名过滤。没有独立的抓取接口。
- **秘塔**：搜索 ¥0.03/次，reader 是独立接口，参数和字段细节待核实。
- **Perplexity**：fast 模式 $1/1k，域名过滤最多 20 个，不提供抓取。

## 5. 给 aihot 项目的建议

1. **主路线用 DeepSeek Search/Fetch，备选用博查**。两家都是中文索引，都支持 `site:` 或 `include`，都返回发布时间。用法：`site:tgb.cn`、`site:guba.eastmoney.com` 加题材关键词，按小时级发现新帖。分钟级的快讯仍然交给现有的财联社和同花顺爬虫，搜索 API 只做补充和补漏。
2. **雪球单独处理**：直接抓会遇到阿里云 WAF 的 JS 挑战（实测）。通用 Reader 或 Fetch 很可能拿不到正文。建议只用搜索结果里的标题和摘要做发现信号，正文继续走现有方案，或者只抓用户已登录可见的数据。是否合规由项目自行判断。
3. **海外厂商只做专项**：X 和英文资讯用 Tavily 或 Brave（domain 和时间过滤成熟）。要大批量抓已知 URL 正文，可以考虑 Exa contents（$1/1k 页）或 Jina Reader，但都要先确认能不能访问这三个中文站。
4. **上线前做一次小样本实测**，建议 50 个关键词 × 3 个站。对比 DeepSeek、博查、秘塔三家的命中数、发布时间延迟（帖子发出到能搜到的时间）、去重率和失败率，用免费额度就够。没做这个实测之前，“哪家对股吧收录最好”**不能下结论**。

## 6. 来源

- DeepSeek：/workspace/aihot_research/deepseek_search_fetch_integration.md；https://api-docs.deepseek.com/zh-cn/guides/search/
- Tavily：https://docs.tavily.com/documentation/api-credits ；https://docs.tavily.com/documentation/api-reference/endpoint/search ；https://docs.tavily.com/documentation/best-practices/best-practices-search
- Serper：https://serper.dev/ （官网定价和 FAQ）；第三方：https://serpprices.com/provider/serper ；https://coldiq.com/blog/serper-pricing ；scrape 接口：https://apis.io/apis/serper/serper-webpage-scrape-api/
- Brave：https://brave.com/search/api/ ；https://api-dashboard.search.brave.com/documentation/resources/search-operators ；https://api-dashboard.search.brave.com/app/documentation/web-search/query
- Exa：https://exa.ai/pricing ；https://exa.ai/docs/reference/search
- Firecrawl：https://www.firecrawl.dev/pricing ；https://docs.firecrawl.dev/features/search ；https://docs.firecrawl.dev/api-reference/endpoint/search
- Jina：https://jina.ai/reader/ ；https://jina.ai/api-dashboard/pricing/ ；https://github.com/jina-ai/reader
- 博查：https://open.bochaai.com/ ；官方产品文档 PDF：https://mkp-res.hc-cdn.com/marketplace/public/appv2/attachment/FE5/A96/96F/0000000000FE5A9696F.20250527042304.feac985174234808a69f64e899bd6792.pdf ；参数：https://docs.console.zenlayer.com/api/cn/ai/mcpg/web-search/bochaai ；套餐（社区）：https://github.com/EitanWong/search-gateway/blob/main/docs/bocha-pricing.md
- 秘塔：https://mp.weixin.qq.com/s/AKYOZfBM_Ph0OiIj_8lCeg （官方公告）；https://gongfang.ai/course/mita-guide/03-di-san-bu-fen-gong-neng-xiang-jie/16-16.-16.-api%EF%BC%88kai-fa-zhe-jie-kou%EF%BC%89 （社区教程）
- Perplexity：https://docs.perplexity.ai/docs/getting-started/pricing ；https://docs.perplexity.ai/docs/search/quickstart ；https://docs.perplexity.ai/docs/search/fast-search
- 社区实测：https://www.threetwoa.live/posts/ai-search-api-comparison/ （2026-08-08）
- 实测记录（2026-10-17，box）：Jina 匿名返回 401（AS54113）；雪球首页返回阿里云 WAF 挑战页；淘股吧和东财股吧直连 200。原始返回存放在 /workspace/aihot_research/jina_checks/
