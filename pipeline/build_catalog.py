"""카탈로그 생성: 전체 작품 목록 + 3개 국어 제목 + ID 매핑 → sources/catalog_full.json"""
import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),"sources"))
import json,re,collections,sys
sys.path.insert(0,'..')
from names_ko import TAG_KO, add_season
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
    PH=re.compile(r'[\(（]\s*(続編|新作|新シリーズ|仮|仮題|仮称|タイトル未定|新アニメ化プロジェクト|新アニメ|新作アニメ|アニメ化決定|アニメ化プロジェクト)\s*[\)）]|\(仮\)')     # 발표 전 자리표시 제목
    ja=pick(t,'ja')
    if ja and PH.search(ja): ja=next((y for y in x['synonyms'] if kana.search(y) and not PH.search(y) and y.replace(' ','').startswith(PH.sub('',ja).replace(' ','').strip())),None) or ja
    ja=ja or next((y for y in x['synonyms'] if kana.search(y)),None) or next((y for y in x['synonyms'] if cjk.search(y) and not hangul.search(y)),None)
    if ja and re.fullmatch(r'[ぁ-ん]{2,6}', ja):          # 「るるりり」 같은 히라가나 줄임말이 뽑히면 정식 제목으로
        ja=next((y for y in x['synonyms'] if re.search(r'[\u30a0-\u30ff\u4e00-\u9fff]', y) and len(y) >= 6 and not hangul.search(y)), None) or ja
    ko=pick(t,'ko') or next((y for y in x['synonyms'] if hangul.search(y)),None)
    ko=add_season(ko, pick(t,'ja') or next((y for y in x['synonyms'] if kana.search(y)),None), x['title'])
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
    rec=dict(k=k,_syn=[y for y in x['synonyms'] if not hangul.search(y)][:40],r=ro,ja=ja,ko=ko,en=en,ty=x['type'][0] if x['type']!='UNKNOWN' else 'X',
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
    t = re.sub(r'(?:part|cour|cor)(\d)', r'pt\1', t)                         # 「Part 2」와 「Cour 2」는 같은 2쿨 (앞에서 ou→o로 바뀌어 cour는 cor가 됨)
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
CJK = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
def keys(r):
    """비교 키: (종류, 정규화한 제목, 대표 제목인지). 다른 이름(synonyms)끼리만 같은 경우는 합치지 않으려고 대표 여부를 붙임
    (예: 「Hungry Days」라는 다른 이름을 함께 가진 서로 다른 광고 영상)."""
    ks = {}
    def add(k, prim): ks[k] = ks.get(k, False) or prim
    # 부제 앞부분(「世界最強の後衛 ~迷宮国の新人探索者~」의 「世界最強の後衛」)도 다른 이름처럼 비교 (부제를 뺀 이름만 적은 보조 출처 항목과 맞추려고)
    def mains(x):
        m = re.split(r'\s*[~～〜:：]\s*', x or '', maxsplit=1)[0].strip()
        return [m] if m and m != (x or '').strip() else []
    for jt, prim in [(r['ja'], True)] + [(y, False) for y in r.get('_syn', []) if CJK.search(y)] + [(y, False) for y in mains(r['ja'])]:
        j = nja(jt)
        if (CJK.search(j) and len(j) >= 2) or len(j) >= 4: add(('ja', j), prim)       # 일본어는 「猫と竜」처럼 짧은 제목도 구분력이 큼
    for t, prim in [(r['r'], True), (r.get('en'), True)] + [(y, False) for y in r.get('_syn', []) if not CJK.search(y)] + [(y, False) for y in mains(r['r'])]:
        n = nro(t)
        if len(n) >= 6: add(('ro', n), prim)
    return ks
for i, r in enumerate(out):
    if r['adb']: buckets[('adb', r['adb'])].append((i, True))
    for key, prim in keys(r).items(): buckets[('t',) + key].append((i, prim))
    kb = nbare(r['ja'])
    if len(kb) >= 4 and (kb != nja(r['ja']) or not (r['al'] or r['mal'])): buckets[('tb', kb, r['y'])].append((i, True))
def digits(r): return set(re.findall(r'\d+', unicodedata.normalize('NFKC', (r['ja'] or '') + ' ' + (r['r'] or ''))))
def prefix_ok(x, y, n=4):
    return any(len(p) >= n and len(q) >= n and p[:n] == q[:n] for p, q in ((nja(x['ja']), nja(y['ja'])), (nro(x['r']), nro(y['r']))))
def syn_ok(a, b):
    """한쪽의 「다른 이름」과만 같을 때는 더 엄격하게: 같은 해, 제목 속 숫자(시즌·편 번호)가 서로 맞고, 대표 제목 앞부분이 같을 것
    (「오시리 탐정 9기 2쿨」과 「10기」, 「사이보그 009 콜 오브 저스티스」 1·2편, 「원피스」·「드래곤볼」 같은 방송 특집이 섞이지 않게)"""
    if not (a['y'] and b['y']) or a['y'] != b['y']: return False          # 연도를 모르면 합치지 않음 (예: 「Blue Lock: Neo Egoist League」 연도 없음 → 1기와 섞임)
    if digits(a) != digits(b): return False                             # 한쪽에만 번호가 있어도 다른 편 (예: 「Baki-dou: Dai 2 Cour」와 「Baki-dou」)
    return prefix_ok(a, b)
def compatible(a, b):
    """같은 제목일 때 같은 작품으로 볼지: 형식이 같고(미분류는 예외), 연도 차이 1년 이내(한쪽이 미상이면 허용).
    출처마다 방영 시기를 다르게 적는 경우(예: 한 곳은 봄, 한 곳은 여름)가 있어 분기는 보지 않음."""
    if a['y'] and b['y'] and abs(a['y'] - b['y']) > 1: return False
    if a['ty'] != b['ty'] and 'X' not in (a['ty'], b['ty']):
        # 형식이 달라도, 한쪽이 ID 없는 약한 출처(ANN 등)뿐이고 연도가 둘 다 있으면 같은 작품으로 봄 (약한 출처는 형식을 자주 다르게 적음)
        # 단, TV·웹끼리 또는 OVA·스페셜·웹끼리만 (극장판은 다른 형식과 섞지 않음: 「비밀의 아코짱」 TV와 극장판 같은 경우)
        weak = lambda r: not (r['al'] or r['mal'] or r['adb'])
        near = {a['ty'], b['ty']} <= {'T', 'O'} or {a['ty'], b['ty']} <= {'V', 'S', 'O'}
        return (weak(a) or weak(b)) and bool(a['y'] and b['y']) and near
    return True
for (kind, *rest), idx in buckets.items():
    for x in range(len(idx)):
        for y_ in range(x + 1, len(idx)):
            (ia, pa), (ib, pb) = idx[x], idx[y_]
            if not (pa or pb): continue                      # 둘 다 「다른 이름」으로만 같으면 합치지 않음
            a, b = out[ia], out[ib]
            if kind == 't' and not (pa and pb) and not syn_ok(a, b): continue
            if kind == 't' and not compatible(a, b): continue
            if kind == 'tb':
                # 괄호를 뺀 제목으로만 같은 경우: 형식이 같고, 한쪽이 AniList·MAL ID가 없는 보조 출처 항목이고,
                # 연도를 알고, 둘 중 하나는 괄호 덧붙임이 없을 때만 합침 (둘 다 괄호가 있으면 다른 판일 수 있음)
                if a['ty'] != b['ty'] and 'X' not in (a['ty'], b['ty']): continue
                if (a['al'] or a['mal']) and (b['al'] or b['mal']): continue
                if not a['y'] or not (nja(a['ja']) == rest[0] or nja(b['ja']) == rest[0]): continue
            union(ia, ib)
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
        m.setdefault('_alias', []).append(o['k']); m['_syn'] = m.get('_syn', []) + o.get('_syn', [])
    merged.append(m)
print('중복 합치기:', len(out), '→', len(merged))
out = merged
key2i = {r['k']: i for i, r in enumerate(out)}
alias = {a: r['k'] for r in out for a in r.get('_alias', [])}
for r in out: r.pop('_alias', None); r.pop('_syn', None)

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
json.dump(alias,open('catalog_aliases.json','w'))   # 합쳐져 사라진 작품 번호 → 남은 작품 번호 (사이트가 예전 체크 기록을 옮길 때 씀)
