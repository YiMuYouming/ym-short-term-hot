import json,sys
sys.path.insert(0,'dict'); sys.path.insert(0,'global_mapping')
from themes_v2_src import ADD_TO_OLD,NEW
from chains_src import C
EXTRA=json.load(open('global_mapping/extra_src.json'))
L=json.load(open('logs/code_verify_log.json'))
excluded=[]
def ok(c,n):
  v=L[c]
  if v['st_flag']: excluded.append({"code":c,"name":n,"reason":f"东财现简称 {v['eastmoney_name']}(ST)，按规则剔除"}); return None
  name=v['eastmoney_name']
  note=None
  if name.startswith('XD'): name=n; note=f"东财当日显示 {v['eastmoney_name']}(除息前缀)，简称仍为 {n}"
  elif name!=n: note=f"原写 {n}，东财最新简称 {name}"
  return name,note
def stock(c,n,role,extra=None):
  r=ok(c,n)
  if not r: return None
  d={"code":c,"name":r[0],"code_name_status":"已核实(东财suggest，logs/code_verify_log.json)","role":role,"role_note":"主观归类"}
  if r[1]: d["name_note"]=r[1]
  if extra: d.update(extra)
  return d
old=json.load(open('dict/themes.json'))
v2=[]
for t in old:
  t=json.loads(json.dumps(t))
  for c,n,role in ADD_TO_OLD.get(t['standard_name'],[]):
    s=stock(c,n,role,{"nicknames":[]})
    if s and c not in [x['code'] for x in t['representative_stocks']]: t['representative_stocks'].append(s)
  t['source']="v1"; v2.append(t)
for name,al,st in NEW:
  ss=[s for s in (stock(c,n,r,{"nicknames":[]}) for c,n,r in st) if s]
  v2.append({"standard_name":name,"aliases":al,"representative_stocks":ss,"source":"v2新增","aliases_status":"常见用语，未逐词做股吧抽样"})
json.dump(v2,open('dict/themes_v2.json','w'),ensure_ascii=False,indent=1)
out=[]
for tid,subj,tk,kw,logic,themes,stocks in C:
  sl=list(stocks)+[tuple(x) for x in EXTRA.get(tid,[])]
  cs=[]
  for c,n,role,reason,basis in sl:
    s=stock(c,n,role)
    if s:
      s.update({"symbol":(c+(".SH" if c.startswith('6') else ".SZ")),"nicknames":[],"mapping_reason":reason,"mapping_basis":basis}); cs.append(s)
  out.append({"trigger_id":tid,"overseas_catalyst":{"subject":subj,"us_ticker":tk,"x_signal_keywords":kw},"transmission_logic":logic,"transmission_logic_status":"主观推演","ashare_themes":themes.split(';'),"core_stocks":cs,"core_stock_count_ok":3<=len(cs)<=6})
json.dump(out,open('global_mapping/overseas_to_ashare.json','w'),ensure_ascii=False,indent=1)
json.dump(excluded,open('logs/excluded_codes.json','w'),ensure_ascii=False,indent=1)
ns=sum(len(t['representative_stocks']) for t in v2); uniq=len({s['code'] for t in v2 for s in t['representative_stocks']})
print("themes",len(v2),"stocks",ns,"unique",uniq,"chains",len(out),"short",[o['trigger_id'] for o in out if not o['core_stock_count_ok']],"excluded",excluded)
print("basis P",sum(1 for o in out for s in o['core_stocks'] if s['mapping_basis'].startswith('公开')))
