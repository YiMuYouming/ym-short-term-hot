# YM-ShortTerm-Hot (弈沐 A 股短线热点与社区舆情雷达)

[弈沐资本导航](../README.md) · [当前进度](PROGRESS.md) · [实施与验收计划](docs/实施与验收计划.md) · [SH-01 开工单](docs/开工单-SH01-基座与短线KnowHow-2026-10-16.md) · [AIHOT 上游原文档](docs/upstream/AIHOT-README.md)

> **独立项目声明**：本仓库是 `/Users/yimu/Projects/YM_Capital/ym-short-term-hot` 下的**独立一级工程**，与 `live-dashboard`（8088）完全解耦，不共用进程、数据库或前端代码。默认 Web/API 端口规划为 `3088`。
> **引擎底座**：基于开源框架 [`KKKKhazix/AIHOT`](https://github.com/KKKKhazix/AIHOT)（上游基线 commit `c8704e5313e6b051560365226b3919d7e0ada5ea`）构建；底层结构化行情、同花顺/东财热榜、涨跌停池与开盘啦题材统一通过 [`YM-data-pipeline`](../YM-data-pipeline/README.md) 公共契约获取。

---

## 1. 项目定位与核心价值

**YM-ShortTerm-Hot** 是专为 A 股超短线交易（连板接力、龙头博弈、主线题材掘金）打造的**跨平台热门股发现与社区评论情绪自动分类平台**。

系统将短线交易员日常盯盘与复盘分散在 5~6 个 App 的动作收敛为一个自动化闭环：
1. **硬事实与题材骨架（100% 由 `YM-data-pipeline` 驱动）**：
   - 自动拉取**同花顺热榜 (`ths_hot`)、东方财富人气榜 (`dc_hot`)、开盘啦涨停榜单与正宗题材分类 (`kpl_list`/`kpl_concept`)、同花顺涨停原因解读 (`limit_list_ths`)、连板天梯 (`limit_step`)**，合并去重锁定当日最核心的 **25~40 只焦点股**；
2. **软舆情与社区评论靶向采集（Python `bridge/`）**：
   - 绝不全市场盲爬，仅针对焦点股与核心题材，定向采集第一批三大短线社区：
     - **东方财富股吧 (`guba.eastmoney.com`)**：个股实时评论流、15m/60m 盖楼流速、散户多空情绪；
     - **淘股吧 (`tgb.cn`)**：24h 热门文章榜/精华复盘贴、超短游资接力跟帖与分歧态度；
     - **雪球 (`xueqiu.com`)**：热股讨论榜、个股深度逻辑拆解与高赞评论；
3. **AIHOT 双轨精选与事件聚簇（不动引擎核心，只配 `industry/` 与 `site/`）**：
   - **长文/高信息密度内容 (`participation_mode: "editorial"`)**：淘股吧 24h 热帖、雪球长逻辑、涨停归因进入精选流，经两次独立打分、结构化抽取（抽关联股票/题材/连板身位）与同题材/同股事件聚簇；
   - **高频短评脉冲 (`participation_mode: "hot_signal"`)**：东财股吧盖楼、个股短评作为“大家在吵什么”的热度证据注入事件，**只算热度与分歧度、绝不刷屏精选流**；
4. **短线专属双视图看板（`modules/short-term-radar/` 扩展模块）**：
   - **默认视图 `[🧩 题材主线梯队视图]`**：按开盘啦/同花顺题材归类今日主线，组内按 `👑 空间龙 -> ⚔️ 20cm弹性 -> 🐘 容量中军 -> 🌱 首板跟风` 排布，展示评论流速与 `【高度一致·警惕兑现】` / `【良性分歧·换手博弈】` 状态胶囊；
   - **切换视图 `[🔥 跨平台人气共振 Top 30 榜]`**：同屏对比同花顺、东财、淘股吧、雪球四端热度排名与 15 分钟评论增速斜率；
   - **个股舆情抽屉**：点击展开「硬事实（涨停原因/题材身位） + 软舆情（多空观点对照表 + 三大社区高赞原话直达）」。

---

## 2. 目录结构与职责边界

系统严格遵守 AIHOT 的模块边界（由 `tests/architecture.test.ts` 强校验），**禁止在 `packages/backend/` 写死业务定制逻辑**，所有开发集中在 `site/`、`industry/`、`modules/short-term-radar/` 与 `bridge/`：

```text
ym-short-term-hot/
├── README.md                       # 本交接说明文档
├── AGENTS.md                       # Agent 角色分工、开发铁律与审计门禁
├── PROGRESS.md                     # 唯一活动工程进度板（遵循 ../shared/progress-workflow.md）
├── docs/
│   ├── 实施与验收计划.md           # 第一期（SH-01 ~ SH-03）及后续阶段完整蓝图
│   ├── 开工单-*.md                 # 各阶段具体开工单（谷米签发，稳米执行）
│   ├── evidence/                   # 各阶段测试、构建与回读证据目录
│   └── upstream/                   # AIHOT 上游原始 README 与 AGENTS 备份
├── site/                           # 站点身份配置 (site.ts, models.ts, modules/ 注册表)
├── industry/                       # A股短线行业知识包
│   ├── taxonomy.ts                 # 6大短线分类、连板/题材标签词表、核心股票/题材实体
│   ├── topics.json                 # 主题目录（核心题材、人气龙头、游资视角）
│   ├── selection.ts                # T1/T1_5/T2 精选入选门槛
│   ├── sources.json                # 初始信源配置
│   └── prompts/                    # 短线五维评分 (selection-score.md)、结构抽取 (structure.md) 等提示词
├── modules/
│   └── short-term-radar/           # 【SH-03 实施】@aihot/short-term-radar 扩展模块
│       ├── module.ts               # 模块路由声明 (/radar, /api/site/radar/*)
│       ├── server.ts               # 后端接口、雷达快照入库、定时任务与 MCP 工具
│       ├── web.tsx                 # 双视图前端组件（题材主线梯队 ⇄ 跨平台人气共振 Top 30 + 舆情抽屉）
│       ├── migrations/             # 模块专属表 (0001_radar_tables.sql)
│       └── tests/                  # 模块前后端自动化测试
├── bridge/                         # 【SH-02 实施】Python 采集与管道桥接层
│   ├── pyproject.toml              # Python 依赖与测试配置
│   ├── run_bridge.py               # 定时/单次执行入口（盘中 15m 滚动 / 盘前 08:30 / 盘后 15:35）
│   ├── pipeline_client.py          # 调用 /Users/yimu/Projects/YM_Capital/YM-data-pipeline 公共入口
│   ├── collectors/                 # 东财股吧、淘股吧、雪球三大社区靶向采集器
│   ├── synthesizer.py              # 评论清洗、盖楼流速计算、多空分歧提炼与 /api/ingest/items 推送
│   └── tests/                      # 离线 Fixture 单元测试（不联网、不耗额度）
├── apps/                           # AIHOT 原生三进程 (api / worker / web)
├── packages/                       # AIHOT 原生共享后端与类型契约 (backend / contracts)
└── database/migrations/            # AIHOT 原生 PostgreSQL 迁移文件
```

---

## 3. 角色分工与阶段闭环流程

本项目采用 **「谷米规划审计 + 稳米分阶段实施」** 的双 Agent 协作机制：
1. **谷米（规划与审计方）**：负责架构设计、签发阶段开工单（`SH-01` → `SH-02` → `SH-03`），并在每个阶段交付后执行代码、测试与契约独立审计；
2. **稳米（实施方）**：严格按当前生效的唯一开工单施工，完成本阶段代码、测试与 `docs/evidence/<单号>/` 证据落盘，更新 `PROGRESS.md` 后**立即停下等待谷米审计**，不跨阶段抢跑。

---

## 4. 验收与测试门禁

每次阶段交付前，必须通过以下对应的检查命令并留存输出证据：

```bash
# 1. TypeScript 类型检查与架构边界检查
npm run typecheck

# 2. 后端与模块全量测试（库名必须以 _test 或 _ci 结尾，测试完全离线，不访问外部服务）
DATABASE_URL=postgres://127.0.0.1:5432/ymhot_test npm test

# 3. Web 前端构建与路由测试
npm run build -w @aihot/web && node --test apps/web/tests/*.test.ts

# 4. Python Bridge 离线单元测试（SH-02 起启用）
cd bridge && uv run python -m unittest discover -s tests -v
```
