"""AnimeThemes: 오프닝·엔딩(일부 삽입곡) 곡명, 가수, 사용 회차. 쇼보이 캘린더에 없는 옛 작품·OVA 보완.
목록 전체를 쪽 단위로 훑으며, 쪽 번호를 저장해 다음 실행에서 이어 받습니다."""
import argparse
from common import *

BASE = 'https://api.animethemes.moe/anime?page[size]=25&include=resources,animethemes.song.artists,animethemes.animethemeentries&page[number]='

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); ap.add_argument('--restart', action='store_true'); a = ap.parse_args()
    http = Http(0.8)
    by = {}
    for w in load_catalog():
        if w['mal']: by[('MyAnimeList', str(w['mal']))] = w['k']
        if w['al']: by[('AniList', str(w['al']))] = w['k']
    state = (load('animethemes', '_state') or {}) if not a.restart else {}
    start = state.get('page', 1)
    def page(n):
        d = http.json(BASE + str(n))
        if not isinstance(d, dict) or 'anime' not in d: raise SchemaError('AnimeThemes 응답 형식이 바뀜')
        return d
    pages = iter(range(start, 100000))
    done = {'end': False}
    def gen():
        for n in pages:
            if done['end']: return
            yield {'k': f'쪽{n}', 'n': n}
    def work(x, run):
        http.run = run; d = page(x['n']); got = 0
        for a_ in d['anime']:
            k = next((by.get((r['site'], str(r.get('external_id')))) for r in a_.get('resources', []) if by.get((r['site'], str(r.get('external_id'))))), None)
            if not k: continue
            songs = []
            for t in a_.get('animethemes', []):
                s = t.get('song') or {}
                eps = ', '.join(e['episodes'] for e in t.get('animethemeentries', []) if e.get('episodes'))
                songs.append({'kind': t.get('type'), 'seq': t.get('sequence'), 'title': s.get('title') or '', 'eps': eps or None,
                              'credits': [{'role': '歌', 'name': y['name']} for y in s.get('artists', [])]})
            save('animethemes', k, {'id': a_['id'], 'songs': songs}); got += 1
        save('animethemes', '_state', {'page': x['n'] + 1})
        if not (d.get('links') or {}).get('next'):
            done['end'] = True; save('animethemes', '_state', {'page': 1})   # 끝까지 돌면 다음엔 처음부터 (새 곡 반영)
        return d['anime']
    run_source('animethemes', gen(), work, canary=(lambda: 'anime' in http.json('https://api.animethemes.moe/anime?page[size]=1'), '작품 1개 조회'), budget_min=a.budget_min, max_empty=0.95)
