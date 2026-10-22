"""카탈로그 생성: 전체 작품 목록 + 3개 국어 제목 + ID 매핑 → sources/catalog_full.json"""
import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),"sources"))
import json,re,collections,sys
sys.path.insert(0,'..')
from names_ko import TAG_KO
a=json.load(open('aod.json'))['data']
NONJP={'chinese animation','chinese production','korean animation','south korean production','north korean production','original in english'}
CO=re.compile(r'japanese co-production|japanese production|sino-japanese|korean-japanese')
def idof(srcs,site):
    for s in srcs:
        if site in s: return s.rstrip('/').split('/')[-1]
    return None
# AniDB titles
titles={}
for line in open('at.json'):
    d=json.loads(line); t=collections.defaultdict(list)
    for x in d['titles']: t[(x['language'],x['type'])].append(x['title'])
    titles[d['id']]=t
arm={}
for x in json.load(open('arm.json')):
    for kk,src in (('al','anilist_id'),('mal','mal_id')):
        if x.get(src): arm.setdefault((kk,str(x[src])),x)
bgm={}
for it in json.load(open('bangumi-data.json'))['items']:
    st={x['site']:x for x in it['sites']}
    rec={'bgm':(st.get('bangumi') or {}).get('id'),'site':it.get('officialSite') or None,
         'jp':[n for n in ('danime','unext','abema','netflix','prime','nicovideo','disneyplus','youtube') if n in st],
         'us':[n for n in ('crunchyroll','netflix','prime','disneyplus') if n in st]}
    if 'mal' in st: bgm.setdefault(('mal',str(st['mal']['id'])),rec)
    if 'aniList' in st: bgm.setdefault(('al',str(st['aniList']['id'])),rec)
fr={}
for f in json.load(open('fribb.json')):
    if f.get('mal_id'): fr.setdefault(('mal',f['mal_id']),f)
    if f.get('anilist_id'): fr.setdefault(('al',f['anilist_id']),f)
kana=re.compile('[\u3040-\u30ff]'); hangul=re.compile('[\uac00-\ud7a3]'); cjk=re.compile('[\u4e00-\u9fff]')
def pick(t,lang,types=('official','main','syn')):
    for ty in types:
        if t.get((lang,ty)): return t[(lang,ty)][0]
SEAS={'WINTER':1,'SPRING':2,'SUMMER':3,'FALL':4}
out=[];key2i={};dropped=collections.Counter()
for x in a:
    tags=set(x['tags'])
    if tags&NONJP and not any(CO.search(t) for t in tags): dropped['nonjp']+=1; continue
    s=x['sources']; al=idof(s,'anilist.co'); mal=idof(s,'myanimelist.net'); adb=idof(s,'anidb.net')
    f=fr.get(('al',int(al))) if al else None
    if not f and mal: f=fr.get(('mal',int(mal)))
    if f and not adb and f.get('anidb_id'): adb=str(f['anidb_id'])
    t=titles.get(int(adb),{}) if adb else {}
    ja=pick(t,'ja') or next((y for y in x['synonyms'] if kana.search(y)),None) or next((y for y in x['synonyms'] if cjk.search(y) and not hangul.search(y)),None)
    ko=pick(t,'ko') or next((y for y in x['synonyms'] if hangul.search(y)),None)
    en=pick(t,'en') ; ro=pick(t,'x-jat',('main','official','syn')) or x['title']
    k=('a'+al) if al else ('m'+mal) if mal else ('d'+adb) if adb else None
    if not k:
        u=s[0].rstrip('/'); site=re.sub(r'^https?://','',u).split('/')[0].split('.')[0][:2]
        k=site+'_'+u.split('/')[-1]
    dur=x.get('duration',{}).get('value')
    pic=x.get('picture','')
    if 'myanimelist' in pic: pic='M'+pic.split('/images/anime/')[1]
    elif 'anilist' in pic: pic='A'+pic
    elif 'nopicture' in pic or 'no_pic' in pic: pic=''
    tm=(f or {}).get('themoviedb_id') or {}
    rec=dict(k=k,r=ro,ja=ja,ko=ko,en=en,ty=x['type'][0] if x['type']!='UNKNOWN' else 'X',
        y=x['animeSeason'].get('year'),q=SEAS.get(x['animeSeason'].get('season')),
        e=x['episodes'],d=dur,st=x['status'][0],p=pic,stu=x['studios'][:3],
        al=al,mal=mal,adb=adb,tmdb=tm.get('tv') if isinstance(tm,dict) else None,tms=((f or {}).get('season') or {}).get('tmdb'),
        rel=[r for r in x['relatedAnime']],
        net=1 if 'netflix original' in tags or 'netflix' in tags else 0)
    m=arm.get(('al',al)) or arm.get(('mal',mal)) or {}
    rec['sy']=m.get('syobocal_tid'); rec['an']=m.get('annict_id')
    b=bgm.get(('al',al)) or bgm.get(('mal',mal)) or {}
    rec['bgm']=b.get('bgm'); rec['site']=b.get('site'); rec['vod']={'JP':b['jp'],'US':b['us']} if b else None
    rec['tags']=[t for t in x['tags'] if t in TAG_KO]
    key2i[k]=len(out); out.append(rec)
# resolve relations to keys
url2k={}
for r in out:
    if r['al']: url2k['anilist.co/anime/'+r['al']]=r['k']
    if r['mal']: url2k['myanimelist.net/anime/'+r['mal']]=r['k']
for r in out:
    rel=set()
    for u in r['rel']:
        m=re.search(r'(anilist\.co/anime/\d+|myanimelist\.net/anime/\d+)',u)
        if m and m.group(1) in url2k and url2k[m.group(1)]!=r['k']: rel.add(url2k[m.group(1)])
    r['rel']=sorted(rel)
print(len(out),dropped)
print(collections.Counter(bool(r['ko']) for r in out),collections.Counter(bool(r['ja']) for r in out))
print(collections.Counter((r['y']//10*10 if r['y'] else None) for r in out))
json.dump(out,open('catalog_full.json','w'),ensure_ascii=False)
