# 拉取东财龙虎榜营业部明细（近一年）用于席位佐证与次日溢价统计
import json,urllib.request,urllib.parse,time,sys
B="https://datacenter-web.eastmoney.com/api/data/v1/get"
f=urllib.parse.quote("(TRADE_DATE>='2025-10-16')")
rows=[]
for p in range(1,264):
  u=f"{B}?reportName=RPT_OPERATEDEPT_TRADE_DETAILS&columns=OPERATEDEPT_CODE,OPERATEDEPT_NAME,TRADE_DATE,SECURITY_CODE,SECURITY_NAME_ABBR,ACT_BUY,ACT_SELL,NET_AMT,D1_CLOSE_ADJCHRATE&pageSize=500&pageNumber={p}&source=WEB&client=WEB&sortColumns=TRADE_DATE,SECURITY_CODE&sortTypes=-1,1&filter={f}"
  for t in range(3):
    try: d=json.load(urllib.request.urlopen(u,timeout=20)); break
    except Exception as e: time.sleep(2)
  rows+=d['result']['data'] or []
  if p%20==0: print(p,len(rows),flush=True)
json.dump(rows,open('/tmp/lhb_1y.json','w'),ensure_ascii=False)
print("done",len(rows))
