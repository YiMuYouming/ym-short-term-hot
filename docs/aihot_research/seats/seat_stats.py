# 席位统计：近6个月(2026-04-16~2026-10-16) 东财 RPT_OPERATEDEPT_TRADE_DETAILS / RPT_ORGANIZATION_TRADE_DETAILS
import json,gzip,collections,statistics as st
R=json.load(gzip.open('lhb_operatedept_1y.json.gz'))
R=[r for r in R if r['TRADE_DATE']>='2026-04-16']
def board(c):
  if c.startswith(('60','00')): return '主板'
  if c.startswith('30'): return '创业板'
  if c.startswith('68'): return '科创板'
  if c.startswith(('92','8','4')): return '北交所'
  return '其他'
def q(v,p):
  v=sorted(v); return round(v[int(p*(len(v)-1))],3) if v else None
by=collections.defaultdict(list)
for r in R: by[r['OPERATEDEPT_NAME']].append(r)
out={}
for n,L in by.items():
  if len(L)<3: continue
  b=[r['ACT_BUY'] or 0 for r in L]; s=[r['ACT_SELL'] or 0 for r in L]
  two=[(x,y) for x,y in zip(b,s) if x>0 and y>0]
  ratio=[min(x,y)/max(x,y) for x,y in two]
  bd=collections.Counter(board(r['SECURITY_CODE']) for r in L)
  days=collections.defaultdict(lambda:collections.Counter())
  for r in L: days[r['TRADE_DATE'][:10]][board(r['SECURITY_CODE'])]+=1
  multi=sum(1 for d in days.values() if sum(d.values())>=3)/len(days)
  multi_sameboard=sum(1 for d in days.values() if max(d.values())>=3)/len(days)
  nb=[r for r in L if (r['NET_AMT'] or 0)>0 and r['D1_CLOSE_ADJCHRATE'] is not None]
  d1=[r['D1_CLOSE_ADJCHRATE'] for r in nb]
  out[n]={"records_6m":len(L),"active_days":len(days),"two_way_share":round(len(two)/len(L),3),
   "two_way_min_max_ratio_p25_p50_p75":[q(ratio,.25),q(ratio,.5),q(ratio,.75)],
   "board_share":{k:round(v/len(L),3) for k,v in bd.most_common()},
   "days_with_ge3_stocks":round(multi,3),"days_with_ge3_same_board":round(multi_sameboard,3),
   "net_buy_records_with_d1":len(nb),"next_day_ret_mean_pct":round(st.mean(d1),2) if d1 else None,"next_day_ret_median_pct":round(st.median(d1),2) if d1 else None,"next_day_up_prob":round(sum(x>0 for x in d1)/len(d1),3) if d1 else None,
   "median_buy_amt_wan":round(st.median([x for x in b if x>0])/1e4,0) if any(b) else None}
json.dump(out,open('stats_operatedept_6m.json','w'),ensure_ascii=False,indent=0)
# 机构专用
O=json.load(open('/tmp/org_6m.json')); json.dump(O,open('org_trade_6m.json','w'),ensure_ascii=False)
def grp(f):
  x=[o for o in O if f(o) and o['D1_CLOSE_ADJCHRATE'] is not None]
  d=[o['D1_CLOSE_ADJCHRATE'] for o in x]
  return {"n":len(x),"d1_mean":round(st.mean(d),2) if d else None,"d1_up_prob":round(sum(v>0 for v in d)/len(d),3) if d else None}
org={"records_6m":len(O),
 "all_net_buy":grp(lambda o:(o['NET_BUY_AMT'] or 0)>0),
 "two_way_close(min/max>=0.6)":grp(lambda o:o['BUY_AMT'] and o['SELL_AMT'] and min(o['BUY_AMT'],o['SELL_AMT'])/max(o['BUY_AMT'],o['SELL_AMT'])>=0.6),
 "pure_buy(sell=0)":grp(lambda o:(o['BUY_AMT'] or 0)>0 and not o['SELL_AMT']),
 "20cm_smallcap(freecap<50亿)_pure_buy_2000-4000万":grp(lambda o:o['SECURITY_CODE'][:2] in('30','68') and (o['FREECAP'] or 999)<50 and not o['SELL_AMT'] and 2e7<=(o['BUY_AMT'] or 0)<=4e7),
 "20cm_smallcap_pure_buy_other_amt":grp(lambda o:o['SECURITY_CODE'][:2] in('30','68') and (o['FREECAP'] or 999)<50 and not o['SELL_AMT'] and not 2e7<=(o['BUY_AMT'] or 0)<=4e7 and (o['BUY_AMT'] or 0)>0),
 "main_board_pure_buy":grp(lambda o:o['SECURITY_CODE'][:2] in('60','00') and (o['BUY_AMT'] or 0)>0 and not o['SELL_AMT']),
 "buy_times>=3_net_buy":grp(lambda o:(o['BUY_TIMES'] or 0)>=3 and (o['NET_BUY_AMT'] or 0)>0),
 "buy_times==1_net_buy":grp(lambda o:(o['BUY_TIMES'] or 0)==1 and (o['NET_BUY_AMT'] or 0)>0)}
# 次日全卖检测: 同一股票次日机构席位再上榜且 SELL>=前日BUY*0.8
idx={(o['SECURITY_CODE'],o['TRADE_DATE'][:10]):o for o in O}
dates=sorted({o['TRADE_DATE'][:10] for o in O}); nxt={d:dates[i+1] for i,d in enumerate(dates[:-1])}
c=0;dump=0
for o in O:
  if o['SECURITY_CODE'][:2] in('30','68') and not o['SELL_AMT'] and 2e7<=(o['BUY_AMT'] or 0)<=4e7 and o['TRADE_DATE'][:10] in nxt:
    c+=1; n2=idx.get((o['SECURITY_CODE'],nxt[o['TRADE_DATE'][:10]]))
    if n2 and (n2['SELL_AMT'] or 0)>=0.8*o['BUY_AMT']: dump+=1
org["20cm_2000-4000万纯买_次日机构席位卖出>=80%_observed"]={"base":c,"observed_dump":dump,"note":"仅当次日该股再次上榜才可观测，下界估计"}
json.dump(org,open('stats_institution_6m.json','w'),ensure_ascii=False,indent=1)
print(len(out)); print(json.dumps(org,ensure_ascii=False))
