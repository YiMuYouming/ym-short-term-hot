# jiuyan_cls/：韭研公社与快讯源（第五波）

## 文件
- `fast_news_endpoints.json`：17 条端点实测记录（HTTP 状态码、字段、样本、核实状态）。
- `jiuyan_authors.json`：27 位韭研作者（昵称、32 位 ID、主页、赛道/风格、代表作链接）。主页全部 HTTP 200 实测；赛道是根据 2026-10-16 首页抽样文章标题归纳的。逻辑挖掘王、超前一步只在首页榜单出现过，赛道待核实。
- `collect_authors.py` / `authors_raw.json`：采集脚本和原始结果（39 篇文章、118 个用户主页）。
- `probe_log_partial.md`：首轮探测日志。

## 结论
- **可以直接免鉴权用（真实请求验证）**：
  - 选股宝 `flash-api` 的异动股、涨停炸板分时、板块排行；
  - 华尔街见闻 `api-one.wallstcn.com` 的 lives 快讯；
  - 同花顺 `news.10jqka.com.cn/tapp/news/push/stock/`；
  - 韭研公社 SSR 页面：首页、文章 `/a/{id}`、用户 `/u/{id}`。
- **财联社**：电报列表接口返回 `errno 10012 签名错误`，需要前端 JS 生成的 sign 参数。
- **韭研公社异动解析**：`/action` 的 SSR 只返回空骨架，数据由带签名的 XHR 加载；App 接口返回“版本过低”。

## 需浏览器实测的 URL 清单
1. https://www.jiuyangongshe.com/action ：抓异动数据的真实 XHR，包括请求头、签名字段和 token 来源（state.mQ7vL2xR9a.digest）。
2. https://www.jiuyangongshe.com/hotsearch 、/theme 、/study 、/search?k=… ：curl 请求 302 回首页，需确认登录态和真实路径。
3. 韭研公社文章的点赞数、阅读数字段（判断高赞长帖），以及排序/列表 XHR。
4. https://www.cls.cn/telegraph ：抓 get_roll_list 或 updateTelegraphList 的 sign 生成方式和真实参数。
5. 选股宝快讯（xuangubao.cn 前端）：确认现在用的快讯 API 域名（api.xuangubao.cn、baoer-api 均连接失败）。
6. 同花顺盘中异动（如 q.10jqka.com.cn 或 data.10jqka.com.cn 的异动页）：找真实 XHR。

## 限流
- 本次请求量很低（韭研约 160 次，每次间隔 0.2~0.3 秒），没有遇到 429 或封禁。
- 实际限流阈值待核实。

## 浏览器实测合并（2026-10-16 约 18:45 台北时间，未登录）
- **韭研 /action**：未登录显示 0 条，没有发现异动专用 XHR，待交易日或登录后复测。
- **韭研 web-api**：页面的 XHR 全部是 POST `web-api.jiuyangongshe.com/jystock-app/api/...`（word-cloud、user/info、timeline/news、article/rank-board 等），返回 200 但未登录时响应体为空。请求头有 timestamp、token、platform，另有一个签名头，头名未记录。
- **韭研文章列表**：SSR，可直接用 curl 解析（已用 curl 验证 /study_hot：39 篇，计数可按图标 class 取）：
  - `/study_publish` 最新发布
  - `/study_hot` 最新热度
  - `/study_action` 最新互动
  - `/study_30` 30 天热度

  选择器见 fast_news_endpoints.json。图标对应关系：forward=转发、reply=评论、fabulous=点赞、integral=积分。
- **财联社**：`/api/cache?app=CailianpressWeb&name=telegraph&os=web&sv=8.7.9` 目前不校验 sign（错误 sign、空 sign、不带 sign 都返回数据），所以可以免签名拉电报。这也意味着“sha1 再 md5”的说法无法通过此接口验证，仍待核实。`/v1/roll/get_roll_list` 仍报签名错误。
- **同花顺**：7x24 pagesize=400 时浏览器带了 hexin-v 反爬头；curl 小页不带该头也能取到。资金流 JSONP `pop.10jqka.com.cn/getcashflow.php` 只做了浏览器验证。盘中异动专页未找到。
- **选股宝**：网页端空白、没有快讯通道，待核实是否已迁移到 App。

### 仍需浏览器或登录实测
1. 交易日盘中或登录后的韭研 /action 异动数据请求。
2. web-api 的签名头名称与算法。
3. 财联社 get_roll_list 的签名生成方式。
4. 同花顺盘中异动页。
5. 选股宝快讯现在走的通道。
