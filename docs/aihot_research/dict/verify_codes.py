# 批量核对股票代码与最新简称：东财 searchapi suggest（真实请求），结果写 logs/code_verify_log.json
import json,urllib.request,time,sys
sys.path.insert(0,'dict'); sys.path.insert(0,'global_mapping')
from themes_v2_src import ADD_TO_OLD,NEW
from chains_src import C
EXTRA={"Gold_price":[("000975","山金国际","容量中军","黄金","社区常见映射—待核实")],"Pharma_BD":[("600196","复星医药","容量中军","创新药","社区常见映射—待核实")],
"Fed_rates":[("300033","同花顺","容量中军","风险偏好","社区常见映射—待核实")],"Stablecoin":[("600570","恒生电子","容量中军","金融IT","社区常见映射—待核实")],
"Meta_Llama":[("002230","科大讯飞","容量中军","大模型","社区常见映射—待核实")],"Shipbuilding_US":[("600685","中船防务","容量中军","造船","社区常见映射—待核实")],
"Pets_US":[("301498","乖宝宠物","容量中军","宠物食品","社区常见映射—待核实")],"Fusion_news":[("600875","东方电气","容量中军","聚变/核电装备","社区常见映射—待核实")]}
old=json.load(open('dict/themes.json'))
codes={}
for t in old:
  for s in t['representative_stocks']: codes[s['code']]=s['name']
for v in ADD_TO_OLD.values():
  for c,n,_ in v: codes[c]=n
for _,_,st in NEW:
  for c,n,_ in st: codes[c]=n
for ch in C:
  for s in ch[6]: codes[s[0]]=s[1]
for v in EXTRA.values():
  for s in v: codes[s[0]]=s[1]
log={}
for c,n in sorted(codes.items()):
  u=f"https://searchapi.eastmoney.com/api/suggest/get?input={c}&type=14&token=D43BF722C8E33BDC906FB84D85E326E8&count=5"
  for t in range(3):
    try: d=json.load(urllib.request.urlopen(u,timeout=10)); break
    except Exception as e: d=None; time.sleep(1)
  m=[x for x in ((d or {}).get('QuotationCodeTable',{}).get('Data') or []) if x['Code']==c and x.get('SecurityTypeName','') in ('沪A','深A','科创板','京A','创业板') or (x['Code']==c and x.get('Classify') in ('AStock','23'))]
  real=m[0]['Name'].replace(' ','') if m else None
  log[c]={"expected":n,"eastmoney_name":real,"security_type":m[0].get('SecurityTypeName') if m else None,"match":real==n,"st_flag":bool(real and 'ST' in real),"http_ok":d is not None}
  time.sleep(0.15)
json.dump(log,open('logs/code_verify_log.json','w'),ensure_ascii=False,indent=1)
json.dump(EXTRA,open('global_mapping/extra_src.json','w'),ensure_ascii=False)
bad={k:v for k,v in log.items() if not v['match']}
print(len(log),"mismatch",len(bad)); print(json.dumps(bad,ensure_ascii=False))
