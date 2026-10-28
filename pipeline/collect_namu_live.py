"""나무위키 실시간 (집 PC 전용): 실제 브라우저(Playwright의 Chromium)로 나무위키 작품 문서를 찾아, 문서 주소와 문서 제목(한국어 제목)을 모읍니다.
2022년 덤프에 없는 신작도 잡으려는 것입니다. 나무위키는 데이터센터 주소를 Cloudflare 확인 화면으로 막아서 집 인터넷에서만 돕니다.
확인 화면이 15초 안에 풀리지 않으면 그 실행은 멈춥니다(우회하지 않음).

찾는 순서 (작품마다)
 1. 사이트에 나온 한국어 제목이 있으면 「제목/애니메이션」 → 「제목」 문서
 2. 없거나 못 찾으면 나무위키 검색에 일본어 원제를 넣고 결과 위쪽 문서 몇 개
 문서 본문 앞부분에 작품의 일본어 원제가 그대로 있을 때만 그 문서로 정합니다.

준비: pip install playwright && python -m playwright install chromium
속도: 문서 하나 열 때마다 3~5초 쉼, 한 번에 최대 --limit 편(기본 150). 찾은 문서는 30일, 못 찾은 작품은 14일 동안 다시 열지 않습니다.
결과: raw/namu_live/<작품>.json = {url, title, ko, v}"""
import argparse, datetime, json, random, time, unicodedata, urllib.parse, urllib.request
from common import *

SITE_CATALOG = 'https://dabwanni.pages.dev/data/catalog.json'      # 배포된 목록 (병합 단계가 채운 한국어 제목이 들어 있음)
V = 2      # 2: 원제가 문서 앞부분(1,000자 안)에 있어야 하고, 한자 한 글자 문서(「描」)·관련 없는 문서를 거름. 1판 기록은 다시 확인
SEASON_KO = re.compile(r'\s*(\d+\s*기|\d+\s*쿨|\d+\s*부|시즌\s*\d+|파트\s*\d+|완결편)(\s*\d+\s*쿨)?\s*$')

def norm(t): return re.sub(r'[\s・･·「」『』〈〉《》()（）\[\]【】~〜\-－―!！?？、。,，.:：/／&＆]', '', unicodedata.normalize('NFKC', t or '')).lower()
def ja_base(t):
    t = unicodedata.normalize('NFKC', t or '')
    t = re.sub(r'[\(（](19|20)\d\d[\)）]', '', t)
    return re.sub(r'\s*(第\s*\d+\s*(期|クール|シーズン|部)|\d+(st|nd|rd|th)\s*Season|Season\s*\d+|\s[2-9])\s*$', '', t, flags=re.I).strip()

class Blocked2(Exception): pass

def main():
    ap = argparse.ArgumentParser(); budget_arg(ap)
    ap.add_argument('--limit', type=int, default=150)
    ap.add_argument('--headed', action='store_true', help='브라우저 창을 띄워서 (확인 화면이 자꾸 걸릴 때 시험용)')
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        r = Run('namu_live'); r.status, r.reason = 'skipped', 'playwright가 없음: pip install playwright && python -m playwright install chromium'; r.finish(); sys.exit(0)
    # 배포된 목록의 한국어 제목 (없으면 작품 목록 그대로)
    ko_of, base_ko = {}, {}
    try:
        req = urllib.request.Request(SITE_CATALOG, headers={'User-Agent': UA})
        c = json.load(urllib.request.urlopen(req, timeout=60)); F = c['fields']
        ki, kk = F.index('k'), F.index('ko')
        ko_of = {r[ki]: r[kk] for r in c['rows'] if r[kk]}
        jai = F.index('ja')
        for r in c['rows']:                                   # 같은 원제(시즌 표시 뺀)의 다른 작품 한국어 제목: 「ダンダダン 3」 → 「단다단」
            if r[kk] and r[jai]: base_ko.setdefault(norm(ja_base(r[jai])), SEASON_KO.sub('', r[kk]).strip())
    except Exception as e: print('배포된 목록을 못 받아 한국어 제목 없이 진행:', e)
    cy = datetime.date.today().year
    W = [w for w in load_catalog() if w.get('ja') and w.get('ty') in ('T', 'O', 'M', 'V') and (w.get('y') or 0) >= cy - 1]
    W.sort(key=lambda w: (-(w.get('y') or 0), -(w.get('q') or 0)))
    now = datetime.datetime.now(datetime.timezone.utc)
    def due(w):
        old = load('namu_live', w['k']); at = fetched_at('namu_live', w['k'])
        if not old or old.get('v') != V or not at: return True
        return (now - at).days >= (30 if old.get('url') else 14)
    todo = [w for w in W if due(w)][:a.limit]
    run = Run('namu_live', a.budget_min); run.say(f'대상 {len(todo)}편 (최근 작품 {len(W)}편 중)')
    if not todo: run.finish(); return
    found = 0
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not a.headed)
        ctx = b.new_context(locale='ko-KR')
        pg = ctx.new_page()
        def open_doc(title):
            url = 'https://namu.wiki/w/' + urllib.parse.quote(title)
            r = pg.goto(url, timeout=40000, wait_until='domcontentloaded')
            for _ in range(15):                                   # Cloudflare 확인 화면이면 풀릴 때까지 최대 15초
                if '보안 확인' not in (pg.title() + pg.inner_text('body')[:200]) and 'Just a moment' not in pg.title(): break
                time.sleep(1)
            else: raise Blocked2('Cloudflare 확인 화면이 풀리지 않음')
            time.sleep(random.uniform(3, 5))
            if r and r.status == 404 or '문서를 찾을 수 없습니다' in pg.inner_text('body')[:2000]: return None, None
            return pg.url, pg.inner_text('article') if pg.query_selector('article') else pg.inner_text('body')
        def search(q):
            url = 'https://namu.wiki/Search?q=' + urllib.parse.quote(q)
            pg.goto(url, timeout=40000, wait_until='domcontentloaded'); time.sleep(random.uniform(3, 5))
            hrefs = pg.eval_on_selector_all('a[href^="/w/"]', 'els => els.map(e => e.getAttribute("href"))')
            out = []
            for h in hrefs:
                t = urllib.parse.unquote(h[3:].split('#')[0])
                if t and t not in out and not t.startswith(('나무위키:', '틀:', '분류:', '파일:')): out.append(t)
            return out[:4]
        try:
            for w in todo:
                if not run.time_left(): run.status, run.reason = 'partial', '시간 예산 소진, 다음 실행에서 이어 받음'; break
                jb = norm(ja_base(w['ja']))
                cands = []
                ko = ko_of.get(w['k']) or base_ko.get(jb)
                if ko:
                    base = SEASON_KO.sub('', ko).strip()
                    cands += [f'{base}/애니메이션', base]
                rec = {'url': None, 'title': None, 'ko': None, 'v': V}
                tried = set()
                def check(title):
                    if title in tried: return False
                    tried.add(title)
                    u, text = open_doc(title)
                    t = urllib.parse.unquote(u.split('/w/', 1)[1].split('#')[0].split('?')[0]) if u else ''      # 넘겨주기 꼬리 「?from=…」 뗌
                    head = (t, t.split('/')[0])
                    if u and jb and jb in norm((text or '')[:1000]) and re.search(r'[가-힣]', head[1]) and head[1] not in w['ja'] and not re.search(r'\((드라마|소설|만화|게임|실사|영화|뮤지컬|라이트 노벨|웹툰|음반|노래|인물|성우|가수|배우)', head[1]) and '출생' not in (text or '')[:800]:   # 앞부분 1,000자 안에 원제, 한글 제목, 원제의 일부 글자 문서 아님
                        rec.update(url='https://namu.wiki/w/' + urllib.parse.quote(t), title=t, ko=t.split('/')[0]); return True
                    return False
                ok = any(check(t) for t in cands)
                if not ok:
                    for t in search(ja_base(w['ja'])):
                        if check(t): ok = True; break
                save('namu_live', w['k'], rec); found += bool(ok)
                run.c['ok' if ok else 'empty'] += 1
        except Blocked2 as e:
            run.fail_source(str(e))
        finally:
            b.close()
    run.say(f'문서를 찾은 작품 {found}편')
    run.finish()
    if run.status == 'failed': sys.exit(2)

if __name__ == '__main__': main()
