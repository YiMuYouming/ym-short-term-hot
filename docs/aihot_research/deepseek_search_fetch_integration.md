# DeepSeek Search / Fetch API 接入调研

> 调研日期：2026-10-17（Asia/Taipei）
> 来源：DeepSeek 官方文档 https://api-docs.deepseek.com/zh-cn/guides/search/ （本文件写入当日抓取核对）
> 状态标记：文档内容 = 已核对官方文档；**真实请求验证 = 尚未进行（待核实）**，本调研未调用接口、未修改任何代码/配置、未执行 git 操作。

## 1. API 基本信息

| 项 | 内容 | 状态 |
| --- | --- | --- |
| Search | `POST https://api.deepseek.com/v1/tools/search` | 官方文档核对；待核实（未实测） |
| Fetch | `POST https://api.deepseek.com/v1/tools/fetch` | 官方文档核对；待核实（未实测） |
| 鉴权 | `Authorization: Bearer <DeepSeek API Key>`，`Content-Type: application/json`，与现有 DeepSeek 模型 API 共用 Key | 官方文档核对 |
| 数据源 | Search 由 DeepSeek 自研搜索引擎支持；Fetch 抓取单页并返回 Markdown 正文 | 官方文档核对 |

### Search 请求字段
| 字段 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `query` | string | 是 | - | 1～128 个 Unicode 字符，支持搜索语法 |
| `count` | int | 否 | 10 | 1～50，**单次最多 50 条** |
| `ori_question` | string | 否 | - | 触发搜索的原始问题，1～128 字符 |
| `localization` | string | 否 | "" | 用于本地化结果的 IP 地址 |
| `need_content` | bool | 否 | false | 是否返回网页正文 `content` |

### 搜索语法（原样透传）
`site:`（多个用 `OR` 连接）、`-site:`、`-关键词`、`-"短语"`、`"精确短语"`、`lang:zh,en`、`after:2025` / `after:2025-01-01`、`before:...`，可在一个 query 中组合。

### Search 返回字段
`rerank_score`（0～3，≥1.5 为优质）、`title`、`url`、`snippet`（100～200 字）、`summary`（600～800 字，适合喂模型）、`content`（需 need_content）、`site_name`、`site_icon`、`date`（UTC RFC3339，可能为 null）、`authority`（0～4，-1 未知，≥3 极权威）。无匹配时 `results` 为空数组。

### Fetch
请求：`{"url": "..."}`（HTTP/HTTPS，≤8192 字符，不能带用户名密码）。返回：`{"title": "...", "content": "<Markdown 正文>"}`。结果受目标站点可用性与访问策略影响。

## 2. 定价

| API | 计费单位 | 价格 |
| --- | --- | --- |
| Search | 每 1,000 次成功请求 | 5 元 |
| Fetch | 每 1,000 次成功请求 | 5 元 |

- 两者**独立计费**，按次数，不按 token / 条数；`count` 不影响单价。
- 只对 HTTP 200 且有结果的请求计费（Search `results` 非空；Fetch 返回正文）。失败、无结果、超时**不计费**。
- **免费范围更正**：官方说明中，"目前未计费"的只是在 DeepSeek Harness / Claude Code / Codex 里使用 DeepSeek API 时，由**服务端工具调用**自动触发的 Search/Fetch；这部分将于**北京时间 2026-11-01 00:00 起按次收费**。**项目代码直接调用 `/v1/tools/*` 不属于该免费范围，按文档应当即计费**（待以账单实测核实）。
- 成本估算示例：每 5 分钟对 10 个来源各搜一次 ≈ 2,880 次/天 ≈ 14.4 元/天（仅 Search，按全部成功计；实际以成功率为准）。

## 3. 对 aihot_research 的适用场景

目标：用 `site:` 限定社区来源，做实时帖子/资讯发现，作为现有反爬方案（财联社电报 sign 签名、同花顺 hexin-v token 等）的**补充**，而非直接替代。

| 来源 | 建议 query 写法 | 预期适配度 | 状态 |
| --- | --- | --- | --- |
| 淘股吧 | `site:tgb.cn 题材关键词 after:YYYY-MM-DD` | 取决于搜索引擎收录速度 | 待核实 |
| 雪球 | `site:xueqiu.com 个股/题材 after:...` | 同上，雪球部分内容需登录，Fetch 可能 403/404 | 待核实 |
| X | `site:x.com 关键词 lang:zh,en` | X 页面多为动态渲染，收录与 Fetch 正文都存疑 | 待核实 |
| 韭研公社 | `site:jiuyangongshe.com 题材 after:...` | 同上 | 待核实 |
| 财联社 / 同花顺 | `site:cls.cn` / `site:10jqka.com.cn` | 可作为电报/快讯的**交叉校验**来源 | 待核实 |

判断要点：
- **时效性**：搜索引擎有收录延迟，分钟级的电报流仍应以现有直连方案为主；Search 更适合"小时级题材发现、补漏、溯源"。
- **替代价值**：Fetch 可把单条 URL 转成 Markdown，减少自己维护 HTML 解析的工作；但对需要签名/登录的接口型数据（如电报列表 API、hexin-v 接口）**不能替代**。
- **用于验证**：配合项目"禁止编造、必须标注来源"的要求，Search 的 `url` + `date` + `authority` 可作为情报溯源字段。

## 4. 示例请求与预期返回

### 示例 A：限定社区来源搜题材
```json
POST https://api.deepseek.com/v1/tools/search
{
  "query": "机器人 题材 site:tgb.cn OR site:jiuyangongshe.com OR site:xueqiu.com lang:zh after:2026-10-16",
  "count": 20,
  "ori_question": "今天机器人题材社区热度如何",
  "need_content": false
}
```
预期返回（结构依官方文档，内容为示意）：
```json
{
  "results": [
    {
      "rerank_score": 2.1,
      "title": "<帖子标题>",
      "url": "https://www.tgb.cn/a/<id>",
      "snippet": "<100~200 字短摘要>",
      "summary": "<600~800 字长摘要>",
      "content": "",
      "site_name": "淘股吧",
      "site_icon": "https://.../favicon.ico",
      "date": "2026-10-17T02:30:00+00:00",
      "authority": 2
    }
  ]
}
```

### 示例 B：抓取单帖正文
```json
POST https://api.deepseek.com/v1/tools/fetch
{ "url": "https://www.jiuyangongshe.com/a/<id>" }
```
预期返回：
```json
{ "title": "<页面标题>", "content": "# <标题>\n\n<Markdown 正文>" }
```
失败时为 OpenAI 兼容错误格式，例如 404 表示无可提取正文或被站点策略拦截。

## 5. 接入注意事项

1. **限速**：账号级 Search 5 QPS、Fetch 5 QPS，各自独立，与 API Key 数量无关，与模型并发限制独立；Fetch 另有**按目标域名**的 QPS 限制。超限返回 429 → 需全局令牌桶 + 按域名限流。
2. **重试策略**：408 / 429 / 5xx 退避重试；402 余额不足需充值；其它 4xx 不改请求不要重试（避免浪费）。
3. **去重**：按规范化 URL（去 query/utm、统一 http/https、移动端域名）去重；同一帖多次命中只保留首次 `date`；可再用 `title` + 正文哈希做近似去重。
4. **时间处理**：`date` 是 UTC，入库前转 Asia/Shanghai；`date` 可能为 null，需用抓取时间兜底并标记。
5. **质量过滤**：可先用 `rerank_score ≥ 1.5`、`authority` 阈值过滤；社区帖权威分普遍不高，阈值需实测调整（待核实）。
6. **与现有 pipeline 衔接**：建议作为独立"发现层"数据源，输出统一字段（source=deepseek_search、site、url、title、summary、published_at、fetched_at、query、rerank_score、authority），进入现有题材字典匹配与股票代码校验流程；**股票代码与简称仍须走东方财富等接口核对**，不能直接信任帖子文本。
7. **成本控制**：控制 query 数量与轮询频率；`count` 拉满不加价，宜一次取足再本地过滤；Fetch 只对通过初筛的 URL 调用。
8. **合规与可用性**：Fetch 结果受目标站点策略影响，登录墙/动态页面（雪球部分页面、X）可能拿不到正文；不应绕过站点访问控制。
9. **待实测清单**（真实请求验证前均为待核实）：各 site 的收录延迟、命中量、Fetch 成功率、直接调用当前是否计费、`localization` 对中文结果的影响。
