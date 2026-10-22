"""나무위키 덤프에서 한국어 이름 찾기: 작품 제목, 캐릭터·성우·스태프·가수·제작사 이름, 한국 방영·더빙 정보.
나무위키 덤프(JSON 또는 Parquet, 열: title, text)를 직접 내려받아 경로를 지정하세요. 예:
  python3 collect_namu.py ~/namuwiki.parquet
문서 앞부분의 괄호 속 일본어 표기(例: 種﨑敦美)를 그 문서 제목(한국어)과 연결한 색인을 만듭니다."""
import sys, re, json, os
from common import *

JA = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
PAREN = re.compile(r'[（(]([^()（）\n]{1,60})[)）]')
FIELD = re.compile(r'\|\|\s*(?:원제|원어 명칭|본명|이름|일본어)\s*\|\|\s*([^|\n]{1,80})')
KR_SEC = re.compile(r'^=+\s*(?:한국|국내)[^=\n]*(?:방영|방송|정발|더빙|수입)[^=\n]*=+\s*$(.*?)(?=^=+ )', re.M | re.S)

def plain(t):
    t = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[[^\]]*\]', '', t); t = re.sub(r"'''|''|~~|--|\{\{\{[^ ]*\s?|\}\}\}", '', t)
    t = re.sub(r'\|\|', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def rows(path):
    if path.endswith('.parquet'):
        import pyarrow.parquet as pq
        for b in pq.ParquetFile(path).iter_batches(columns=['title', 'text'], batch_size=2000):
            for t, x in zip(b.column('title').to_pylist(), b.column('text').to_pylist()): yield t, x or ''
    else:
        with open(path, encoding='utf-8') as f:
            first = f.read(1); f.seek(0)
            if first == '[':
                for d in json.load(f): yield d.get('title'), d.get('text') or ''
            else:
                for line in f:
                    d = json.loads(line); yield d.get('title'), d.get('text') or ''

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('NAMU_DUMP')
    run = Run('namu', min_n=1)
    if not path or not os.path.exists(path):
        run.say('나무위키 덤프 파일이 없어 건너뜁니다 (NAMU_DUMP 또는 인자로 경로 지정).'); run.status = 'skipped'; run.reason = '덤프 파일 없음'; run.finish(); sys.exit(0)
    index, kr = {}, {}
    try:
        for n, (title, text) in enumerate(rows(path)):
            if n % 100000 == 0: run.say(f'문서 {n}')
            if not title or text.startswith('#redirect') or text.startswith('#넘겨주기'): continue
            head = text[:2500]; cands = set()
            for m in PAREN.finditer(head):
                for part in re.split(r'[/,、;·]', m.group(1)):
                    part = part.strip()
                    if JA.search(part) and not re.search(r'[\uac00-\ud7a3]', part): cands.add(part)
            for m in FIELD.finditer(head):
                v = plain(m.group(1))
                if JA.search(v): cands.add(v)
            for c in cands:
                L = index.setdefault(pname(c), [])
                if title not in L and len(L) < 8: L.append(title)
            m = KR_SEC.search(text)
            if m: kr[title] = plain(m.group(1))[:600]
        if len(index) < 50000: raise SchemaError(f'색인이 {len(index)}개뿐: 덤프 형식이 다를 가능성 (열 이름 title, text 필요)')
        save('namu', 'index', index); save('namu', 'korea', kr)
        run.c['ok'] = len(index); run.say(f'색인 {len(index)}, 한국 방영 문단 {len(kr)}')
    except Exception as e:
        run._record_fail('덤프', e); run.fail_source(f'{type(e).__name__}: {e}')
    s = run.finish()
    sys.exit(2 if s['status'] == 'failed' else 0)
