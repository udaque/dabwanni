"""AniList: 캐릭터(엑스트라 포함)·일한영 성우, 스태프(회차별 표기 포함), 제작사(원청·참여사), 원작 종류, 장르·태그,
평점·인기, 연령 등급, PV, 공식 링크, 시리즈 관계."""
import argparse
from common import *

NAME = 'name{first last full native alternative}'
Q = '''query($id:Int,$page:Int){Media(id:$id,type:ANIME){id countryOfOrigin source isAdult averageScore meanScore popularity favourites
 title{native english romaji} genres tags{name rank isMediaSpoiler}
 trailer{id site} externalLinks{site url type language}
 studios{edges{isMain node{id name isAnimationStudio}}}
 relations{edges{relationType node{id type}}}
 characters(page:$page,perPage:25,sort:[ROLE,RELEVANCE,ID]){pageInfo{hasNextPage}
  edges{role node{id %s image{medium}}
   ja:voiceActors(language:JAPANESE){id %s}
   ko:voiceActors(language:KOREAN){id %s}
   en:voiceActors(language:ENGLISH){id %s}}}
 staff(page:$page,perPage:25,sort:[RELEVANCE,ID]){pageInfo{hasNextPage} edges{role node{id %s}}}}}''' % ((NAME,) * 5)
URL = 'https://graphql.anilist.co'

def query(http, al, page):
    d = http.json(URL, {'query': Q, 'variables': {'id': int(al), 'page': page}}, {'Accept': 'application/json'})
    errs = [e for e in (d or {}).get('errors') or [] if e.get('status') != 404]
    if errs: raise SchemaError('AniList 오류: ' + '; '.join(e.get('message', '') for e in errs)[:200])
    m = ((d or {}).get('data') or {}).get('Media')
    if m is not None and not ('title' in m and 'characters' in m and 'staff' in m): raise SchemaError('AniList 응답 형식이 바뀜')
    return m

def fetch(http, al):
    out, page = None, 1
    while True:
        try: m = query(http, al, page)
        except NotFound: return out
        if not m: return out
        if out is None: out = m
        else:
            out['characters']['edges'] += m['characters']['edges']; out['staff']['edges'] += m['staff']['edges']
        if not (m['characters']['pageInfo']['hasNextPage'] or m['staff']['pageInfo']['hasNextPage']): return out
        page += 1

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--interval', type=float, default=2.1); budget_arg(ap); a = ap.parse_args()
    http = Http(a.interval)
    W = sorted((w for w in load_catalog() if w['al']), key=lambda w: -(w['y'] or 0))
    def work(w, run):
        http.run = run
        if not needs('anilist', w): return SKIP
        r = fetch(http, w['al']) or {}; save('anilist', w['k'], r); return r
    def canary():
        m = query(http, 1, 1); return bool(m and m['title'].get('native'))
    run_source('anilist', W, work,
               canary=(canary, 'AniList 1번 작품(카우보이 비밥)'), budget_min=a.budget_min)
