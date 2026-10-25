"""라프텔: 분기별 작품 목록을 받아, 병합 단계에서 다봤니 작품과 짝지어 한국 OTT에 「라프텔」을 붙입니다.
라프텔 웹사이트가 쓰는 비공식 API(laftel.net/api/search/v1/discover)를 씁니다. 공식 공개 API가 아니므로 구조가 바뀌면
시험 요청에서 실패로 잡힙니다. 지난 분기는 한 번 받으면 90일마다, 최근 1년 분기는 3일마다 다시 받습니다."""
import argparse, datetime
from common import *

API = 'https://laftel.net/api/search/v1/discover/?sorting=latest&years='
HEAD = {'laftel': 'TeJava', 'Accept': 'application/json'}   # 라프텔 API가 요구하는 머리글 (알려진 사용 예와 같은 값)

def quarter_label(y, q): return f'{y}년 {q}분기'

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); ap.add_argument('--from-year', type=int, default=1960); a = ap.parse_args()
    http = Http(1.0)
    def page(url):
        d = http.json(url, headers=HEAD)
        if not isinstance(d, dict) or 'results' not in d: raise SchemaError('라프텔 응답 형식이 바뀜 (results 없음)')
        return d
    now = datetime.date.today(); cy, cq = now.year, (now.month - 1) // 3 + 1
    items = []
    for y in range(cy + 1, a.from_year - 1, -1):                    # 최근 분기부터
        for q in range(4, 0, -1):
            if (y, q) > (cy + (cq == 4), (cq % 4) + 1): continue        # 다음 분기까지만
            items.append({'k': f'{y}-{q}', 'y': y, 'q': q})
    def work(x, run):
        http.run = run
        age = fetched_at('laftel', x['k'])
        recent = (cy * 4 + cq) - (x['y'] * 4 + x['q']) <= 4
        if age and (now - age.date()).days < (3 if recent else 90): return SKIP
        url = API + urllib.parse.quote(quarter_label(x['y'], x['q'])); res = []
        while url:
            d = page(url)
            for r in d['results']:
                # 필드 이름은 라프텔 요일별 신작 응답에서 확인된 것들 (is_dubbed: 더빙판, is_uncensored: 무삭제판, is_expired: 판권 만료)
                res.append({k: r.get(k) for k in ('id', 'name', 'img', 'medium', 'genres', 'is_dubbed', 'is_uncensored', 'is_laftel_only',
                                                  'is_avod', 'is_viewing', 'is_expired', 'is_adult') if k in r})
            url = d.get('next')
        save('laftel', x['k'], {'quarter': quarter_label(x['y'], x['q']), 'items': res}); return res
    run_source('laftel', items, work, canary=(lambda: page(API + urllib.parse.quote(quarter_label(cy - 1, 4)))['count'] > 0, '작년 4분기 목록'),
               budget_min=a.budget_min, max_empty=None)
