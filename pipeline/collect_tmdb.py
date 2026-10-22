"""TMDB: 한국어·영어 제목, 회차 제목(한·일·영)·길이(2배 분량 판별), 한국·일본·미국 OTT.
TMDB_API_KEY 환경 변수 필요. OTT는 7일마다, 방영 중 작품은 3일마다 다시 받습니다."""
import os, sys, argparse, statistics, datetime
from common import *

KEY = os.environ.get('TMDB_API_KEY'); B = 'https://api.themoviedb.org/3'

if __name__ == '__main__':
    if not KEY:
        r = Run('tmdb'); r.status, r.reason = 'skipped', 'TMDB_API_KEY가 설정되지 않음'; r.finish(); sys.exit(0)
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(0.3)
    def get(path, **q):
        q['api_key'] = KEY
        return http.json(B + path + '?' + urllib.parse.urlencode(q))
    W = sorted((w for w in load_catalog() if w.get('tmdb')), key=lambda w: w['tmdb'])
    cache = {}
    def show(tv):
        if tv not in cache:
            cache.clear(); cache[tv] = get(f'/tv/{tv}', language='ko-KR', append_to_response='watch/providers,translations')
            if cache[tv] and 'name' not in cache[tv]: raise SchemaError('TMDB 응답 형식이 바뀜')
        return cache[tv]
    def work(w, run):
        http.run = run
        if not needs('tmdb', w, fresh_days=7, airing_days=3): return SKIP
        ko = show(w['tmdb'])
        prov = (ko.get('watch/providers') or {}).get('results', {})
        rec = {'tv': w['tmdb'], 'ott': {c: [{'name': p['provider_name']} for p in (prov.get(c) or {}).get('flatrate', [])] for c in ('KR', 'JP', 'US')},
               'ott_updated': datetime.date.today().isoformat()}
        tr = {t['iso_639_1']: (t.get('data') or {}).get('name') for t in (ko.get('translations') or {}).get('translations', [])}
        rec['titles'] = {'ko': tr.get('ko') or None, 'en': tr.get('en') or None, 'ja': tr.get('ja') or ko.get('original_name')}
        s = w.get('tms')
        if s is not None and w['ty'] in ('T', 'O'):
            eps = {}
            for lang in ('ko-KR', 'ja-JP', 'en-US'):
                try: d = get(f'/tv/{w["tmdb"]}/season/{s}', language=lang) or {}
                except NotFound: d = {}
                for e in d.get('episodes', []):
                    x = eps.setdefault(e['episode_number'], {'no': str(e['episode_number']), 'title': {}, 'air': e.get('air_date'), 'min': e.get('runtime')})
                    if e.get('name') and not re.match(r'^(에피소드|Episode|第)\s*\d', e['name']): x['title'][lang[:2]] = e['name']
            L = [eps[k] for k in sorted(eps)]
            rts = [e['min'] for e in L if e['min']]
            if len(rts) >= 3:
                med = statistics.median(rts)
                for e in L:
                    if e['min'] and e['min'] >= med * 1.7: e['special'] = True
            rec['episodes'] = L
        save('tmdb', w['k'], rec); return rec
    run_source('tmdb', W, work, canary=(lambda: show(30991).get('name'), '카우보이 비밥 (TV 30991)'), budget_min=a.budget_min)
