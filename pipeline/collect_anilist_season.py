"""AniList 분기별 작품 목록: 작품 목록 원천(manami)이 2026년 7월 판에서 멈춰 있어, 그 뒤 발표된 작품과 바뀐 방영 시기·상태·화수를 보충합니다.
작년 1분기부터 내년 4분기까지 분기마다 AniList의 작품 목록을 받아 raw/anilist_season/<연도>-<분기>.json 에 저장하고,
build_catalog.py가 이를 manami 항목처럼 바꿔 합칩니다. 작품 목록 단계(catalog)에서 build_catalog.py 바로 앞에 돕니다."""
import argparse, datetime
from common import *

URL = 'https://graphql.anilist.co'
Q = '''query($s:MediaSeason,$y:Int,$p:Int){Page(page:$p,perPage:50){pageInfo{hasNextPage}
 media(season:$s,seasonYear:$y,type:ANIME,sort:ID){id idMal title{romaji english native} synonyms format episodes duration status season seasonYear
 startDate{year month day} coverImage{large} countryOfOrigin isAdult genres studios(isMain:true){nodes{name}} relations{edges{relationType node{id type}}}}}}'''
SEASONS = ['WINTER', 'SPRING', 'SUMMER', 'FALL']

def page(http, s, y, p):
    d = http.json(URL, {'query': Q, 'variables': {'s': s, 'y': y, 'p': p}}, {'Accept': 'application/json'})
    if (d or {}).get('errors'): raise SchemaError('AniList 오류: ' + '; '.join(e.get('message', '') for e in d['errors'])[:200])
    pg = ((d or {}).get('data') or {}).get('Page')
    if not pg or 'media' not in pg: raise SchemaError('AniList 분기 목록 응답 형식이 바뀜')
    return pg

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(2.0)                               # AniList 분당 요청 제한 대비
    cy = datetime.date.today().year
    items = [{'k': f'{y}-{q}', 'y': y, 'q': q} for y in range(cy - 1, cy + 2) for q in (1, 2, 3, 4)]
    def work(x, run):
        http.run = run; out, p = [], 1
        while True:
            pg = page(http, SEASONS[x['q'] - 1], x['y'], p)
            out += pg['media']
            if not (pg.get('pageInfo') or {}).get('hasNextPage') or p >= 20: break
            p += 1
        save('anilist_season', x['k'], {'media': out}); return out
    run_source('anilist_season', items, work, canary=(lambda: len(page(http, 'FALL', cy - 1, 1)['media']) > 0, '작년 가을 목록'),
               budget_min=a.budget_min, max_empty=None)
