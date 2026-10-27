"""썸네일 그림 지문: 작품 목록의 썸네일을 받아 작게 줄인 그림 지문(64비트 dHash)을 만들어 둡니다.
작품 목록 단계가 「그림이 거의 같고 같은 해·같은 형식인 보조 항목」을 중복으로 합칠 때 씁니다(같은 포스터를 쓰는
시리즈 작품이 많아 그림만으로는 합치지 않음). 지문은 그림 주소별로 raw/thumbhash/<묶음>.json 에 저장하고, 한 번 만든 것은 다시 받지 않습니다."""
import argparse, io, hashlib, concurrent.futures as cf
from common import *

def url(p):
    if not p: return None
    if p[0] == 'M': return 'https://cdn.myanimelist.net/images/anime/' + p[1:].replace('.jpg', 't.jpg')
    if p[0] == 'A': return p[1:]
    return p if p.startswith('https://') else None

def _pil():
    try:
        from PIL import Image; return Image
    except ImportError:          # 실행 서버에 없으면 한 번 설치 (설정 파일을 고치지 않고 쓰려고)
        import subprocess; subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'pillow'], check=False)
        from PIL import Image; return Image

def dhash(data):
    Image = _pil()
    im = Image.open(io.BytesIO(data)).convert('L')
    im = im.crop((0, 0, im.width, int(im.height * 0.8))).resize((9, 8))      # 아래쪽 글자·로고는 판마다 달라 위 80%만
    px = list(im.tobytes())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])

def bucket(p): return hashlib.sha1(p.encode()).hexdigest()[:2]

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(0.0)
    W = [w for w in load_catalog() if w.get('p') and url(w['p'])]
    groups = {}
    for w in W: groups.setdefault(bucket(w['p']), set()).add(w['p'])
    items = [{'k': b, 'ps': sorted(ps)} for b, ps in sorted(groups.items())]
    def work(x, run):
        http.run = run
        old = load('thumbhash', x['k']) or {}
        todo = [p for p in x['ps'] if p not in old]
        if not todo: return SKIP
        def one(p):
            try:
                req = urllib.request.Request(url(p), headers={'User-Agent': UA})
                return p, dhash(urllib.request.urlopen(req, timeout=20).read())
            except Exception: return p, None
        with cf.ThreadPoolExecutor(16) as ex:
            for p, h in ex.map(one, todo[:600]): old[p] = h          # 한 묶음에 한 번 600장까지 (나머지는 다음 실행)
        save('thumbhash', x['k'], {k: v for k, v in old.items() if not k.startswith('_')})
        return [1]
    run_source('thumbhash', items, work, budget_min=a.budget_min, max_empty=None)
