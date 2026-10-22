"""부가 정보: MusicBrainz(사운드트랙·캐릭터 송 음반, 음원 스트리밍 링크), Anitabi(성지순례 장소).
사용:  python3 collect_extra.py music   /   python3 collect_extra.py pilgrimage"""
import sys, re
from common import *

MB = 'https://musicbrainz.org/ws/2/'

def music(http, w):
    t = w.get('ja') or w['r']
    out = []
    for kind, q in (('OST', f'releasegroup:"{t}" AND secondarytype:soundtrack'),
                    ('캐릭터 송', f'releasegroup:"{t}" AND (キャラクターソング OR "character song" OR キャラソン)')):
        d = http.json(MB + 'release-group?fmt=json&limit=25&query=' + urllib.parse.quote(q)) or {}
        for rg in d.get('release-groups', []):
            if rg.get('score', 0) < 85: continue
            yr = (rg.get('first-release-date') or '')[:4]
            if w.get('y') and yr.isdigit() and abs(int(yr) - w['y']) > 3: continue
            links = []
            det = http.json(MB + f"release-group/{rg['id']}?fmt=json&inc=url-rels") or {}
            for r in det.get('relations', []):
                u = (r.get('url') or {}).get('resource', '')
                for site in ('spotify', 'apple', 'youtube', 'amazon', 'line', 'melon'):
                    if site in u: links.append({'site': site, 'url': u})
            out.append({'kind': kind, 'title': rg['title'], 'date': rg.get('first-release-date'),
                        'artists': [a.get('name') for a in rg.get('artist-credit', []) if isinstance(a, dict)], 'links': links})
    return out

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('what', choices=['music', 'pilgrimage']); budget_arg(ap); a = ap.parse_args()
    W = load_catalog()
    if a.what == 'music':
        http = Http(1.1)
        W = [w for w in W if w['ty'] in ('T', 'O', 'M') and (w.get('ja') or w['r'])]
        def work(w, run):
            http.run = run
            if not needs('music', w, fresh_days=180, airing_days=30): return SKIP
            r = {'albums': music(http, w)}; save('music', w['k'], r); return r
        def canary():
            d = http.json(MB + 'release-group?fmt=json&limit=1&query=' + urllib.parse.quote('cowboy bebop'))
            return 'release-groups' in (d or {})
        run_source('music', W, work, canary=(canary, 'MusicBrainz 검색'), budget_min=a.budget_min, max_empty=None)
    else:
        http = Http(0.5)
        W = [w for w in W if w.get('bgm')]
        def lite(b):
            d = http.json(f"https://api.anitabi.cn/bangumi/{b}/lite")
            if d is not None and 'id' not in d: raise SchemaError('Anitabi 응답 형식이 바뀜')
            return d
        def work(w, run):
            http.run = run
            if not needs('anitabi', w, fresh_days=90, airing_days=30): return SKIP
            try: d = lite(w['bgm'])
            except NotFound: d = None
            r = {'city': d.get('city'), 'count': d.get('pointsLength'), 'map': f"https://anitabi.cn/map?bangumiId={w['bgm']}",
                 'points': [{'name': p.get('name'), 'ep': p.get('ep'), 'image': p.get('image'), 'geo': p.get('geo')} for p in d.get('litePoints', [])]} if d and d.get('pointsLength') else {}
            save('anitabi', w['k'], r); return r
        run_source('anitabi', W, work, canary=(lambda: (lite(115908) or {}).get('pointsLength'), '울려라! 유포니엄'), budget_min=a.budget_min, max_empty=None)
