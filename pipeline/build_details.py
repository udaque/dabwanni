"""수집 원본(raw/)을 합쳐 사이트 데이터를 만듭니다.
- site/data/detail/<작품>.json   작품 상세
- site/data/people/<인물>.json   성우·스태프·가수 (+ index.json)
- site/data/studios/<회사>.json  제작사 (+ index.json)
- site/data/catalog.json         한국어 제목·제작사 한국어명을 보강해 다시 저장
모든 사람·회사·캐릭터 이름에는 한국어 표기가 들어갑니다. 확인된 표기(나무위키·Wikidata·사전)가 없으면 음역하고 auto 표시를 붙입니다."""
import os, re, json, shutil, glob, unicodedata
from common import *
from names_ko import add_season, add_arc, season_code, station_ko, JOB_KO, place_ko, date_ko, ja_company, studio_ko, person_ko, studio_sid, role_ko, role_eps, STAFF_ORDER, SOURCE_KO, GENRE_KO, TAG_KO
from translit import kana_to_hangul, name_to_hangul

COMPANY = re.compile(r'(スタジオ|Studio|STUDIO|作画部|アニメーション|プロダクション|株式会社|動画|工房|ピクチャーズ|フィルム|ワークス|Works|Pictures|Animation|\(株\))')
JA = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')

NB = 2048
def bucket(s):
    h = 0x811c9dc5
    for ch in s.encode('utf-8'): h = ((h ^ ch) * 0x01000193) & 0xffffffff
    return h % NB

def strip_disambig(t): return re.sub(r'\s*\([^)]*\)\s*$', '', t or '').strip()

class Names:
    def __init__(self):
        self.namu = load('namu', 'index') or {}
        self.korea = load('namu', 'korea') or {}
        wp = load('wikidata', 'people') or []
        self.wd_people = {pname(r['ja']): r for r in wp if r.get('ja') and r.get('ko')}
        self.wd_people_any = {pname(r['ja']): r for r in wp if r.get('ja')}
        self.wd_studio = {}
        for r in load('wikidata', 'studios') or []:
            for k in (r.get('ja'), r.get('en')):
                if k: self.wd_studio.setdefault(pname(k).lower(), r)
        self.wd_works = {r['mal']: r for r in load('wikidata', 'works') or []}
    def namu_one(self, ja, prefer=None):
        c = self.namu.get(pname(ja or '')) or []
        if prefer:
            for t in c:
                if any(p and p in t for p in prefer): return strip_disambig(t)
        plain = [t for t in c if '(' not in t]
        if len(plain) == 1: return plain[0]
        if len(c) == 1: return strip_disambig(c[0])
        return None
    def person(self, native, first=None, last=None):
        if native and re.search(r'[\uac00-\ud7a3]', native): return {'ko': native, 'ja': native}
        ko = self.namu_one(native, ['성우', '작곡', '작사', '가수', '애니메이터', '감독', '각본', '일러스트']) if native else None
        if not ko and native and pname(native) in self.wd_people: ko = self.wd_people[pname(native)]['ko']
        auto = not ko
        if not ko: ko, _ = person_ko(native, first, last)
        n = {'ko': ko, 'ja': native}
        if first or last: n['en'] = ' '.join(x for x in (first, last) if x)
        if auto: n['auto'] = 1
        return n
    def character(self, native, full=None, first=None, last=None, work_titles=()):
        ko = self.namu_one(native, list(work_titles)) if native else None
        if ko: return {k: v for k, v in {'ko': ko, 'ja': native, 'en': full}.items() if v}
        if native and re.fullmatch(r'[\u3040-\u30ff・ー\s]+', native): k = kana_to_hangul(native)
        elif native or first or last: k, _ = name_to_hangul(native, first, last)
        else: k = full
        return {k2: v for k2, v in {'ko': k, 'ja': native, 'en': full, 'auto': 1}.items() if v}
    def studio(self, name, work=None):
        isja = bool(JA.search(name))
        ko = self.namu_one(name, ['기업', '회사', '스튜디오']) if isja else None
        wd = self.wd_studio.get(pname(name).lower()) or {}
        if not ko and wd.get('ko'): ko = wd['ko']
        auto = False
        if not ko:
            ko, auto = studio_ko(name)
            if isja and auto: ko = ja_company(name, work)
        n = {'ko': ko, 'ja': name if isja else wd.get('ja'), 'en': wd.get('en') if isja else name}
        if auto: n['auto'] = 1
        return {k: v for k, v in n.items() if v}, (wd.get('founded') or '')[:4] or None

def expand_eps(r):
    o = []
    for part in re.split(r'[,、\s]+', r or ''):
        m = re.fullmatch(r'(\d+)-(\d+)', part)
        if m and int(m.group(2)) - int(m.group(1)) < 500: o += [str(x) for x in range(int(m.group(1)), int(m.group(2)) + 1)]
        elif part.isdigit(): o.append(part)
    return o

def parse_air(seq):
    """위키 회차 표의 방영일 문자열들 → (년, 월) 목록. 「2025年1月10日」 뒤로 「1月17日」처럼 연도가 빠지면 앞 연도를 이어 씀."""
    out, yr = [], None
    for a in seq:
        m = re.search(r'(?:(\d{4})\s*年)?\s*(\d{1,2})\s*月', a or '')
        if not m: out.append(None); continue
        if m.group(1): yr = int(m.group(1))
        out.append((yr, int(m.group(2))) if yr else None)
    return out

def episode_offset(w, E, sy_eps, jw_eps, rels, BY):
    """이어서 세는 시즌의 앞쪽 회차 수(오프셋). 0이면 1화부터, None이면 알 수 없음(위키 회차는 쓰지 않음)."""
    nums = lambda L: sorted(int(e['no']) for e in L if str(e.get('no', '')).isdigit())
    sn, jn = nums(sy_eps), nums(jw_eps)
    if not E: return 0
    # 1) 쇼보이 캘린더는 시즌마다 따로라, 번호가 화수보다 크면 그 첫 번호가 곧 시작점
    if sn and sn[-1] > E: return sn[0] - 1
    if not jn or jn[-1] <= E: return 0
    # 2) 위키 문서가 여러 시즌을 담은 경우: 방영 시작 분기에 나간 회차부터
    if w.get('y') and w.get('q'):
        start = (w['y'], (w['q'] - 1) * 3 + 1)
        dated = [(int(e['no']), d) for e, d in zip(jw_eps, parse_air([e.get('air') for e in jw_eps])) if d and str(e.get('no', '')).isdigit()]
        cand = [n for n, d in dated if start <= d < (start[0] + (start[1] + 5) // 12, (start[1] + 5) % 12 + 1)]
        if cand: return min(cand) - 1
    # 3) AniList의 이전 시즌들 화수를 더함
    total, seen, cur = 0, set(), rels or []
    while True:
        pre = [r['k'] for r in cur if r.get('type') == 'PREQUEL' and r['k'] in BY and r['k'] not in seen]
        if not pre: break
        p = pre[0]; seen.add(p); pw = BY[p]
        if pw.get('ty') in ('T', 'O') and pw.get('e'): total += pw['e']
        cur = (load('anilist', p) or {}).get('relations', {}).get('edges', [])
        cur = [{'k': 'a' + str(x['node']['id']), 'type': x['relationType']} for x in cur]
    if total and jn[-1] >= total + 1 and any(total < n <= total + E for n in jn): return total
    return None

LAF_VARIANT = re.compile(r'\s*[\(（\[]?\s*(자막|더빙|무삭제|우리말\s*더빙|한국어\s*더빙)\s*[\)）\]]?\s*$')

def nko(t):
    """한국어 제목 비교용: 띄어쓰기·기호 제거, 시즌 표기 통일(2기·시즌 2·2nd season → 2기), 끝의 (자막)·(더빙)·(무삭제) 표기 제거"""
    t = unicodedata.normalize('NFKC', t or '').lower()
    for _ in range(2): t = LAF_VARIANT.sub('', t)
    t = re.sub(r'(?:시즌|season)\s*(\d+)', r'\1기', t)
    t = re.sub(r'(\d+)(?:st|nd|rd|th)\s*season', r'\1기', t)
    return re.sub(r'[\s\-_:;!?！？・·.,~〜()（）\[\]「」『』<>《》【】\'"“”‘’]', '', t)

def laftel_kind(it):
    """라프텔 항목의 판 구분: 더빙 / 무삭제 / 자막(기본)"""
    n = it.get('name') or ''
    if it.get('is_dubbed') or re.search(r'더빙', n): return '더빙'
    if it.get('is_uncensored') or re.search(r'무삭제', n): return '무삭제'
    return '자막'

def laftel_index():
    """raw/laftel/<연도-분기>.json → {(연도, 분기): [(정규화한 제목, 항목)]}. 판권 만료·시청 불가 항목은 뺌."""
    idx = {}
    for f in glob.glob(os.path.join(RAW, 'laftel', '*.json')):
        try:
            d = json.load(open(f, encoding='utf-8')); y, q = map(int, os.path.basename(f)[:-5].split('-'))
        except Exception: continue
        idx[(y, q)] = [(nko(it.get('name')), it) for it in d.get('items', [])
                       if it.get('id') and it.get('name') and not it.get('is_expired') and it.get('is_viewing') is not False]
    return idx

def laftel_match(w, idx):
    """같은 분기(앞뒤 한 분기 포함)에 한국어 제목이 같은 라프텔 항목들을 판별로 모음: [(판, 번호)].
    자막판·더빙판·무삭제판이 따로 있으면 모두 돌려줌. 같은 판이 둘 이상이면 어느 것인지 애매해 그 판은 뺌."""
    if not idx or not w.get('ko') or not w.get('y'): return []
    name = nko(w['ko'])
    qs = [(w['y'], q) for q in (1, 2, 3, 4)]
    if w.get('q'):
        n = w['y'] * 4 + w['q'] - 1
        qs = [(w['y'], w['q']), ((n - 1) // 4, (n - 1) % 4 + 1), ((n + 1) // 4, (n + 1) % 4 + 1)]
    by = {}
    for k in qs:
        for t, it in idx.get(k, []):
            if t == name: by.setdefault(laftel_kind(it), {})[it['id']] = it
    order = {'자막': 0, '더빙': 1, '무삭제': 2}
    return [(kind, next(iter(ids))) for kind, ids in sorted(by.items(), key=lambda x: order[x[0]]) if len(ids) == 1]

VOD = {'danime': 'dアニメストア', 'unext': 'U-NEXT', 'abema': 'ABEMA', 'netflix': 'Netflix', 'prime': 'Prime Video', 'nicovideo': 'ニコニコ',
       'disneyplus': 'Disney+', 'youtube': 'YouTube', 'crunchyroll': 'Crunchyroll'}
from names_ko import STATION_KO
STATION_KO_KEYS = set(STATION_KO)
JWROLE = {'script': '각본', 'storyboard': '콘티', 'director': '연출', 'animdir': '작화감독', 'chiefanimdir': '총작화감독'}

def main():
    W = load_catalog(); BY = {w['k']: w for w in W}
    NM = Names()
    out = {x: os.path.join(SITE, 'data', x) for x in ('detail', 'people', 'studios')}
    for p in out.values(): shutil.rmtree(p, ignore_errors=True); os.makedirs(p)
    people, studios, prof = {}, {}, {}
    for f in glob.glob(os.path.join(RAW, 'anilist_people', '*.json')):
        try: d = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        if isinstance(d, dict) and d.get('id'): prof[d['id']] = d          # 정보 없음으로 저장된 파일은 받은 시각(_at)만 있음

    romaji = {}
    for f in glob.glob(os.path.join(RAW, 'anilist', '*.json')):
        try:                                   # 파일 하나가 깨져도 읽기 준비 전체가 멈추지 않게
            d = json.load(open(f, encoding='utf-8')) or {}
            for e in (d.get('staff') or {}).get('edges', []):
                n = e['node']['name']; romaji.setdefault(pname(n.get('native') or ''), (n.get('first'), n.get('last')))
            for e in (d.get('characters') or {}).get('edges', []):
                for r in e.get('voiceActorRoles') or []:
                    v = r.get('voiceActor') or {}
                    if v.get('name'): romaji.setdefault(pname(v['name'].get('native') or ''), (v['name'].get('first'), v['name'].get('last')))
        except Exception as ex: print('읽기 건너뜀', os.path.basename(f), type(ex).__name__, ex)
    romaji.pop('', None)

    def P(native, first=None, last=None, al_id=None):
        i = pid(native or ' '.join(x for x in (last, first) if x))
        if not (first or last) and native: first, last = romaji.get(pname(native), (None, None))
        if i not in people:
            people[i] = {'id': i, 'name': NM.person(native, first, last), 'roles': [], 'staff': [], 'songs': []}
        if al_id and 'profile' not in people[i]:
            pr = prof.get(al_id) or {}
            wd = NM.wd_people_any.get(pname(native or ''), {})
            b = pr.get('dateOfBirth') or {}
            pf = {'birth': date_ko('-'.join(str(x) for x in (b.get('year'), b.get('month'), b.get('day')) if x) or (wd.get('birth') or '')[:10]),
                  'hometown': place_ko(pr.get('homeTown')), 'jobs': [JOB_KO.get(j, j) for j in pr.get('primaryOccupations') or []] or None,
                  # 일본어·영어 화면용 원래 값 (생일은 YYYY-MM-DD, 출신지는 AniList 원문)
                  'birth_iso': '-'.join(f'{x:02d}' if i else str(x) for i, x in enumerate((b.get('year'), b.get('month'), b.get('day'))) if x) or (wd.get('birth') or '')[:10] or None,
                  'hometown_raw': pr.get('homeTown') or None,
                  'image': (pr.get('image') or {}).get('medium'),
                  'years': pr.get('yearsActive') or None, 'agency': wd.get('agko') or wd.get('agja'), 'agency_ja': wd.get('agja') or None}
            pf = {k: v for k, v in pf.items() if v}
            if pf: people[i]['profile'] = pf
        return i
    def ref(i): n = people[i]['name']; return {'pid': i, **{k: n[k] for k in ('ko', 'ja', 'en', 'auto') if k in n}}
    cur_work = [None]
    def S(name):
        sid = studio_sid(name)
        if sid not in studios:
            nm, founded = NM.studio(name, cur_work[0])
            studios[sid] = {'id': sid, 'name': nm, 'works': []}
            if founded: studios[sid]['founded'] = founded
        return sid
    def sref(sid): n = studios[sid]['name']; return {'sid': sid, **{k: n[k] for k in ('ko', 'ja', 'en', 'auto') if k in n}}

    LAF = laftel_index()
    made, nonjp, details = 0, {}, {}
    errors = []
    def one(w):
        nonlocal made
        k = w['k']
        al, sy, at, tm, jw, mu, ab = (load(s, k) for s in ('anilist', 'syoboi', 'animethemes', 'tmdb', 'jawiki', 'music', 'anitabi'))
        wdw = NM.wd_works.get(str(w['mal'])) if w['mal'] else None
        # 제목 (한국어: AniDB → TMDB → Wikidata → 나무위키)
        ko = w.get('ko') or ((tm or {}).get('titles') or {}).get('ko') or (wdw or {}).get('ko') or NM.namu_one(w.get('ja'))
        if ko: ko = add_season(add_arc(ko, w.get('ja')), w.get('ja'), w.get('r'))
        if ko: w['ko'] = ko
        cur_work[0] = (w.get('ja'), ko)
        if not any((al, sy, at, tm, jw, mu, ab)):
            for x in w.get('_stu_names') or []: studios[S(x)]['works'].append({'k': k, 'as': 'main'})
            return
        d = {'k': k, 'titles': {x: v for x, v in {'ko': ko, 'ja': ((al or {}).get('title') or {}).get('native') or w.get('ja'),
                                                   'en': ((al or {}).get('title') or {}).get('english') or w.get('en')}.items() if v}}
        work_names = [x for x in (ko, w.get('ja')) if x]
        cur_work[0] = (w.get('ja'), ko)
        if al:
            stmap = {'FINISHED': 'F', 'RELEASING': 'O', 'NOT_YET_RELEASED': 'U', 'CANCELLED': 'C', 'HIATUS': 'H'}
            if al.get('status') in stmap: w['st'] = stmap[al['status']]
            # 방영 전·방영 중인 작품은 AniList 화수가 「1」 같은 자리표시일 때가 많아, 그때는 화수를 줄이지 않음
            if al.get('episodes') and (al.get('status') == 'FINISHED' or al['episodes'] > (w.get('e') or 0)): w['e'] = al['episodes']
            if al.get('countryOfOrigin') and al['countryOfOrigin'] != 'JP': nonjp[k] = al['countryOfOrigin']
            if al.get('source'): d['source'] = SOURCE_KO.get(al['source'], al['source'])
            d['genres'] = [GENRE_KO.get(g, g) for g in al.get('genres') or []]
            d['tags'] = [TAG_KO[t['name'].lower()] for t in al.get('tags') or [] if t['name'].lower() in TAG_KO and not t.get('isMediaSpoiler')][:12]
            for f in ('averageScore', 'popularity', 'favourites'):
                if al.get(f): d[f] = al[f]
            if al.get('isAdult'): d['adult'] = True
            if (al.get('trailer') or {}).get('site') == 'youtube': d['pv'] = 'https://www.youtube.com/watch?v=' + al['trailer']['id']
            d['links'] = [{'site': l['site'], 'url': l['url']} for l in al.get('externalLinks') or [] if l.get('type') in ('INFO', 'SOCIAL')]
            d['relations'] = [{'k': 'a' + str(e['node']['id']), 'type': e['relationType']} for e in (al.get('relations') or {}).get('edges', []) if ('a' + str(e['node']['id'])) in BY]
        if w.get('site') and not any(l['site'] == 'Official Site' for l in d.get('links', [])): d.setdefault('links', []).insert(0, {'site': 'Official Site', 'url': w['site']})

        # 캐릭터·성우
        chars, byname = [], {}
        for e in ((al or {}).get('characters') or {}).get('edges', []):
            n = e['node']['name']
            c = {'name': NM.character(n.get('native'), n.get('full'), n.get('first'), n.get('last'), work_names), 'role': e['role'], 'cast': []}
            img = (e['node'].get('image') or {}).get('medium')
            if img and 'default' not in img: c['img'] = img
            LANG = {'Japanese': 'ja', 'Korean': 'ko', 'English': 'en'}
            seen = set()
            for r in e.get('voiceActorRoles') or []:
                v = r.get('voiceActor') or {}; lang = LANG.get(v.get('languageV2'))
                if not lang or (v.get('id'), lang) in seen: continue
                seen.add((v.get('id'), lang))
                vn = v['name']; i = P(vn.get('native') or vn.get('full'), vn.get('first'), vn.get('last'), v['id'])
                c['cast'].append({**ref(i), 'lang': lang, **({'note': r['roleNotes']} if r.get('roleNotes') else {})})
            chars.append(c)
            for x in (n.get('native'), n.get('full')):
                if x: byname[pname(x)] = c
        for sc in (sy or {}).get('cast', []):
            c = byname.get(pname(sc['char']))
            if not c:
                c = {'name': NM.character(sc['char'], work_titles=work_names), 'role': None, 'cast': []}; chars.append(c); byname[pname(sc['char'])] = c
            i = P(sc['name'])
            if not any(v['pid'] == i for v in c['cast']): c['cast'].append({**ref(i), 'lang': 'ja'})
        for c in chars:
            for v in c['cast']:
                people[v['pid']]['roles'].append({'k': k, 'char': c['name'], 'role': c.get('role'), 'lang': v['lang']})
        if chars: d['characters'] = chars

        al_ep_recs = []      # AniList 회차 표기가 붙은 인물 기록 (이어 세는 시즌이면 나중에 화면 번호로 바꿈)
        # 스태프 (작품 전체 + 회차별)
        staff, ep_staff = {}, {}
        for e in ((al or {}).get('staff') or {}).get('edges', []):
            n = e['node']['name']; i = P(n.get('native') or n.get('full'), n.get('first'), n.get('last'), e['node']['id'])
            r, eps = role_ko(e['role']), role_eps(e['role'])
            if eps:
                for no in eps: ep_staff.setdefault(no, {}).setdefault(r, set()).add(i)
            elif i not in staff.get(r, []): staff.setdefault(r, []).append(i)
            rec = {'k': k, 'role': r, 'eps': eps}; people[i]['staff'].append(rec)
            if eps: al_ep_recs.append(rec)
        for s in (sy or {}).get('staff', []):
            r = role_ko(s['role'])
            if r in ('애니메이션 제작', '제작', '제작위원회'): continue
            i = P(s['name'])
            if i not in staff.get(r, []):
                staff.setdefault(r, []).append(i); people[i]['staff'].append({'k': k, 'role': r})
        order = {r: n for n, r in enumerate(STAFF_ORDER)}
        if staff: d['staff'] = [{'role': r, 'people': [ref(i) for i in v]} for r, v in sorted(staff.items(), key=lambda t: order.get(t[0], 999))]

        # 제작사: 원청 / 협력(회차별) / 제작위원회·참여사
        main, coop, committee = [], {}, []
        for e in ((al or {}).get('studios') or {}).get('edges', []):
            sid = S(e['node']['name'])
            (main if e['isMain'] and e['node'].get('isAnimationStudio') else committee).append(sid)
        if not main: main = [S(x) for x in w.get('_stu_names') or []]
        for s in (sy or {}).get('staff', []):
            if s['role'] in ('アニメーション制作', '制作'): main.append(S(s['name']))
            if s['role'] == '製作': committee.append(S(s['name']))

        # 회차 — 시즌을 이어서 세는 작품(예: 약사의 혼잣말 3기는 49~60화) 처리
        #   no: 화면에 보이는 회차 번호(이어 센 번호), i: 이 작품 안에서의 순서(1부터). 시청 기록은 i로 저장.
        tm_n = sorted(int(e['no']) for e in (tm or {}).get('episodes', []) if str(e.get('no', '')).isdigit())
        tm_abs = bool(tm_n) and tm_n[0] > 1          # TMDB가 시즌 회차를 시리즈 전체 번호(49~60화)로 매긴 경우
        E = w.get('e') or 0
        if w.get('st') in ('U', 'O', 'H') and len(tm_n) > E: E = len(tm_n)     # 방영 전 자리표시 화수(1화)보다 TMDB 회차 목록이 실제에 가까움
        O = episode_offset(w, E, (sy or {}).get('episodes', []), (jw or {}).get('episodes', []), d.get('relations'), BY)      # d['relations']: [{'k','type'}] 꼴
        if tm_abs and not ((sy or {}).get('episodes')): O = tm_n[0] - 1
        if O: d['ep_offset'] = O
        def disp(n_local): return str(O + n_local)
        def from_src(no, local):
            """출처 번호를 화면 번호로. local=True면 그 출처가 시즌 안에서 1부터 센 번호."""
            if not str(no).isdigit(): return str(no)
            n = int(no)
            return disp(n) if (local and O) else str(n)
        def in_range(no):
            return not (E and O is not None and str(no).isdigit() and not (O < int(no) <= O + E))
        # 여기까지 ep_staff에는 AniList 스태프의 「(eps 1-3)」 표기만 들어 있음: 시즌 안 번호로 보고 화면 번호로 옮김
        if O: ep_staff = {(disp(int(no)) if no.isdigit() else no): v for no, v in ep_staff.items()}
        if O:
            for rec in al_ep_recs: rec['eps'] = [disp(int(x)) if x.isdigit() else x for x in rec['eps']]
        sy_local = bool(E) and all(int(x['no']) <= E for x in (sy or {}).get('episodes', []) if x['no'].isdigit())
        eps = {}
        for e in (tm or {}).get('episodes', []):
            no = from_src(e['no'], not tm_abs)
            if not in_range(no): continue
            eps[no] = {**e, 'no': no, 'title': dict(e.get('title') or {})}
        for e in (sy or {}).get('episodes', []):
            no = from_src(e['no'], sy_local)
            if not in_range(no): continue
            x = eps.setdefault(no, {'no': no, 'title': {}})
            x['title'].setdefault('ja', e['title']['ja'])
            if e.get('endcard'):
                i = P(e['endcard']); x['endcard'] = ref(i); people[i]['staff'].append({'k': k, 'role': '엔드카드', 'eps': [no]})
        jw_ok = O is not None
        for e in (jw or {}).get('episodes', []) if jw_ok else []:
            no = e['no']
            if not in_range(no): continue                      # 위키 문서가 시리즈 전체 회차를 담고 있으면 이 시즌 것만
            x = eps.setdefault(no, {'no': no, 'title': {}})
            if e.get('title'): x['title'].setdefault('ja', e['title'])
            if e.get('air') and not x.get('air'): x['air'] = e['air']
            for f, r in JWROLE.items():
                for n in e.get(f, []):
                    if COMPANY.search(n): coop.setdefault(S(re.sub(r'作画部$', '', n)), set()).add(no)
                    else:
                        i = P(n); ep_staff.setdefault(no, {}).setdefault(r, set()).add(i)
                        people[i]['staff'].append({'k': k, 'role': r, 'eps': [no]})
            for n in e.get('studio', []): coop.setdefault(S(n), set()).add(no)
        for no, roles in ep_staff.items():
            x = eps.setdefault(no, {'no': no, 'title': {}})
            x['staff'] = [{'role': r, 'people': [ref(i) for i in ids]} for r, ids in sorted(roles.items(), key=lambda t: order.get(t[0], 999))]
        for sid, nos in coop.items():
            for no in nos: eps.setdefault(no, {'no': no, 'title': {}}).setdefault('studios', []).append(sref(sid))

        # 주제가 (しょぼいカレンダー 우선) + 회차별 사용 곡
        songs = (sy or {}).get('songs') or (at or {}).get('songs') or []
        for s in songs:
            by = {}
            for c in s['credits']:
                c.update(ref(P(c['name']))); by.setdefault(c['pid'], []).append(c['role'])
            for i, roles in by.items(): people[i]['songs'].append({'k': k, 'kind': s['kind'], 'title': s['title'], 'roles': roles})
            for no in expand_eps(s.get('eps')):
                no = from_src(no, sy_local)
                if not in_range(no): continue
                eps.setdefault(no, {'no': no, 'title': {}}).setdefault('songs', []).append({'kind': s['kind'], 'title': s['title']})
        if songs: d['songs'] = songs
        if eps:
            L = sorted(eps.values(), key=lambda e: (0, int(e['no'])) if e['no'].isdigit() else (1, e['no']))
            for e in L:
                if e['no'].isdigit(): e['i'] = int(e['no']) - (O or 0)
            # 회차 목록(TMDB·쇼보이 등)이 화수보다 길면, 아직 안 끝난 작품은 목록 쪽이 실제에 가까움
            mx = max((e['i'] for e in L if isinstance(e.get('i'), int)), default=0)
            if w.get('st') in ('U', 'O', 'H') and mx > (w.get('e') or 0): w['e'] = mx
            use = {}
            for e in L:
                for s in e.get('songs', []): use[(s['kind'], s['title'])] = use.get((s['kind'], s['title']), 0) + 1
            for e in L:
                for s in e.get('songs', []):
                    if use[(s['kind'], s['title'])] <= 2 and len(L) > 4: s['special'] = True   # 특수 엔딩 등
            d['episodes'] = L

        main, committee = list(dict.fromkeys(main)), [s for s in dict.fromkeys(committee) if s not in main]
        d['studios'] = {'main': [sref(s) for s in main], 'committee': [sref(s) for s in committee],
                        'coop': [{**sref(s), 'eps': sorted(n, key=lambda x: int(x) if x.isdigit() else 0)} for s, n in coop.items() if s not in main]}
        for role in ('main', 'coop', 'committee'):
            for s in d['studios'][role]: studios[s['sid']]['works'].append({'k': k, 'as': role, 'eps': s.get('eps')})
        if sy:
            for f in ('broadcast', 'rebroadcast'):
                if sy.get(f): d[f] = [{**x, 'station': station_ko(x['station'])} for x in sy[f]]
            if sy.get('notes'): d['notes'] = sy['notes']
        if ko and NM.korea.get(ko): d['korea'] = NM.korea[ko]
        ott = {c: list(v) for c, v in ((tm or {}).get('ott') or {}).items()}
        for c in ('JP', 'US'):
            for v in ((w.get('vod') or {}).get(c) or []):
                if not any(p['name'] == VOD[v] for p in ott.setdefault(c, [])): ott[c].append({'name': VOD[v]})
        def ott_base(n):
            # 광고형 요금제·아마존 채널 경유는 같은 서비스로 봄 (예: 「Netflix Standard with Ads」→ Netflix, 「Crunchyroll Amazon Channel」→ Crunchyroll)
            if not isinstance(n, str): return n
            n = re.sub(r'\s+(Standard|Basic)?\s*with Ads$', '', n).strip()
            n = re.sub(r'\s+Amazon Channel$', '', n).strip()
            return {'dAnime': 'dアニメストア', 'Amazon Prime Video': 'Prime Video'}.get(n, n)
        for c in ott:
            seen, out = set(), []
            for p in ott[c]:
                n = ott_base(p['name']); n = station_ko(n) if isinstance(n, str) and n in STATION_KO_KEYS else n
                key = json.dumps(n, ensure_ascii=False, sort_keys=True) if not isinstance(n, str) else n
                if key in seen: continue
                seen.add(key); out.append({**p, 'name': n})
            ott[c] = out
        lf = laftel_match(w, LAF)
        if lf:
            kr = [p for p in ott.get('KR', []) if 'laftel' not in str(p.get('name')).lower() and '라프텔' not in str(p.get('name'))]
            many = len(lf) > 1          # 판이 하나뿐이면 그냥 「라프텔」, 여럿이면 「라프텔 (자막)」·「라프텔 (더빙)」
            ott['KR'] = [{'name': f'라프텔 ({kind})' if many else '라프텔', 'url': f'https://laftel.net/item/{lid}'} for kind, lid in lf] + kr
        if any(ott.values()): d['ott'] = ott; d['ott_updated'] = (tm or {}).get('ott_updated')
        if (jw or {}).get('box_office'): d['box_office'] = jw['box_office']
        if (mu or {}).get('albums'): d['albums'] = mu['albums']
        if ab:
            d['pilgrimage'] = {**ab, 'city': {'ko': place_ko(ab['city']), 'ja': ab['city']} if ab.get('city') else None,
                               'points': [{**p, 'name': {'ko': place_ko(p['name']), 'ja': p['name'], 'auto': 1}} for p in ab.get('points', [])]}
        d['sources'] = [n for n, x in zip(('AniList', 'しょぼいカレンダー', 'AnimeThemes', 'TMDB', '위키백과', 'MusicBrainz', 'Anitabi'), (al, sy, at, tm, jw, mu, ab)) if x]
        details[k] = d; made += 1
    for w in W:
        try: one(w)
        except Exception as ex:
            import traceback
            errors.append({'k': w['k'], 'error': f'{type(ex).__name__}: {ex}', 'trace': traceback.format_exc()[-1500:]})
    if errors:
        print(f'병합 중 작품 {len(errors)}건 오류 (이 작품들만 빠지고 나머지는 계속 진행)')
        for x in errors[:5]: print(' ', x['k'], x['error'])          # 전체 오류 위치는 logs/build.jsonl (배포 단계가 build.out의 'Traceback'으로 실패를 판단하므로 여기엔 찍지 않음)
    logs = os.path.join(ROOT, 'logs'); os.makedirs(os.path.join(logs, 'summary'), exist_ok=True)
    with open(os.path.join(logs, 'build.jsonl'), 'w', encoding='utf-8') as f:
        for x in errors: f.write(json.dumps(x, ensure_ascii=False) + '\n')
    json.dump({'source': 'build', 'status': 'ok', 'counts': {'ok': made, 'empty': 0, 'fail': len(errors), 'skip': 0},
               'reason': f'작품 {len(errors)}건 병합 오류 (해당 작품만 제외)' if errors else '',
               'examples': [f"{x['k']}: {x['error'][:160]}" for x in errors[:5]]},
              open(os.path.join(logs, 'summary', 'build.json'), 'w', encoding='utf-8'), ensure_ascii=False)

    # Cloudflare Pages 파일 수 제한(2만 개)에 맞춰 묶음 파일로 저장. 묶음 번호 = FNV-1a(ID) % N (사이트 스크립트와 같은 계산)
    idx = {'people': {}, 'studios': {}}
    for nm, coll in (('detail', details), ('people', people), ('studios', studios)):
        buckets = {}
        for i, p in coll.items():
            buckets.setdefault(bucket(i), {})[i] = p
            if nm != 'detail': idx[nm][i] = [x for x in (p['name'].get('ko'), p['name'].get('ja'), p['name'].get('en')) if x]
        for b, v in buckets.items():
            json.dump(v, open(os.path.join(out[nm], f'{b}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        if nm != 'detail': json.dump(idx[nm], open(os.path.join(out[nm], 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(nonjp, open(os.path.join(SITE, 'data', 'nonjp.json'), 'w'), separators=(',', ':'))
    # 카탈로그에 한국어 제목·제작사 한국어명 반영
    cp = os.path.join(SITE, 'data', 'catalog.json'); c = json.load(open(cp, encoding='utf-8'))
    if 'sm' not in c['fields']:
        c['fields'].append('sm'); [r.append(None) for r in c['rows']]
    ki, si, ei, smi = c['fields'].index('ko'), c['fields'].index('st'), c['fields'].index('e'), c['fields'].index('sm'); n_ko = 0
    for r in c['rows']:
        w = BY[r[0]]
        r[smi] = season_code(w.get('ja'), w.get('r'), w.get('en'))      # 제목 뒤 시즌·쿨 꼬리표용
        if w.get('ko') and r[ki] != w['ko']: n_ko += 1 if not r[ki] else 0; r[ki] = w['ko']
        r[si], r[ei] = w.get('st'), w.get('e')
    for s in c['studios']:
        if s[3] in studios and not studios[s[3]]['name'].get('auto'): s[1], s[2] = studios[s[3]]['name']['ko'], False
    json.dump(c, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'작품 상세 {made}편, 인물 {len(people)}명, 제작사 {len(studios)}곳, 새로 채운 한국어 제목 {n_ko}편, 일본 외 제작 {len(nonjp)}편')

if __name__ == '__main__': main()
