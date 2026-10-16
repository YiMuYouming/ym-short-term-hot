import json,gzip,collections
S=json.load(open('stats_operatedept_6m.json'))
R=json.load(gzip.open('lhb_operatedept_1y.json.gz'))
c1y=collections.Counter(r['OPERATEDEPT_NAME'] for r in R)
last=collections.defaultdict(str)
for r in R: last[r['OPERATEDEPT_NAME']]=max(last[r['OPERATEDEPT_NAME']],r['TRADE_DATE'][:10])
def ev(n):
  s=S.get(n,{})
  return {"full_name":n,"lhb_records_1y":c1y.get(n,0),"last_on_list":last.get(n) or None,"stats_6m":s or None,
          "status":"真实请求验证(东财RPT_OPERATEDEPT_TRADE_DETAILS)" if c1y.get(n) else "近1年未上榜—待核实"}
def bias(names):
  v=[(S[n]['next_day_ret_mean_pct'],S[n]['net_buy_records_with_d1']) for n in names if n in S and S[n]['next_day_ret_mean_pct'] is not None]
  if not v or sum(w for _,w in v)==0: return None,None
  m=sum(a*w for a,w in v)/sum(w for _,w in v); return round(max(-1,min(1,m/3)),2),round(m,2)
def board_pref(names):
  agg=collections.Counter()
  for n in names:
    for k,v in (S.get(n,{}).get('board_share') or {}).items(): agg[k]+=v*S[n]['records_6m']
  t=sum(agg.values()); return {k:round(v/t,3) for k,v in agg.most_common()} if t else None
# ---------- quant ----------
Q=[("高盛世纪大道",["高盛(中国)证券有限责任公司上海浦东新区世纪大道证券营业部"],"pb_multi_strategy",["外资","高盛"]),
("瑞银花园石桥路",["瑞银证券有限责任公司上海花园石桥路证券营业部"],"pb_multi_strategy",["瑞银"]),
("摩根大通银城中路",["摩根大通证券(中国)有限公司上海银城中路证券营业部"],"pb_multi_strategy",["小摩"]),
("中金上海分公司",["中国国际金融股份有限公司上海分公司"],"pb_multi_strategy",["中金上分"]),
("中金北京建国门外大街",["中国国际金融股份有限公司北京建国门外大街证券营业部"],"pb_multi_strategy",[]),
("中金深圳分公司",["中国国际金融股份有限公司深圳分公司"],"pb_multi_strategy",[]),
("中信证券上海分公司",["中信证券股份有限公司上海分公司"],"pb_multi_strategy",["中信上分"]),
("中信深南中路中信大厦",["中信证券股份有限公司深圳深南中路中信大厦证券营业部"],"pb_multi_strategy",[]),
("中信证券总部(非营业场所)",["中信证券股份有限公司总部(非营业场所)"],"pb_multi_strategy",[]),
("华泰营业总部(非营业场所)",["华泰证券股份有限公司营业总部(非营业场所)"],"pb_multi_strategy",["华泰总部"]),
("国泰海通总部",["国泰海通证券股份有限公司"],"pb_multi_strategy",["国君总部(旧称)"]),
("国泰海通上海分公司",["国泰海通证券股份有限公司上海分公司"],"pb_multi_strategy",[]),
("华鑫上海分公司",["华鑫证券有限责任公司上海分公司"],"limit_up_sweep",["华鑫上分"]),
("华宝上海东大名路",["华宝证券股份有限公司上海东大名路证券营业部"],"limit_up_sweep",[]),
("开源西安西大街",["开源证券股份有限公司西安西大街证券营业部"],"limit_up_sweep",["开源西安"]),
("开源西安太华路",["开源证券股份有限公司西安太华路证券营业部"],"limit_up_sweep",["开源西安"]),
("国金深圳分公司",["国金证券股份有限公司深圳分公司"],"convertible_or_micro",[]),
("国信深圳互联网分公司",["国信证券股份有限公司深圳互联网分公司"],"convertible_or_micro",[]),
("国信深圳红岭中路",["国信证券股份有限公司深圳红岭中路证券营业部"],"convertible_or_micro",[]),
("中信建投北京东城分公司",["中信建投证券股份有限公司北京东城分公司"],"convertible_or_micro",[]),
("国信浙江互联网分公司",["国信证券股份有限公司浙江互联网分公司"],"intraday_t0_arb",[]),
("中信建投上海营口路",["中信建投证券股份有限公司上海营口路证券营业部"],"intraday_t0_arb",[]),
("华鑫上海瑞平路",["华鑫证券有限责任公司上海徐汇区瑞平路证券营业部"],"intraday_t0_arb",[]),
("联储证券陕西分公司",["联储证券股份有限公司陕西分公司"],"intraday_t0_arb",[]),
("中信证券浙江分公司",["中信证券股份有限公司浙江分公司"],"intraday_t0_arb",[]),
("国信深圳泰然九路",["国信证券股份有限公司深圳泰然九路证券营业部"],"intraday_t0_arb",[]),
("东莞证券四川分公司",["东莞证券股份有限公司四川分公司"],"convertible_or_micro",[])]
behav={"pb_multi_strategy":("社区经验/推测：盘中分批成交、多股同时出现，常为指数/多因子或外资通道，非单一主体","社区经验/推测：无固定兑现窗口，T+1~T+5 分批调仓"),
"limit_up_sweep":("社区经验/推测：涨停价附近大额扫单/排板，单向买入为主","社区经验/推测：次日竞价或开盘30分钟内兑现"),
"intraday_t0_arb":("社区经验/推测：买卖双向且金额接近，日内T0","社区经验/推测：当日即完成大部分对冲，次日影响小"),
"convertible_or_micro":("社区经验/推测：集中于北交所/小市值，高换手、双向","社区经验/推测：次日高开即卖"),
"fake_institution":("识别模式：机构专用席位纯买入、小市值20cm、金额集中于2000-4000万","社区经验：次日机构专用席位卖出")}
counter={"pb_multi_strategy":"不把它当方向信号，只看是否与游资合力","limit_up_sweep":"次日竞价不及预期即离场，不在高开时接力","intraday_t0_arb":"忽略其净买卖额，看剔除后的游资结构","convertible_or_micro":"北交所/小票上榜时，若该席位双向，降低信号权重","fake_institution":"首板/二板出现纯买机构专用且小市值20cm时，次日按一日游处理"}
q=[]
for i,(nm,fl,typ,sl) in enumerate(Q):
  st=S.get(fl[0],{})
  sc,m=bias(fl)
  r=st.get('two_way_min_max_ratio_p25_p50_p75')
  q.append({"seat_id":f"Q{i+1:02d}","seat_name":nm,"branch_full_names":[ev(n) for n in fl],"quant_type":typ,"quant_type_note":"按 6 个月统计特征 + 社区经验归类，属推测，不代表具体主体",
   "billboard_signature":{"two_way_trading":{"bool":bool(r and r[1] and r[1]>=0.3),"two_way_share":st.get('two_way_share'),"buy_sell_ratio_range":{"min/max_p25_p50_p75":r}},
     "sector_spread":{"days_with_ge3_stocks":st.get('days_with_ge3_stocks'),"days_with_ge3_same_board":st.get('days_with_ge3_same_board'),"note":"同板块按交易所板块(主板/创业/科创/北交)近似，未按行业"},
     "preferred_board":board_pref(fl),"median_buy_amt_wan":st.get('median_buy_amt_wan'),"source":"统计脚本 seat_stats.py，窗口 2026-04-16~2026-10-16"},
   "intraday_behavior":behav[typ][0],"next_day_exit_window":behav[typ][1],
   "next_day_premium_bias":{"score":sc,"next_day_ret_mean_pct(net_buy)":m,"score_method":"score=clip(次日均值/3,-1,1)，数据推导；counter_strategy 为主观","counter_strategy":counter[typ]},
   "community_slang":sl,"verification":"全称与上榜次数为真实请求验证；类型、行为、兑现窗口是社区经验/推测，不断言是某具体私募"})
O=json.load(open('stats_institution_6m.json'))
q.append({"seat_id":"Q99","seat_name":"机构专用(量化假机构 识别模式)","branch_full_names":[{"full_name":"机构专用","status":"东财RPT_ORGANIZATION_TRADE_DETAILS 真实请求验证；无法区分具体主体"}],"quant_type":"fake_institution",
 "billboard_signature":{"two_way_trading":{"bool":None,"buy_sell_ratio_range":"见 stats_institution_6m.json"},"sector_spread":None,"preferred_board":"创业板/科创板小市值(识别条件)","stats":O},
 "intraday_behavior":behav["fake_institution"][0],"next_day_exit_window":behav["fake_institution"][1],
 "next_day_premium_bias":{"score":round(max(-1,min(1,O['20cm_smallcap(freecap<50亿)_pure_buy_2000-4000万']['d1_mean']/3)),2),"counter_strategy":counter["fake_institution"],"note":"样本仅10条，统计意义弱"},
 "community_slang":["假机构","量化机构"],"verification":"识别模式，不对应单一主体"})
json.dump(q,open('quant_seats.json','w'),ensure_ascii=False,indent=1)
# ---------- youzi ----------
Y=[("章盟主",["章建平"],["国泰海通证券股份有限公司上海长宁区江苏路证券营业部(主)","中信证券股份有限公司杭州延安路证券营业部(协同)"],"top_youzi",["大资金","趋势加仓","容量票"]),
("炒股养家",["养家"],["华鑫证券有限责任公司上海宛平南路证券营业部(主)","华鑫证券有限责任公司上海茅台路证券营业部(协同)"],"top_youzi",["情绪周期","龙头"]),
("作手新一",["新一"],["国泰海通证券股份有限公司南京太平南路证券营业部(主)"],"top_youzi",["龙头接力"]),
("孙哥",["溧阳路"],["中信证券股份有限公司上海溧阳路证券营业部(主)","中信证券股份有限公司上海虹口区溧阳路证券营业部(协同)"],"top_youzi",["大资金","打板"]),
("赵老哥",["赵老哥"],["中国银河证券股份有限公司绍兴证券营业部(主)"],"top_youzi",["连板龙头"]),
("陈小群",["小群"],["中国银河证券股份有限公司大连黄河路证券营业部(主)"],"top_youzi",["龙头","高位接力"]),
("方新侠",["方新侠"],["中信证券股份有限公司西安朱雀大街证券营业部(主)"],"top_youzi",["趋势","大资金"]),
("上塘路",["上塘路"],["财通证券股份有限公司杭州上塘路证券营业部(主)"],"top_youzi",["打板"]),
("宁波桑田路",["桑田路"],["国盛证券股份有限公司宁波桑田路证券营业部(主)","国盛证券有限责任公司宁波桑田路证券营业部(旧名)"],"top_youzi",["打板","大资金"]),
("佛山系",["佛山"],["光大证券股份有限公司佛山绿景路证券营业部(主)"],"top_youzi",["一字板","打板"]),
("呼家楼",["呼家楼"],["中信证券股份有限公司北京呼家楼证券营业部(主)"],"top_youzi",["打板"]),
("湖里大道",["湖里大道"],["兴业证券股份有限公司厦门湖里大道证券营业部(主)"],"top_youzi",["打板"]),
("小鳄鱼",["小鳄鱼"],["南京证券股份有限公司南京大钟亭证券营业部(主)"],"top_youzi",["低位","打板"]),
("益田路荣超(代称)",[],["华泰证券股份有限公司深圳益田路荣超商务中心证券营业部"],"top_youzi",[]),
("绍兴胜利东路(代称)",[],["华鑫证券有限责任公司绍兴胜利东路证券营业部"],"top_youzi",[]),
("武汉紫阳东路(代称)",[],["国泰海通证券股份有限公司武汉紫阳东路证券营业部"],"top_youzi",[]),
("北京知春路(代称)",[],["国泰海通证券股份有限公司北京知春路证券营业部"],"top_youzi",[]),
("国新北京分公司(代称)",[],["国新证券股份有限公司北京分公司"],"top_youzi",[]),
("上海松江中山东路(代称)",[],["国泰海通证券股份有限公司上海松江区中山东路证券营业部"],"top_youzi",[]),
("湛江万豪世家(代称)",[],["国泰海通证券股份有限公司湛江万豪世家证券营业部"],"top_youzi",[]),
("东亚前海苏州(代称)",[],["东亚前海证券有限责任公司苏州分公司"],"top_youzi",[]),
("杭州曙光路(代称)",[],["平安证券股份有限公司杭州曙光路证券营业部"],"top_youzi",[]),
("招商益田路免税(代称)",[],["招商证券股份有限公司深圳益田路免税商务大厦证券营业部"],"top_youzi",[]),
("拉萨金融城南环路",["拉萨天团","东财拉萨"],["东方财富证券股份有限公司拉萨金融城南环路证券营业部"],"retail_camp",["散户集合"]),
("拉萨东环路第二",["拉萨天团"],["东方财富证券股份有限公司拉萨东环路第二证券营业部"],"retail_camp",["散户集合"]),
("拉萨团结路第一",["拉萨天团"],["东方财富证券股份有限公司拉萨团结路第一证券营业部"],"retail_camp",["散户集合"]),
("拉萨团结路第二",["拉萨天团"],["东方财富证券股份有限公司拉萨团结路第二证券营业部"],"retail_camp",["散户集合"]),
("拉萨东环路第一",["拉萨天团"],["东方财富证券股份有限公司拉萨东环路第一证券营业部"],"retail_camp",["散户集合"]),
("拉萨东城区江苏大道",["拉萨天团"],["东方财富证券股份有限公司拉萨东城区江苏大道证券营业部"],"retail_camp",["散户集合"]),
("山南香曲东路",["东财藏区"],["东方财富证券股份有限公司山南香曲东路证券营业部"],"retail_camp",["散户集合"]),
("昌都两江大道",["东财藏区"],["东方财富证券股份有限公司昌都两江大道证券营业部"],"retail_camp",["散户集合"]),
("银河北京学院南路(数据识别)",[],["中国银河证券股份有限公司北京学院南路证券营业部"],"one_day_dump",[]),
("华泰北京东三环北路(数据识别)",[],["华泰证券股份有限公司北京东三环北路证券营业部"],"one_day_dump",[]),
("华泰上海武定路(数据识别)",[],["华泰证券股份有限公司上海武定路证券营业部"],"one_day_dump",[]),
("深股通专用",["北向","外资"],["深股通专用"],"institution_alias",["北向资金"]),
("沪股通专用",["北向","外资"],["沪股通专用"],"institution_alias",["北向资金"]),
("机构专用",["机构"],["机构专用"],"institution_alias",["真机构/假机构需结合结构判断"])]
src={"top_youzi":"游资-席位对应：社区公认(淘股吧/股吧/财经自媒体长期流传)，未经官方确认；『(代称)』条目只是近6月数据高活跃席位，没有公认游资名，youzi_name 用营业部简称代替",
"retail_camp":"东财证券西藏营业部为散户集中席位，属社区共识(东方财富证券开户默认挂靠)，数据显示次日均值为负",
"one_day_dump":"纯数据识别：近6月≥100条且净买入次日均值<-1.5%，无游资名",
"institution_alias":"交易所席位类别"}
pb={"top_youzi":"主观：跟随强势合力，独食高开要谨慎","retail_camp":"主观：拉萨系净买入占比高=散户接力，次日偏弱","one_day_dump":"主观：数据显示次日偏弱，上榜买入时不追","institution_alias":"主观：北向/机构净买入需看是否双向接近(T0/调仓)"}
y=[]
for i,(nm,nk,br,cat,tags) in enumerate(Y):
  names=[b.split('(')[0] if b.endswith(')') else b for b in br]
  roles=[b[len(n):] for b,n in zip(br,names)]
  sc,m=bias(names)
  if nm=="机构专用": sc,m=round(max(-1,min(1,O['all_net_buy']['d1_mean']/3)),2),O['all_net_buy']['d1_mean']
  y.append({"seat_id":f"Y{i+1:02d}","youzi_name":nm,"nicknames":nk,"branch_names":[dict(ev(n),role=(r.strip('()') or '主/唯一'),short=nm) for n,r in zip(names,roles)],"category":cat,"style_tags":tags,"style_tags_status":"社区经验" if tags else "无",
   "next_day_premium_bias":{"score":sc,"next_day_ret_mean_pct(net_buy,6m)":m,"score_method":"clip(均值/3,-1,1) 数据推导；样本<30时可靠性低","playbook":pb[cat]},
   "verification":src[cat]})
json.dump(y,open('youzi_seats.json','w'),ensure_ascii=False,indent=1)
print(len(q),len(y))
for x in y: print(x['youzi_name'],[ (b['lhb_records_1y'],b['status'][:4]) for b in x['branch_names']],x['next_day_premium_bias']['score'])
