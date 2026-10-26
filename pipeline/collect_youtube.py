"""공식 유튜브 영상: 작품 상세에 PV·오프닝·엔딩을 넣으려고, 공식 채널이 올린 유튜브 영상만 찾아 둡니다.
오프닝·엔딩 검색에 YOUTUBE_API_KEY(YouTube Data API v3)가 필요합니다. 하루 무료 한도(10,000 단위)를 넘지 않게 하루 검색 수를 정해 둡니다.

- PV: 여기서 찾지 않음. AniList에 등록된 예고편(유튜브)은 공식으로 보고 병합 단계에서 그대로 씀
- 오프닝·엔딩: 「(일본어 제목) ノンクレジット」로 검색해(100단위), 공식 채널이 올린 영상 중 제목에 OP·ED 표시가 있는 것만 씀
- 공식 채널 판단: 애니메이션 제작·배급사 공식 채널 이름(아래 OFFICIAL)이거나, 채널 이름에 「公式·official」과 작품 제목이 함께 있을 때
찾은 결과는 raw/youtube/<작품>.json 에 저장하고, 못 찾은 작품은 60일 뒤에 다시 찾습니다. 최근 작품부터 차례로 채웁니다."""
import os, sys, re, argparse, datetime, unicodedata
from common import *

KEY = os.environ.get('YOUTUBE_API_KEY'); B = 'https://www.googleapis.com/youtube/v3'
PER_DAY = int(os.environ.get('YOUTUBE_PER_DAY', '80'))     # 검색 80회 × 100단위 = 8,000 (영상 정보 조회 여유분 남김)

# 일본 애니메이션 제작·배급·음반사 공식 채널 이름에 들어가는 말
OFFICIAL = re.compile(r'(アニプレックス|Aniplex|KADOKAWA|カドカワ|TOHO animation|東宝|ポニーキャニオン|PONY ?CANYON|avex|エイベックス|バンダイナムコ|Bandai ?Namco|'
                      r'東映アニメーション|Toei Animation|MAPPA|ufotable|京都アニメーション|Kyoto Animation|キングレコード|KING ?RECORDS|フライングドッグ|FlyingDog|'
                      r'ランティス|Lantis|ソニー・?ミュージック|Sony Music|日本コロムビア|Columbia|NBC ?ユニバーサル|NBCUniversal|ワーナー|Warner Bros\.? Japan|'
                      r'ムービック|movic|DMM pictures|アニメイト|animate|バップ|VAP|EMOTION|エモーション|ジェンコ|GENCO|日本アニメーション|サンライズ|SUNRISE|'
                      r'A-1 Pictures|CloverWorks|WIT STUDIO|P\.A\.WORKS|トムス|TMS|プロダクション・?アイジー|Production I\.G|ProductionIG|Crunchyroll|アニメ公式)', re.I)

def official(channel, w):
    if not channel: return False
    if OFFICIAL.search(channel): return True
    if re.search(r'(公式|official|オフィシャル)', channel, re.I):
        t = unicodedata.normalize('NFKC', w.get('ja') or '')
        head = re.sub(r'[\s　・:：~〜!！?？].*$', '', t)[:6]
        return bool(head) and head in unicodedata.normalize('NFKC', channel)
    return False

def kind_of(title):
    t = unicodedata.normalize('NFKC', title or '')
    if re.search(r'(ノンクレジット|クレジットなし|creditless|non-?credit)', t, re.I):
        if re.search(r'(OP|オープニング|opening)', t, re.I): return 'op'
        if re.search(r'(ED|エンディング|ending)', t, re.I): return 'ed'
    return None

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    if not KEY:
        r = Run('youtube'); r.status, r.reason = 'skipped', 'YOUTUBE_API_KEY가 설정되지 않음 (PV는 키 없이 AniList 예고편으로 나옴)'; r.finish(); sys.exit(0)
    http = Http(0.2)
    def get(path, **q):
        q['key'] = KEY
        d = http.json(B + path + '?' + urllib.parse.urlencode(q))
        if d and d.get('error'): raise SchemaError('YouTube 오류: ' + str(d['error'].get('message'))[:200])
        return d or {}
    cy = datetime.date.today().year
    W = [w for w in load_catalog() if w.get('ja') and w.get('ty') in ('T', 'O', 'M') and (w.get('y') or 0) >= cy - 3]
    W.sort(key=lambda w: (-(w.get('y') or 0), -(w.get('q') or 0)))          # 최근 작품부터
    used = [0]
    def work(w, run):
        http.run = run
        old = load('youtube', w['k']) or {}
        at = fetched_at('youtube', w['k'])
        age = (datetime.datetime.now(datetime.timezone.utc) - at).days if at else None
        if old.get('op') or old.get('ed') or (age is not None and age < 60): return SKIP   # 찾은 것은 그대로, 못 찾은 것은 60일 뒤 다시
        if used[0] >= PER_DAY: return SKIP                                                  # 오늘 검색 한도
        rec = {'op': [], 'ed': []}
        used[0] += 1
        s = get('/search', part='snippet', type='video', maxResults=15, q=f'{w["ja"]} ノンクレジット')
        for it in s.get('items') or []:
            sn = it.get('snippet') or {}; vid = (it.get('id') or {}).get('videoId')
            k = kind_of(sn.get('title'))
            # 영상 제목에 이 작품 제목 앞부분이 있어야 함 (같은 채널의 다른 작품 영상 배제)
            head = re.sub(r'\s', '', unicodedata.normalize('NFKC', w['ja']))[:4]
            if vid and k and official(sn.get('channelTitle'), w) and head in re.sub(r'\s', '', unicodedata.normalize('NFKC', sn.get('title') or '')):
                if vid not in rec[k] and len(rec[k]) < 3: rec[k].append(vid)
        save('youtube', w['k'], rec); return rec if (rec['op'] or rec['ed']) else []
    run_source('youtube', W, work, canary=(lambda: 'items' in get('/videos', part='snippet', id='dQw4w9WgXcQ'), '영상 정보 조회'),
               budget_min=a.budget_min, max_empty=None)
