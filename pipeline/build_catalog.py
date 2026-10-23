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
# ── 중복 합치기 ─────────────────────────────────────────────
# 원천 목록(manami)은 출처끼리 정보가 다르면 같은 작품을 따로 둡니다(예: AniDB만, anisearch만 있는 항목).
# 같은 AniDB ID이거나, 형식·연도가 같고 일본어 제목 또는 로마자 제목이 같으면 한 작품으로 합칩니다.
import unicodedata
def nja(t):
    t = unicodedata.normalize('NFKC', t or '')
    t = re.sub(r'[第割]\s*(\d+)\s*クール', r'\1cour', t)          # 「第2クール」 (원천의 오타 「割2クール」 포함)
    return re.sub(r'[\s「」『』""“”‘’\'"!?！？・･、。,.:：;；~〜\-－―ー()（）\[\]【】]', '', t)
def nro(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'[^a-z0-9]', '', t)
    t = t.replace('wo', 'o').replace('ou', 'o').replace('uu', 'u').replace('oo', 'o')
    t = re.sub(r'(.)\1+', r'\1', t)                                   # Lilly / Lily 같은 겹글자 차이
    return t
def nbare(t):
    # 괄호 속 덧붙임(「(新アニメ化プロジェクト)」·「[マジックナイト]」 등)을 뺀 제목
    return nja(re.sub(r'[\(（\[【][^\)）\]】]*[\)）\]】]', '', unicodedata.normalize('NFKC', t or '')))
par = list(range(len(out)))
def find(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
ids = [{('al', r['al'])} if r['al'] else set() for r in out]
for i, r in enumerate(out):
    if r['mal']: ids[i].add(('mal', r['mal']))
def union(a, b):
    a, b = find(a), find(b)
    if a == b: return
    # 원천 목록이 서로 다른 AniList·MAL ID로 따로 둔 작품끼리는 합치지 않음 (분할 2쿨 등 제목이 같은 다른 작품 보호)
    ka = {k for k, _ in ids[a]}; kb = {k for k, _ in ids[b]}
    if any(x in ka and x in kb and {v for k, v in ids[a] if k == x} != {v for k, v in ids[b] if k == x} for x in ('al', 'mal')): return
    lo, hi = min(a, b), max(a, b); par[hi] = lo; ids[lo] |= ids[hi]
buckets = collections.defaultdict(list)
for i, r in enumerate(out):
    if r['adb']: buckets[('adb', r['adb'])].append(i)
    ty = r['ty'] if r['ty'] != 'X' else None
    for key in {nja(r['ja']), nro(r['r'])}:
        if len(key) >= 4: buckets[('t', key, r['y'])].append(i)
    kb = nbare(r['ja'])
    if len(kb) >= 4 and kb != nja(r['ja']) or (len(kb) >= 4 and not (r['al'] or r['mal'])): buckets[('tb', kb, r['y'])].append(i)
for (kind, *rest), idx in buckets.items():
    for j in idx[1:]:
        a, b = out[idx[0]], out[j]
        if kind in ('t', 'tb') and a['ty'] != b['ty'] and 'X' not in (a['ty'], b['ty']): continue
        # 괄호를 뺀 제목으로만 같은 경우는, 한쪽이 AniList·MAL ID가 없는 보조 출처 항목일 때만 합침
        if kind == 'tb' and (a['al'] or a['mal']) and (b['al'] or b['mal']): continue
        # 연도를 모르거나, 둘 다 괄호 덧붙임이 있으면(서로 다른 판일 수 있음) 합치지 않음
        if kind == 'tb' and (not a['y'] or not (nja(a['ja']) == rest[0] or nja(b['ja']) == rest[0])): continue
        union(idx[0], j)
groups = collections.defaultdict(list)
for i in range(len(out)): groups[find(i)].append(i)
def rank(r): return (bool(r['al']), bool(r['mal']), bool(r['adb']), r['p'][:1] in ('M', 'A'))
merged = []
for g in groups.values():
    rs = sorted((out[i] for i in g), key=rank, reverse=True)
    m = dict(rs[0])
    for o in rs[1:]:
        for f in ('ja', 'ko', 'en', 'y', 'q', 'd', 'tmdb', 'tms', 'sy', 'an', 'bgm', 'site', 'vod'):
            if not m.get(f) and o.get(f): m[f] = o[f]
        if not m['p'] and o['p']: m['p'] = o['p']
        if (o.get('e') or 0) > (m.get('e') or 0): m['e'] = o['e']      # 방영 전 자리표시(1화)보다 큰 값이 실제에 가까움
        m['rel'] = m['rel'] + [x for x in o['rel'] if x not in m['rel']]
        m['tags'] = m['tags'] + [t for t in o['tags'] if t not in m['tags']]
        m.setdefault('_alias', []).append(o['k'])
    merged.append(m)
print('중복 합치기:', len(out), '→', len(merged))
out = merged
key2i = {r['k']: i for i, r in enumerate(out)}
alias = {a: r['k'] for r in out for a in r.get('_alias', [])}
for r in out: r.pop('_alias', None)

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
    r['rel']=sorted(alias.get(x, x) for x in rel if alias.get(x, x) != r['k'])
print(len(out),dropped)
print(collections.Counter(bool(r['ko']) for r in out),collections.Counter(bool(r['ja']) for r in out))
print(collections.Counter((r['y']//10*10 if r['y'] else None) for r in out))
json.dump(out,open('catalog_full.json','w'),ensure_ascii=False)
