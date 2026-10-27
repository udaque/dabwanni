"""카탈로그 생성: 전체 작품 목록 + 3개 국어 제목 + ID 매핑 → sources/catalog_full.json"""
import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),"sources"))
import json, glob, os,re,collections,sys
sys.path.insert(0,'..')
from names_ko import TAG_KO, add_season
a=json.load(open('aod.json'))['data']
NONJP={'chinese animation','chinese production','original in english'}      # 한국 제작 작품은 넣음 (일본·한국 작품을 다룸)
KOREAN={'korean animation','south korean production','korean production'}
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
_kk=[None]
def ja_like(y, title):
    """일본어 이름 y를 읽은 로마자가 제목과 얼마나 닮았는지 (0~1). 중국어 간체·번체로 보이는 이름은 깎음."""
    import difflib
    if _kk[0] is None:
        try: import pykakasi; _kk[0]=pykakasi.kakasi()
        except Exception: _kk[0]=False
    rd=''.join(p['hepburn'] for p in _kk[0].convert(y)) if _kk[0] else y
    a=re.sub(r'[^a-z0-9]','',rd.lower()); b=re.sub(r'[^a-z0-9]','',(title or '').lower())
    sc=difflib.SequenceMatcher(None,a,b).ratio()
    if not re.search(r'[\u3040-\u30ff]', y): sc-=0.3        # 가나가 없으면(중국어 제목일 가능성) 덜 믿음
    return sc

def pick(t,lang,types=('official','main','syn')):
    for ty in types:
        if t.get((lang,ty)): return t[(lang,ty)][0]
SEAS={'WINTER':1,'SPRING':2,'SUMMER':3,'FALL':4}
# ── AniList 분기 목록으로 보충 (manami 원천이 7월 판에서 멈춘 동안 새로 발표된 작품과 바뀐 시기·상태·화수) ──
FMT={'TV':'TV','TV_SHORT':'TV','ONA':'ONA','OVA':'OVA','SPECIAL':'SPECIAL','MOVIE':'MOVIE','MUSIC':'MUSIC'}
STAT={'FINISHED':'FINISHED','RELEASING':'ONGOING','NOT_YET_RELEASED':'UPCOMING','HIATUS':'ONGOING','CANCELLED':'FINISHED'}
SEAS_OF={1:'WINTER',2:'SPRING',3:'SUMMER',4:'FALL'}
TYCODE={'TV':'T','ONA':'O','OVA':'V','SPECIAL':'S','MOVIE':'M','MUSIC':'S','UNKNOWN':'X'}
def is_music_video(x):
    """노래 한 곡짜리 뮤직비디오(보컬로이드 곡 영상 등): 스페셜·웹·미분류이면서 1~2화, 10분 이하이고 「music」·「vocaloid」 표시가 있는 것.
    화수를 아직 모르는 신작(0화)은 보컬로이드 표시가 있을 때만."""
    t=set(x.get('tags') or []); d=(x.get('duration') or {}).get('value') or 0; e=x.get('episodes') or 0
    if x.get('type')=='MUSIC': return True
    if x.get('type') not in ('SPECIAL','ONA','UNKNOWN') or e>2 or (d and d>600): return False
    if e==0: return 'vocaloid' in t
    return 'vocaloid' in t or 'music' in t
def from_anilist(m):
    sd=m.get('startDate') or {}
    yr=sd.get('year') or m.get('seasonYear'); sea=SEAS_OF[(sd['month']-1)//3+1] if sd.get('month') else (m.get('season') or 'UNDEFINED')
    t=m.get('title') or {}
    syn=[x for x in [t.get('native'), t.get('english')] + (m.get('synonyms') or []) if x]
    return {'title': t.get('romaji') or t.get('english') or t.get('native') or '', 'type': FMT.get(m.get('format'),'UNKNOWN'),
            'episodes': m.get('episodes') or 0, 'status': STAT.get(m.get('status'),'UNKNOWN'),
            'animeSeason': {'season': sea, 'year': yr}, 'picture': (m.get('coverImage') or {}).get('large') or '',
            'synonyms': syn, 'sources': [f"https://anilist.co/anime/{m['id']}"] + ([f"https://myanimelist.net/anime/{m['idMal']}"] if m.get('idMal') else []),
            'relatedAnime': [f"https://anilist.co/anime/{e['node']['id']}" for e in ((m.get('relations') or {}).get('edges') or []) if (e.get('node') or {}).get('type')=='ANIME'],
            'tags': [g.lower() for g in m.get('genres') or []] + ({None: [], 'JP': [], 'KR': ['korean animation'], 'CN': ['chinese animation'], 'TW': ['chinese animation']}.get(m.get('countryOfOrigin'), ['original in english'])),
            'studios': [n['name'] for n in ((m.get('studios') or {}).get('nodes') or [])], 'duration': {'value': (m.get('duration') or 0)*60, 'unit': 'SECONDS'} if m.get('duration') else {}}
ALS={}
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),'raw','anilist_season','*.json'))):
    try:
        for m in json.load(open(f,encoding='utf-8')).get('media') or []: ALS[str(m['id'])]=m
    except Exception as ex: print('AniList 분기 목록 읽기 실패', f, ex)
if ALS:
    seen=set(); upd=0
    for x in a:
        al_=idof(x['sources'],'anilist.co')
        if al_ and al_ in ALS:
            seen.add(al_); n=from_anilist(ALS[al_])
            # 이미 있는 작품: 방영 시기·상태는 AniList 값으로, 화수는 더 큰 쪽(방영 전 자리표시 1화 대비)
            if n['animeSeason']['year']: x['animeSeason']=n['animeSeason']
            if n['status']!='UNKNOWN': x['status']=n['status']
            if n['episodes'] and (n['status']=='FINISHED' or n['episodes']>(x.get('episodes') or 0)): x['episodes']=n['episodes']
            if not x.get('picture') or 'nopicture' in x['picture']: x['picture']=n['picture']
            upd+=1
    new=[from_anilist(m) for k_,m in ALS.items() if k_ not in seen]
    a=a+new
    print(f'AniList 분기 목록: 기존 {upd}편 시기·상태 갱신, 새 작품 {len(new)}편 추가')

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
    if not ja:
        # AniDB에 일본어 제목이 아직 없는 새 작품: 다른 이름 중 첫 번째가 아니라, 읽었을 때 대표 로마자 제목과 가장 닮은 일본어 이름을 고름
        # (「Fujimoto Tatsuki 17-26」에 회차 제목 「シカク」, 「Golden Kamuy: Inazuma Goutou…」에 「…シマエナガ」가 뽑히던 문제)
        cands=[y for y in x['synonyms'] if not hangul.search(y) and (kana.search(y) or cjk.search(y))]
        ja=max(cands, key=lambda y: ja_like(y, x['title']), default=None) if cands else None
    if ja and len(ja) <= 4:                               # 「幼ラブ」처럼 짧은 줄임말이 뽑혔으면, 같은 글자로 시작하는 긴 정식 제목으로
        ja=next((y for y in x['synonyms'] if y[:1]==ja[:1] and len(y) >= len(ja)+4 and kana.search(y) and not hangul.search(y)), None) or ja
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
    rec=dict(k=k,_syn=[y for y in x['synonyms'] if not hangul.search(y)][:40],r=ro,ja=ja,ko=ko,en=en,ty=TYCODE.get(x['type'],'X'),
        y=x['animeSeason'].get('year'),q=SEAS.get(x['animeSeason'].get('season')),
        e=x['episodes'],d=dur,st=x['status'][0],p=pic,stu=x['studios'][:3],
        al=al,mal=mal,adb=adb,tmdb=tm.get('tv') if isinstance(tm,dict) else None,tms=((f or {}).get('season') or {}).get('tmdb'),
        rel=[r for r in x['relatedAnime']],
        net=1 if 'netflix original' in tags or 'netflix' in tags else 0)
    rec['_mv']=is_music_video(x)                         # 뮤직비디오 표시 (합친 뒤에 형식을 P로 바꿈: 합치기 규칙은 원래 형식으로)
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
    t = unicodedata.normalize('NFKC', t or '').lower()                  # 대소문자 무시 (「Cyber Land」·「ROAD TO THE TOP」)
    t = re.sub(r'[\(（]\s*(19|20)\d\d\s*[\)）]', '', t)          # 「タヌキとキツネ (2026)」의 연도 꼬리는 비교에서 뺌
    t = re.sub(r'[第割]\s*(\d+)\s*クール', r'\1cour', t)          # 「第2クール」 (원천의 오타 「割2クール」 포함)
    t = re.sub(r'^\s*(OVA|OAD|ONA|劇場版OVA)\s+', '', t)               # 「OVA ケガレボシ」 = 「ケガレボシ」
    return re.sub(r'[\s「」『』""“”‘’\'"!?！？・･、。,.:：;；~〜\-－―ー()（）\[\]【】/／]', '', t)
def nro(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'\(\s*(19|20)\d\d\s*\)', '', t)                 # 「Shibuya Hachi (2025) TV」의 연도 꼬리
    t = re.sub(r'^\s*(ova|oad|ona)\s+', '', t)
    t = re.sub(r'\b(part|cour|season)\s*(iv|iii|ii)\b', lambda m: m.group(1) + {'ii': '2', 'iii': '3', 'iv': '4'}[m.group(2)], t)   # 「Part II」 = 「Part 2」 (겹글자 줄이기 전에)
    t = re.sub(r'[^a-z0-9]', '', t)
    t = t.replace('wo', 'o').replace('ou', 'o').replace('uu', 'u').replace('oo', 'o')
    t = re.sub(r'(.)\1+', r'\1', t)                                   # Lilly / Lily 같은 겹글자 차이
    t = re.sub(r'(?:part|cour|cor)(\d)', r'pt\1', t)                         # 「Part 2」와 「Cour 2」는 같은 2쿨 (앞에서 ou→o로 바뀌어 cour는 cor가 됨)
    return t
KANJI_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
SEASON_MARK = re.compile(r'\s*(第\s*[0-9一二三四五六七八九十]+\s*(期|シーズン|クール|部)|[0-9]+\s*期|[0-9]+(st|nd|rd|th)\s*season|season\s*[0-9]+|part\s*([0-9]+|ii|iii|iv)|cour\s*[0-9]+|(?<=\s)[2-9]|(?<=\s)(II|III|IV|V|VI)|(?<=[^\sA-Za-z])(II|III|IV|Ⅱ|Ⅲ|Ⅳ))\s*$', re.I)
# 끝의 맨 번호(「転生したら剣でした 2」)와 로마 숫자도 시즌 표시로 봄 (2~9만: 「86」 같은 제목 숫자와 구분)
def season_base(t):
    """제목 끝의 시즌 표시를 뺀 이름 (「地獄楽 第二期」→「地獄楽」, 「Jigokuraku 2nd Season」→「Jigokuraku」). 표시가 없으면 None."""
    t0 = unicodedata.normalize('NFKC', t or '').strip(); b = SEASON_MARK.sub('', t0).strip()
    return b if b and b != t0 else None

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
        out = []
        # 부제 앞부분, 두 편을 「/」로 묶은 제목의 첫 편 (「…お銀/シマエナガ」). 「Ranma 1/2」 같은 숫자 사이 「/」와 「Fate/Zero」처럼 짧은 뒷부분은 나누지 않음
        for sep in (r'\s*[~～〜:：]\s*', r'(?<=[^\d\s])\s*/\s*(?=[^\d\s/]{6})'):
            m = re.split(sep, x or '', maxsplit=1)[0].strip()
            if m and m != (x or '').strip(): out.append(m)
        return out
    for jt, prim in [(r['ja'], True)] + [(y, False) for y in r.get('_syn', []) if CJK.search(y)] + [(y, False) for y in mains(r['ja'])]:
        j = nja(jt)
        if (CJK.search(j) and len(j) >= 2) or len(j) >= 4: add(('ja', j), prim)       # 일본어는 「猫と竜」처럼 짧은 제목도 구분력이 큼
    # 앞뒤가 바뀐 제목(「戦車椅子-TANK CHAIR-」와 「TANK CHAIR-戦車椅子-」): 구분 기호로 나눈 조각을 정렬해 비교
    for t, prim in ((r['ja'], True), (r['r'], True)):
        parts = [nja(p) for p in re.split(r'[-‐―－~〜～:：]', unicodedata.normalize('NFKC', t or '')) if nja(p)]
        if len(parts) >= 2: add(('ja', '|'.join(sorted(parts))), prim)
    for t, prim in [(r['r'], True), (r.get('en'), True)] + [(y, False) for y in r.get('_syn', []) if not CJK.search(y)] + [(y, False) for y in mains(r['r'])]:
        n = nro(t)
        if len(n) >= 6 or (prim and len(n) >= 4): add(('ro', n), prim)      # 대표 제목끼리는 「SANDA」처럼 짧아도 비교
    return ks
for i, r in enumerate(out):
    if r['adb']: buckets[('adb', r['adb'])].append((i, True))
    for key, prim in keys(r).items(): buckets[('t',) + key].append((i, prim))
    # 시즌 표시를 뺀 이름: 시즌 작품(번호 있음)은 'season', 번호 없는 보조 출처 항목은 'plain'으로 같은 해 같은 이름끼리 묶음
    # (ANN이 2기를 그냥 「地獄楽」로 적은 항목을 「地獄楽 第二期」에 합치려고)
    for t, nf in ((r['ja'], nja), (r['r'], nro)):
        sb = season_base(t)
        if sb and len(nf(sb)) >= 2: buckets[('tbase', nf(sb), r['y'])].append((i, 'season'))
        elif not (r['al'] or r['mal']) and t and len(nf(t)) >= 2: buckets[('tbase', nf(t), r['y'])].append((i, 'plain'))
    kb = nbare(r['ja'])
    if len(kb) >= 4 and (kb != nja(r['ja']) or not (r['al'] or r['mal'])): buckets[('tb', kb, r['y'])].append((i, True))
def digits(r):
    t = unicodedata.normalize('NFKC', (r['ja'] or '') + ' ' + (r['r'] or ''))
    t = re.sub(r'[\(（]\s*(19|20)\d\d\s*[\)）]', '', t)          # 「かくりよの宿飯 (2025)」의 연도 꼬리는 번호로 안 봄
    return set(re.findall(r'\d+', t))
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
# 같은 해 시즌 짝(tbase)을 먼저 합쳐, 연도 1년 차이 규칙보다 앞서게 함 (예: ANN의 2025년 「Grand Blue Dreaming」은 2기에, 3기가 아니라)
for (kind, *rest), idx in sorted(buckets.items(), key=lambda kv: kv[0][0] != 'tbase'):
    for x in range(len(idx)):
        for y_ in range(x + 1, len(idx)):
            (ia, pa), (ib, pb) = idx[x], idx[y_]
            if not (pa or pb): continue                      # 둘 다 「다른 이름」으로만 같으면 합치지 않음
            a, b = out[ia], out[ib]
            if kind == 'tbase':
                # 번호 있는 시즌 작품 하나와 번호 없는 보조 출처 항목 하나일 때만, 같은 해·비슷한 형식이면 합침
                if {pa, pb} != {'season', 'plain'} or not a['y']: continue
                if not ({a['ty'], b['ty']} <= {'T', 'O', 'X'} or a['ty'] == b['ty']): continue
                union(ia, ib); continue
            if kind == 't' and not (pa and pb) and not syn_ok(a, b): continue
            if kind == 't' and not compatible(a, b): continue
            if kind == 'tb':
                # 괄호를 뺀 제목으로만 같은 경우: 형식이 같고, 한쪽이 AniList·MAL ID가 없는 보조 출처 항목이고,
                # 연도를 알고, 둘 중 하나는 괄호 덧붙임이 없을 때만 합침 (둘 다 괄호가 있으면 다른 판일 수 있음)
                if a['ty'] != b['ty'] and 'X' not in (a['ty'], b['ty']): continue
                if (a['al'] or a['mal']) and (b['al'] or b['mal']): continue
                if not a['y'] or not (nja(a['ja']) == rest[0] or nja(b['ja']) == rest[0]): continue
            union(ia, ib)
# ── 전수 점검으로 찾은 남은 중복: 한쪽이 보조 출처 항목이고 제목이 거의 같은 것 ──
# 같은 해, 제목 유사도 0.92 이상, 번호 같음, 「前編·総集編·OP·CM」 같은 편 표시가 같음, TV와 극장판처럼 성격이 다르지 않을 것
import difflib
PART_MARK = re.compile(r'(前編|後編|中編|総集編|特別編|番外編|おまけ|お負け|omake|recap|OP|ED|CM|PV|予告|ティザー|teaser|trailer|special|specials|picture drama|ova|oad)', re.I)
def _nj2(t): return nja(re.sub(r'^\s*(劇場版|映画)\s*', '', unicodedata.normalize('NFKC', t or '')))     # 「クラナド」 = 「劇場版 クラナド」
def _sim(a, b):
    s = 0
    ja_, jb = _nj2(a['ja']), _nj2(b['ja'])
    if len(ja_) >= 4 and len(jb) >= 4: s = max(s, difflib.SequenceMatcher(None, ja_, jb).ratio())
    ra, rb = nro(a['r']), nro(b['r'])
    if len(ra) >= 6 and len(rb) >= 6: s = max(s, difflib.SequenceMatcher(None, ra, rb).ratio())
    return s
def _marks(r): return {m.lower() for m in PART_MARK.findall(unicodedata.normalize('NFKC', ' '.join(x for x in (r['ja'], r['r'], r.get('en')) if x)))}
def sc_of(r):
    """제목 속 시즌·쿨 번호 (「2」·「第2クール」·「Part 2」·「2nd Season」 모두 2). 없으면 1"""
    t = unicodedata.normalize('NFKC', ' '.join(x for x in (r['ja'], r['r']) if x))
    m = re.search(r'(?:第\s*(\d+)\s*(?:期|クール|シーズン|部)|(\d+)(?:st|nd|rd|th)\s*(?:season|cour)|(?:season|part|cour)\s*(\d+)|\s(\d)\s*$)', t, re.I)
    return int(next(g for g in m.groups() if g)) if m else 1
fz_blocks = collections.defaultdict(set)
for i, r in enumerate(out):
    if not r['y']: continue
    j, ro_ = _nj2(season_base(r['ja']) or r['ja']), nro(r['r'])
    q_in = re.search(r'[「『]([^」』]{4,})[」』]', unicodedata.normalize('NFKC', r['ja'] or ''))   # 「Animatica「北斗の拳 …」第2クール」 같은 상표 감싸기
    if q_in and len(_nj2(q_in.group(1))) >= 4: fz_blocks[(r['y'], 'j', _nj2(q_in.group(1))[:3])].add(i)
    if len(j) >= 4: fz_blocks[(r['y'], 'j', j[:3])].add(i)
    if len(ro_) >= 6: fz_blocks[(r['y'], 'r', ro_[:4])].add(i)
n_fz = 0
for key, idx in fz_blocks.items():
    idx = sorted(idx)
    if len(idx) > 60: continue
    for x_ in range(len(idx)):
        for y_ in range(x_ + 1, len(idx)):
            a, b = out[idx[x_]], out[idx[y_]]
            if find(idx[x_]) == find(idx[y_]): continue
            weak_a, weak_b = not (a['al'] or a['mal']), not (b['al'] or b['mal'])
            # 한쪽은 AniList 번호만, 다른 쪽은 MAL 번호만 있는 짝은 원천 목록이 서로 못 이은 같은 작품일 수 있어 보조 항목처럼 비교
            cross = (a['al'] and not a['mal'] and b['mal'] and not b['al']) or (b['al'] and not b['mal'] and a['mal'] and not a['al'])
            if not (weak_a or weak_b or cross): continue      # 같은 번호 체계로 따로 둔 작품은 다른 작품으로 봄
            if a.get('_mv') != b.get('_mv') and (a['al'] or a['mal']) == (b['al'] or b['mal']): continue   # 한쪽이 보조 항목이면 그쪽 형식 표시는 믿지 않음
            if {a['ty'], b['ty']} & {'T'} and {a['ty'], b['ty']} & {'M'}: continue   # TV 시리즈와 극장판 총집편은 다른 작품
            if a['q'] and b['q'] and abs(a['q'] - b['q']) > 1: continue
            if (a['e'] or 0) > 2 and (b['e'] or 0) > 2 and abs(a['e'] - b['e']) > 3: continue
            if digits(a) != digits(b) or _marks(a) != _marks(b): continue
            # 「~Prelude~」와 「~Interlude~」처럼 끝이 다른 별개 편을 막으려고: 아주 비슷하거나(0.95), 괄호 덧붙임만 다를 때
            br = lambda t: bool(re.search(r'[\(（\[【]', t or ''))
            same_bare = nbare(a['ja']) and nbare(a['ja']) == nbare(b['ja']) and not (br(a['ja']) and br(b['ja']))   # 둘 다 괄호가 있으면 다른 판(UG 파트·SATORU 파트)
            # 시즌 표시를 뺀 제목끼리도 비교 (「…挽歌 2」 = 「…挽歌 Part 2」), 보조 항목은 앞뒤 상표(「Animatica「…」第2クール」)를 감싼 경우도
            def inner(r):
                # 「Animatica「北斗の拳 …」第2クール」처럼 따옴표 바깥이 영문 상표·시즌 표시뿐일 때만 안쪽 제목을 씀
                # (「「外科医エリーゼ」放送後ミニドラマ」처럼 바깥에 일본어 설명이 붙으면 다른 영상)
                t = unicodedata.normalize('NFKC', r['ja'] or ''); m = re.search(r'[「『]([^」』]{4,})[」』]', t)
                if not m: return None
                rest = SEASON_MARK.sub('', (t[:m.start()] + ' ' + t[m.end():]).strip())
                return _nj2(m.group(1)) if re.fullmatch(r'[A-Za-z0-9 .\-]*', rest.strip()) else None
            sa, sb = _nj2(season_base(a['ja']) or a['ja']), _nj2(season_base(b['ja']) or b['ja'])
            if weak_a and inner(a) and inner(a) == sb: sa = sb
            if weak_b and inner(b) and inner(b) == sa: sb = sa
            same_season = bool(sa) and sa == sb and (a.get('_sc') or sc_of(a)) == (b.get('_sc') or sc_of(b))
            if cross and not (same_season or _sim(a, b) >= 0.97): continue
            if _sim(a, b) >= 0.95 or same_bare or same_season: union(idx[x_], idx[y_]); n_fz += 1
print('비슷한 제목 보조 항목 합침', n_fz)

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
for r in merged:
    # 뮤직비디오: 대표 항목이 뮤직비디오이고 스페셜·웹·미분류·뮤직이면 형식을 P로
    if r.get('_mv') and r['ty'] in ('S', 'O', 'X', 'P'): r['ty'] = 'P'
    elif r['ty'] == 'P': r['ty'] = 'S'
print('뮤직비디오로 분류', sum(1 for r in merged if r['ty'] == 'P'))
print('중복 합치기:', len(out), '→', len(merged))
out = merged
key2i = {r['k']: i for i, r in enumerate(out)}
alias = {a: r['k'] for r in out for a in r.get('_alias', [])}
for r in out: r.pop('_alias', None); r.pop('_syn', None); r.pop('_mv', None)

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
