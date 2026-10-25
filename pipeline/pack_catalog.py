"""카탈로그를 사이트용 압축 형식으로 저장 → ../site/data/catalog.json"""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import json,gzip
from names_ko import studio_ko, studio_sid, TAG_KO
c=json.load(open('sources/catalog_full.json'))
stu={};tags={};F=['k','r','ja','ko','en','ty','y','q','e','d','st','p','stu','al','mal','adb','tmdb','rel','net','sy','an','tms','bgm','site','vod','tags']
rows=[]
for r in c:
    r['stu']=[stu.setdefault(s,len(stu)) for s in r['stu']]
    r['tags']=sorted({tags.setdefault(TAG_KO[t],len(tags)) for t in r['tags']})
    rows.append([r[f] for f in F])
al=json.load(open('sources/catalog_aliases.json')) if os.path.exists('sources/catalog_aliases.json') else {}
d={'v':2,'aliases':al,'fields':F,'studios':[[s,*studio_ko(s),studio_sid(s)] for s in stu],'tags':list(tags),'rows':rows,'sources':'manami-project/anime-offline-database (ODbL), AniDB titles (CC BY-NC-SA), Fribb/anime-lists'}
if len(rows) < 30000:
    raise SystemExit(f'작품 수가 {len(rows)}편뿐이라 원천 데이터 형식이 바뀐 것으로 보고 기존 목록을 유지합니다.')
s=json.dumps(d,ensure_ascii=False,separators=(',',':'))
open('../site/data/catalog.json','w',encoding='utf-8').write(s)
print(len(s)/1e6,'MB raw',len(gzip.compress(s.encode()))/1e6,'MB gz')
