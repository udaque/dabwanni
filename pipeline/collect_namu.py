"""나무위키 덤프에서 한국어 이름 찾기: 작품 제목, 캐릭터·성우·스태프·가수·제작사 이름, 한국 방영·더빙 정보.
나무위키 덤프(JSON 또는 Parquet, 열: title, text)를 직접 내려받아 경로를 지정하세요. 예:
  python3 collect_namu.py ~/namuwiki.parquet
문서 앞부분의 괄호 속 일본어 표기(例: 種﨑敦美)를 그 문서 제목(한국어)과 연결한 색인을 만듭니다."""
import sys, re, json, os, glob
from common import *

JA = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
# 문서 주제의 원어 이름만: 첫머리의 굵은 제목 바로 뒤 괄호 (예: '''유키 아오이'''(悠木碧, ...))
# 예전엔 앞부분의 괄호를 모두 넣어서, 작품 문서에 나오는 제작진 이름까지 그 작품 문서와 이어졌음 (荻野美希 → 「5등분의 신부」)
PAREN = re.compile(r"'''[^'\n]{1,80}'''\s*[（(]([^()（）\n]{1,60})[)）]")
ANY_PAREN = re.compile(r'[（(]([^()（）\n]{1,60})[)）]')     # 작품 제목용 넓은 색인: 앞부분의 괄호 모두 (예전 방식)
def lead_names(head):
    """문서 첫머리의 굵은 제목 바로 뒤 괄호 안 원어 이름들. 괄호 안의 읽기 괄호(「悠木(ゆうき) 碧(あおい)」)와
    「일본어: 」 같은 한국어 머리말, 위키 문법을 걷어 냄. 예전엔 괄호가 겹치면 통째로 놓쳐서 색인이 크게 줄었음."""
    out = []
    for m in list(re.finditer(r"'''[^'\n]{1,80}'''\s*[（(]", head))[:2]:
        i, depth = m.end(), 1
        while i < len(head) and depth and i - m.end() < 300:
            if head[i] in '(（': depth += 1
            elif head[i] in ')）': depth -= 1
            i += 1
        inner = head[m.end():i - 1]
        inner = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', inner)            # [[문서|보이는 글]] → 보이는 글
        inner = re.sub(r"'{2,}|\{\{\{[^}]*\}\}\}|\[\*[^\]]*\]", '', inner)        # 기울임·굵게, 문법 묶음, 각주
        prev = None
        while prev != inner: prev, inner = inner, re.sub(r'[（(][^()（）]*[)）]', '', inner)   # 읽기 괄호 걷기
        for part in re.split(r'[/,、;·]', inner):
            part = re.sub(r'^\s*[가-힣\s]+[:：]\s*', '', part).strip()         # 「일본어: 悠木碧」 → 「悠木碧」
            if part: out.append(part)
    return out

FIELD = re.compile(r'\|\|\s*(?:원제|원어 명칭|본명|이름|일본어)\s*\|\|\s*([^|\n]{1,80})')
KR_SEC = re.compile(r'^=+\s*(?:한국|국내)[^=\n]*(?:방영|방송|정발|더빙|수입)[^=\n]*=+\s*$(.*?)(?=^=+ )', re.M | re.S)

def plain(t):
    t = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[[^\]]*\]', '', t); t = re.sub(r"'''|''|~~|--|\{\{\{[^ ]*\s?|\}\}\}", '', t)
    t = re.sub(r'\|\|', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

HF_DATASET = os.environ.get('NAMU_DATASET', 'heegyu/namuwiki')   # 나무위키 2022-03-01 덤프 (title, text 열, 약 3GB)

def download_dump(dest='/tmp/namu'):
    """덤프 파일이 따로 없으면 Hugging Face에서 Parquet 파일들을 받아 그 폴더를 돌려줌."""
    http = Http(0.2)
    api = 'https://datasets-server.huggingface.co/parquet?dataset=' + urllib.parse.quote(HF_DATASET)
    d = http.json(api)
    files = [f for f in (d or {}).get('parquet_files', []) if f.get('split') == 'train']
    if not files: raise SchemaError(f'{HF_DATASET} 의 Parquet 파일 목록이 비어 있음 (주소나 형식이 바뀌었을 가능성)')
    os.makedirs(dest, exist_ok=True)
    for f in files:
        p = os.path.join(dest, f['filename'])
        if os.path.exists(p) and os.path.getsize(p) == f.get('size'): continue
        req = urllib.request.Request(f['url'], headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=600) as r, open(p + '.tmp', 'wb') as o:
            while True:
                b = r.read(1 << 20)
                if not b: break
                o.write(b)
        os.replace(p + '.tmp', p)
    return dest

def rows(path):
    if os.path.isdir(path):                      # 여러 Parquet 파일이 든 폴더
        for p in sorted(glob.glob(os.path.join(path, '**', '*.parquet'), recursive=True)):
            yield from rows(p)
        return
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
        try:
            run.say(f'덤프 파일 경로가 없어 Hugging Face({HF_DATASET})에서 받습니다.')
            path = download_dump()
        except Exception as e:
            run._record_fail('덤프 받기', e); run.fail_source(f'덤프를 받지 못함: {type(e).__name__}: {e}'); run.finish(); sys.exit(2)
    index, works, kr = {}, {}, {}      # index: 인물·회사·캐릭터용(엄격), works: 작품 제목용(넓게)
    try:
        for n, (title, text) in enumerate(rows(path)):
            if n % 100000 == 0: run.say(f'문서 {n}')
            if not title or text.startswith('#redirect') or text.startswith('#넘겨주기'): continue
            # 하위 문서(「아이돌 타임 프리파라/방영 목록」, 「…/애니메이션/1982년」)와 목록·등장인물 문서는 그 대상의 이름이 아니라서 색인에 넣지 않음
            if '/' in title or re.search(r'(목록|등장인물|에피소드|회차|줄거리|평가|설정|OST|음반|디스코그래피)$', title): continue
            head = text[:2500]; cands = set()
            for part in lead_names(head):
                if JA.search(part) and not re.search(r'[\uac00-\ud7a3]', part): cands.add(part)
            for m in FIELD.finditer(head):
                v = plain(m.group(1))
                if JA.search(v): cands.add(v)
            for c in cands:
                L = index.setdefault(pname(c), [])
                if title not in L and len(L) < 8: L.append(title)
            # 작품 제목은 문서 첫머리에 굵은 제목 없이 「개요」부터 시작하는 문서가 많아, 예전처럼 앞부분 괄호를 모두 씀.
            # (엄격한 색인만 쓰자 「タヌキとキツネ」 같은 작품의 한국어 제목이 사라졌음)
            wc = set(cands)
            for m in ANY_PAREN.finditer(head):
                for part in re.split(r'[/,、;·]', m.group(1)):
                    part = re.sub(r'^\s*[가-힣\s]+[:：]\s*', '', part).strip()
                    if JA.search(part) and not re.search(r'[\uac00-\ud7a3]', part): wc.add(part)
            for c in wc:
                L = works.setdefault(pname(c), [])
                if title not in L and len(L) < 8: L.append(title)
            m = KR_SEC.search(text)
            if m: kr[title] = plain(m.group(1))[:600]
        if len(index) < 10000: raise SchemaError(f'색인이 {len(index)}개뿐: 덤프 형식이 다를 가능성 (열 이름 title, text 필요)')
        if len(works) < 50000: raise SchemaError(f'작품 색인이 {len(works)}개뿐: 덤프 형식이 다를 가능성')
        save('namu', 'index', index); save('namu', 'index_works', works); save('namu', 'korea', kr)
        run.c['ok'] = len(index); run.say(f'색인 {len(index)}, 한국 방영 문단 {len(kr)}')
    except Exception as e:
        run._record_fail('덤프', e); run.fail_source(f'{type(e).__name__}: {e}')
    s = run.finish()
    sys.exit(2 if s['status'] == 'failed' else 0)
