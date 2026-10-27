"""한국어 위키백과: 한국어 제목이 없는 최근 작품을 일본어 원제로 검색해, 문서 첫머리에 그 원제가 그대로 적힌 문서의 제목을 한국어 제목으로 씁니다.
공개 API(ko.wikipedia.org/w/api.php)를 씁니다. 찾은 것은 raw/kowiki/<작품>.json 에 저장하고, 못 찾은 작품은 30일 뒤 다시 찾습니다.
예: 「FX戦士くるみちゃん」 → 문서 「FX 전사 쿠루미」 (첫머리: 《FX 전사 쿠루미》(일본어: FX戦士くるみちゃん …))"""
import argparse, datetime, unicodedata
from common import *

API = 'https://ko.wikipedia.org/w/api.php'
ANIME_WORDS = re.compile(r'(애니메이션|만화|라이트 노벨|소설)')
V = 2      # 기록 형식 판: 2부터는 첫머리 「일본어: 원제」가 원제와 똑같을 때만 씀 (1판은 원제가 일부만 들어 있어도 써서 「ブレス」에 「젤다의 전설 브레스 오브 더 와일드」가 붙었음)

def original_title(head):
    """문서 첫머리의 「(일본어: 원제 …」에서 원제만 꺼냄. 원제 뒤의 한글 읽기·쉼표·괄호 앞까지"""
    m = re.search(r'일본어\s*:\s*([^,，)\]]+)', head)
    if not m: return None
    t = re.split(r'[\uac00-\ud7a3]', m.group(1))[0]
    return t.strip()

def norm(t): return re.sub(r'[\s・･·「」『』()（）\[\]【】~〜\-－―!！?？、。,，.:：/／]', '', unicodedata.normalize('NFKC', t or '')).lower()

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(0.5)
    def api(**q):
        q.update(format='json', formatversion='2')
        d = http.json(API + '?' + urllib.parse.urlencode(q))
        if not isinstance(d, dict) or 'query' not in d and 'error' not in d: raise SchemaError('위키백과 응답 형식이 바뀜')
        return d.get('query') or {}
    cy = datetime.date.today().year
    from build_details import tmdb_title_ok
    def has_ko(w):
        if w.get('ko'): return True
        return bool(tmdb_title_ok(w, load('tmdb', w['k'])))     # TMDB 시리즈 이름만 붙은 작품(이야기 시리즈 등)도 찾아봄
    W = [w for w in load_catalog() if w.get('ja') and w.get('ty') in ('T', 'O', 'M', 'V') and ((w.get('y') or 0) >= cy - 3 or int(w.get('tms') or 0) >= 2)]
    W.sort(key=lambda w: (-(w.get('y') or 0), -(w.get('q') or 0)))
    def work(w, run):
        http.run = run
        old = load('kowiki', w['k']); at = fetched_at('kowiki', w['k'])
        if old and old.get('v') == V and old.get('title'): return SKIP
        if old and old.get('v') == V and at and (datetime.datetime.now(datetime.timezone.utc) - at).days < 30: return SKIP
        if has_ko(w): return SKIP
        ja = unicodedata.normalize('NFKC', w['ja'])
        hits = [h['title'] for h in (api(action='query', list='search', srsearch=f'"{ja}"', srnamespace=0, srlimit=4).get('search') or [])]
        if not hits:
            # 속편·구분 표기를 뗀 원제로도 찾음 (「ねずみくんのチョッキ (TV) 第2期」 → 「ねずみくんのチョッキ」)
            base = re.sub(r'\s*(\((TV|2\d{3})\)|第\s*\d+\s*(期|クール|シーズン)|\d+(st|nd|rd|th)\s*Season|Season\s*\d+|\s[2-9])\s*', ' ', ja).strip()
            if base and base != ja:
                ja = base
                hits = [h['title'] for h in (api(action='query', list='search', srsearch=f'"{ja}"', srnamespace=0, srlimit=4).get('search') or [])]
        title = None
        if hits:
            pages = api(action='query', prop='extracts', exintro=1, explaintext=1, titles='|'.join(hits)).get('pages') or []
            ex = {p['title']: p.get('extract') or '' for p in pages}
            for h in hits:
                head = ex.get(h, '')[:400]
                # 첫머리 「일본어: 원제」가 찾는 원제와 똑같고, 애니메이션·만화·소설 문서일 때만
                if norm(ja) and norm(original_title(head) or '') == norm(ja) and ANIME_WORDS.search(head):
                    title = re.sub(r'\s*\((애니메이션|만화|소설|라이트 노벨|텔레비전 애니메이션|[0-9]{4}년 애니메이션)\)\s*$', '', h).strip(); break
        save('kowiki', w['k'], {'title': title, 'query': ja, 'v': V}); return {'title': title} if title else []
    run_source('kowiki', W, work, canary=(lambda: bool(api(action='query', list='search', srsearch='"薬屋のひとりごと"', srlimit=1).get('search')), '약사의 혼잣말 검색'),
               budget_min=a.budget_min, max_empty=None)
