"""AniList 인물 프로필: 생년월일, 출신지, 활동 분야, 사진, 활동 연도. collect_anilist.py 뒤에 실행."""
import glob, argparse
from common import *

Q = '''query($ids:[Int]){Page(perPage:50){staff(id_in:$ids){id name{first last full native alternative}
 dateOfBirth{year month day} homeTown primaryOccupations yearsActive image{medium} gender}}}'''

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(2.1); ids = set()
    for f in glob.glob(os.path.join(RAW, 'anilist', '*.json')):
        d = json.load(open(f, encoding='utf-8')) or {}
        for e in (d.get('characters') or {}).get('edges', []):
            for l in ('ja', 'ko', 'en'):
                for v in e.get(l) or []: ids.add(v['id'])
        for e in (d.get('staff') or {}).get('edges', []): ids.add(e['node']['id'])
    todo = sorted(i for i in ids if not have('anilist_people', str(i)))
    chunks = [todo[n:n + 50] for n in range(0, len(todo), 50)]
    def page(chunk):
        d = http.json('https://graphql.anilist.co', {'query': Q, 'variables': {'ids': chunk}}, {'Accept': 'application/json'})
        if (d or {}).get('errors'): raise SchemaError(str(d['errors'])[:200])
        return {s['id']: s for s in ((d or {}).get('data') or {}).get('Page', {}).get('staff', [])}
    def work(chunk, run):
        http.run = run; got = page(chunk)
        for i in chunk: save('anilist_people', str(i), got.get(i, {}))
        return got
    run_source('anilist_people', [{'k': f'묶음{n}', 'c': c} for n, c in enumerate(chunks)], lambda x, run: work(x['c'], run),
               canary=(lambda: 95 in page([95]) or True, 'AniList 인물 조회'), budget_min=a.budget_min)
