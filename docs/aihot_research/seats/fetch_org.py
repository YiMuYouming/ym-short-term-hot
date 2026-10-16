# 东财 机构专用 上榜明细（RPT_ORGANIZATION_TRADE_DETAILS），近6个月
import json,urllib.request,urllib.parse,time
B="https://datacenter-web.eastmoney.com/api/data/v1/get"
f=urllib.parse.quote("(TRADE_DATE>='2026-04-16')")
rows=[];p=1;pages=1
while p<=pages:
  u=f"{B}?reportName=RPT_ORGANIZATION_TRADE_DETAILS&columns=ALL&pageSize=500&pageNumber={p}&source=WEB&client=WEB&sortColumns=TRADE_DATE,SECURITY_CODE&sortTypes=-1,1&filter={f}"
  for t in range(3):
    try: d=json.load(urllib.request.urlopen(u,timeout=20)); break
    except Exception: time.sleep(2)
  pages=d['result']['pages']; rows+=d['result']['data']; p+=1
json.dump(rows,open('/tmp/org_6m.json','w'),ensure_ascii=False); print("done",len(rows),pages)
