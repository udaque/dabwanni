"""수집 원본(raw/)을 합쳐 사이트 데이터를 만듭니다.
- site/data/detail/<작품>.json   작품 상세
- site/data/people/<인물>.json   성우·스태프·가수 (+ index.json)
- site/data/studios/<회사>.json  제작사 (+ index.json)
- site/data/catalog.json         한국어 제목·제작사 한국어명을 보강해 다시 저장
모든 사람·회사·캐릭터 이름에는 한국어 표기가 들어갑니다. 확인된 표기(나무위키·Wikidata·사전)가 없으면 음역하고 auto 표시를 붙입니다."""
import os, re, json, shutil, glob
from common import *
from names_ko import add_season, station_ko, JOB_KO, place_ko, date_ko, ja_company, studio_ko, person_ko, studio_sid, role_ko, role_eps, STAFF_ORDER, SOURCE_KO, GENRE_KO, TAG_KO
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
        d = json.load(open(f, encoding='utf-8'))
        if d: prof[d['id']] = d

    romaji = {}
    for f in glob.glob(os.path.join(RAW, 'anilist', '*.json')):
        d = json.load(open(f, encoding='utf-8')) or {}
        for e in (d.get('staff') or {}).get('edges', []):
            n = e['node']['name']; romaji.setdefault(pname(n.get('native') or ''), (n.get('first'), n.get('last')))
        for e in (d.get('characters') or {}).get('edges', []):
            for r in e.get('voiceActorRoles') or []:
                v = r.get('voiceActor') or {}
                if v.get('name'): romaji.setdefault(pname(v['name'].get('native') or ''), (v['name'].get('first'), v['name'].get('last')))
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
                  'image': (pr.get('image') or {}).get('medium'),
                  'years': pr.get('yearsActive') or None, 'agency': wd.get('agko') or wd.get('agja')}
            pf = {k: v for k, v in pf.items() if v}
            if pf: people[i]['profile'] = pf
        return i
    def ref(i): n = people[i]['name']; return {'pid': i, **{k: n[k] for k in ('ko', 'ja', 'auto') if k in n}}
    cur_work = [None]
    def S(name):
        sid = studio_sid(name)
        if sid not in studios:
            nm, founded = NM.studio(name, cur_work[0])
            studios[sid] = {'id': sid, 'name': nm, 'works': []}
            if founded: studios[sid]['founded'] = founded
        return sid
    def sref(sid): n = studios[sid]['name']; return {'sid': sid, **{k: n[k] for k in ('ko', 'ja', 'auto') if k in n}}

    made, nonjp, details = 0, {}, {}
    for w in W:
        k = w['k']
        al, sy, at, tm, jw, mu, ab = (load(s, k) for s in ('anilist', 'syoboi', 'animethemes', 'tmdb', 'jawiki', 'music', 'anitabi'))
        wdw = NM.wd_works.get(str(w['mal'])) if w['mal'] else None
        # 제목 (한국어: AniDB → TMDB → Wikidata → 나무위키)
        ko = w.get('ko') or ((tm or {}).get('titles') or {}).get('ko') or (wdw or {}).get('ko') or NM.namu_one(w.get('ja'))
        if ko: ko = add_season(ko, w.get('ja'), w.get('r'))
        if ko: w['ko'] = ko
        cur_work[0] = (w.get('ja'), ko)
        if not any((al, sy, at, tm, jw, mu, ab)):
            for x in w.get('_stu_names') or []: studios[S(x)]['works'].append({'k': k, 'as': 'main'})
            continue
        d = {'k': k, 'titles': {x: v for x, v in {'ko': ko, 'ja': ((al or {}).get('title') or {}).get('native') or w.get('ja'),
                                                   'en': ((al or {}).get('title') or {}).get('english') or w.get('en')}.items() if v}}
        work_names = [x for x in (ko, w.get('ja')) if x]
        cur_work[0] = (w.get('ja'), ko)
        if al:
            stmap = {'FINISHED': 'F', 'RELEASING': 'O', 'NOT_YET_RELEASED': 'U', 'CANCELLED': 'C', 'HIATUS': 'H'}
            if al.get('status') in stmap: w['st'] = stmap[al['status']]
            if al.get('episodes'): w['e'] = al['episodes']
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

        # 스태프 (작품 전체 + 회차별)
        staff, ep_staff = {}, {}
        for e in ((al or {}).get('staff') or {}).get('edges', []):
            n = e['node']['name']; i = P(n.get('native') or n.get('full'), n.get('first'), n.get('last'), e['node']['id'])
            r, eps = role_ko(e['role']), role_eps(e['role'])
            if eps:
                for no in eps: ep_staff.setdefault(no, {}).setdefault(r, set()).add(i)
            elif i not in staff.get(r, []): staff.setdefault(r, []).append(i)
            people[i]['staff'].append({'k': k, 'role': r, 'eps': eps})
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

        # 회차
        eps = {}
        for e in (tm or {}).get('episodes', []): eps[e['no']] = {**e, 'title': dict(e.get('title') or {})}
        for e in (sy or {}).get('episodes', []):
            x = eps.setdefault(e['no'], {'no': e['no'], 'title': {}})
            x['title'].setdefault('ja', e['title']['ja'])
            if e.get('endcard'):
                i = P(e['endcard']); x['endcard'] = ref(i); people[i]['staff'].append({'k': k, 'role': '엔드카드', 'eps': [e['no']]})
        for e in (jw or {}).get('episodes', []):
            x = eps.setdefault(e['no'], {'no': e['no'], 'title': {}})
            if e.get('title'): x['title'].setdefault('ja', e['title'])
            if e.get('air') and not x.get('air'): x['air'] = e['air']
            for f, r in JWROLE.items():
                for n in e.get(f, []):
                    if COMPANY.search(n): coop.setdefault(S(re.sub(r'作画部$', '', n)), set()).add(e['no'])
                    else:
                        i = P(n); ep_staff.setdefault(e['no'], {}).setdefault(r, set()).add(i)
                        people[i]['staff'].append({'k': k, 'role': r, 'eps': [e['no']]})
            for n in e.get('studio', []): coop.setdefault(S(n), set()).add(e['no'])
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
                eps.setdefault(no, {'no': no, 'title': {}}).setdefault('songs', []).append({'kind': s['kind'], 'title': s['title']})
        if songs: d['songs'] = songs
        if eps:
            L = sorted(eps.values(), key=lambda e: (0, int(e['no'])) if e['no'].isdigit() else (1, e['no']))
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
        for c in ott: ott[c] = [{'name': station_ko(p['name']) if p['name'] in STATION_KO_KEYS else p['name']} for p in ott[c]]
        if any(ott.values()): d['ott'] = ott; d['ott_updated'] = (tm or {}).get('ott_updated')
        if (jw or {}).get('box_office'): d['box_office'] = jw['box_office']
        if (mu or {}).get('albums'): d['albums'] = mu['albums']
        if ab:
            d['pilgrimage'] = {**ab, 'city': {'ko': place_ko(ab['city']), 'ja': ab['city']} if ab.get('city') else None,
                               'points': [{**p, 'name': {'ko': place_ko(p['name']), 'ja': p['name'], 'auto': 1}} for p in ab.get('points', [])]}
        d['sources'] = [n for n, x in zip(('AniList', 'しょぼいカレンダー', 'AnimeThemes', 'TMDB', '위키백과', 'MusicBrainz', 'Anitabi'), (al, sy, at, tm, jw, mu, ab)) if x]
        details[k] = d; made += 1

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
    ki, si, ei = c['fields'].index('ko'), c['fields'].index('st'), c['fields'].index('e'); n_ko = 0
    for r in c['rows']:
        w = BY[r[0]]
        if w.get('ko') and r[ki] != w['ko']: n_ko += 1 if not r[ki] else 0; r[ki] = w['ko']
        r[si], r[ei] = w.get('st'), w.get('e')
    for s in c['studios']:
        if s[3] in studios and not studios[s[3]]['name'].get('auto'): s[1], s[2] = studios[s[3]]['name']['ko'], False
    json.dump(c, open(cp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'작품 상세 {made}편, 인물 {len(people)}명, 제작사 {len(studios)}곳, 새로 채운 한국어 제목 {n_ko}편, 일본 외 제작 {len(nonjp)}편')

if __name__ == '__main__': main()
