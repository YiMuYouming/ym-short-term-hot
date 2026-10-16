# global_mapping/：海外催化 → A股映射（第六波）

- `overseas_to_ashare.json`：42 条链条。字段：trigger_id、overseas_catalyst{subject, us_ticker, x_signal_keywords}、transmission_logic、ashare_themes[]、core_stocks[]{code, symbol, name, role, nicknames, mapping_reason, mapping_basis}。
- 覆盖：英伟达(财报/CPO/电源/对华管制/铜缆)、存储、台积电、博通、谷歌、云厂商资本开支、OpenAI(模型/Stargate)、AI Agent、Meta、特斯拉(Optimus/飞行汽车/FSD/储能)、苹果与 AI 眼镜、SpaceX、Neuralink、xAI、量子(IONQ/RGTI)、核电(OKLO/CEG)与核聚变、QS 固态电池、创新药 BD、流感、JOBY、黄金、铜铝、原油航运、关税自主可控、稀土、汇率、美联储、稳定币、谷子 IP、造船港口费、光伏、宠物。

## 核实状态
- **代码与简称**：全部用东财 suggest 接口实测核对，日志在 `../logs/code_verify_log.json`。ST 股按规则剔除，见 `../logs/excluded_codes.json`。
- **mapping_basis**：
  - 7 只标“公开报道/公司披露”：中际旭创、新易盛（光模块供应）；三花智控、拓普集团、旭升集团（2026 年媒体报道的 Optimus 供应链，含泰国建厂）；立讯精密、蓝思科技（苹果长期供应商）。
  - 其余都标“社区常见映射—待核实”，没有逐条找互动易或公告佐证。
- **transmission_logic**：主观推演。
- **nicknames**：没有做抽样，留空。

## 缺口
- IONQ_RGTI 只有 2 只股（国盾量子、中天科技），不到 3 只的下限；中天科技的量子业务也待核实。没有为凑数补股票。
- core_stocks 是代表性映射，不是完整受益名单。
