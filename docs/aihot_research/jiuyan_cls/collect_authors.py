# 从韭研公社首页与文章页收集作者主页 /u/<32hex>，再请求主页取昵称（真实请求验证）
import re,urllib.request,json,time,collections
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
def get(u):
  try:
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=12); return r.status,r.read().decode('utf-8','ignore')
  except Exception as e: return getattr(e,'code',0),''
s,h=get("https://www.jiuyangongshe.com/")
ids=collections.Counter(re.findall(r'/u/([0-9a-f]{32})',h)+re.findall(r'"([0-9a-f]{32})"',h))
arts=list(dict.fromkeys(re.findall(r'href="(/a/[0-9a-z]+)"',h)))[:40]
art_info=[]
for a in arts:
  s2,ah=get("https://www.jiuyangongshe.com"+a)
  t=re.search(r'<title>([^<]*)',ah); au=re.findall(r'/u/([0-9a-f]{32})',ah)
  art_info.append({"url":"https://www.jiuyangongshe.com"+a,"status":s2,"title":t.group(1) if t else None,"author_ids":list(dict.fromkeys(au))[:3]})
  for x in au: ids[x]+=1
  time.sleep(0.3)
users={}
for uid,_ in ids.most_common(120):
  s3,uh=get(f"https://www.jiuyangongshe.com/u/{uid}")
  t=re.search(r'<title>([^<]*)',uh)
  if s3==200 and t and '韭研' in t.group(1):
    users[uid]={"status":s3,"title":t.group(1)}
  time.sleep(0.2)
json.dump({"articles":art_info,"users":users},open('/workspace/aihot_research/jiuyan_cls/authors_raw.json','w'),ensure_ascii=False,indent=1)
print(len(art_info),len(users))
for k,v in list(users.items())[:80]: print(k,v['title'])
