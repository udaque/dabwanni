"""일본어 위키백과: 회차별 부제·각본·콘티·연출·작화감독·총작화감독·협력(하청) 스튜디오, 극장판 흥행 수입.
Wikidata 수집(collect_wikidata.py) 뒤에 실행합니다."""
import re, sys, json
from common import *

API = 'https://ja.wikipedia.org/w/api.php?action=parse&prop=wikitext&format=json&formatversion=2&redirects=1&page='
COLS = {'話数': 'no', '話': 'no', '#': 'no', 'サブタイトル': 'title', '副題': 'title', 'タイトル': 'title', '脚本': 'script', 'シナリオ': 'script',
        '絵コンテ': 'storyboard', 'コンテ': 'storyboard', '演出': 'director', '作画監督': 'animdir', '総作画監督': 'chiefanimdir',
        'アニメーション制作': 'studio', '制作協力': 'studio', 'グロス': 'studio', '作画': 'animdir', '放送日': 'air', '初放送日': 'air', '配信日': 'air', '備考': 'note'}

def clean(s):
    s = re.sub(r'<ref[^>]*/>|<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'\{\{(?:lang|Lang)\|[^|]*\|([^}]*)\}\}', r'\1', s)
    s = re.sub(r'\{\{(?:nowrap|Nowrap|small|smaller|ruby|Ruby)\|([^|}]*)(?:\|[^}]*)?\}\}', r'\1', s)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r"'{2,}", '', s)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

def split_cells(line, sep):
    line = line[1:] if line[:1] in '|!' else line
    return [c for c in re.split(r'\|\||!!' if sep == '!' else r'\|\|', line)]

def parse_cell(raw):
    attrs, val = {}, raw
    m = re.match(r'\s*([^|\[\]{}]*?)\|(?!\|)(.*)$', raw, re.S)
    if m and re.search(r'(rowspan|colspan|style|align|class)\s*=', m.group(1)):
        val = m.group(2)
        for k in ('rowspan', 'colspan'):
            x = re.search(k + r'\s*=\s*"?(\d+)', m.group(1))
            if x: attrs[k] = int(x.group(1))
    return attrs, clean(val)

def tables(wt):
    for m in re.finditer(r'\{\|.*?\n\|\}', wt, re.S):
        yield m.group(0)

def parse_table(t):
    rows, cur = [], None
    for line in t.split('\n')[1:]:
        if line.startswith('|-') or line.startswith('|}'):
            if cur is not None: rows.append(cur)
            cur = []; continue
        if line.startswith('|+'): continue
        if line[:1] in '|!':
            if cur is None: cur = []
            for c in split_cells(line, line[0]):
                cur.append((line[0] == '!',) + parse_cell(c))
        elif cur:
            h, a, v = cur[-1]; cur[-1] = (h, a, v + '\n' + clean(line))
    if cur: rows.append(cur)
    # rowspan/colspan 펼치기
    grid, carry = [], {}
    for r in rows:
        out, ci, it = [], 0, iter(r)
        pending = list(r)
        while pending or ci in carry:
            if ci in carry:
                v, left = carry[ci]; out.append(v)
                if left > 1: carry[ci] = (v, left - 1)
                else: del carry[ci]
                ci += 1; continue
            h, a, v = pending.pop(0)
            for _ in range(a.get('colspan', 1)):
                out.append((h, v))
                if a.get('rowspan', 1) > 1: carry[ci] = ((h, v), a['rowspan'] - 1)
                ci += 1
        if out: grid.append(out)
    return grid

def episode_tables(wt):
    eps = []
    for t in tables(wt):
        g = parse_table(t)
        if not g: continue
        head = [v for h, v in g[0]]
        keys = [COLS.get(re.sub(r'\s', '', x)) for x in head]
        if 'no' not in keys or not ({'title', 'script', 'storyboard', 'director', 'animdir'} & set(keys)): continue
        for row in g[1:]:
            if all(h for h, _ in row): continue
            e = {}
            for k, (_, v) in zip(keys, row):
                if k == 'air' and v: v = v.replace(chr(10), '')
                if k and v: e[k] = v if k in ('no', 'title', 'air', 'note') else [x.strip() for x in re.split(r'[\n、,，・/]', v) if x.strip()]
            no = re.sub(r'[^\d.]', '', e.get('no', ''))
            if not no: continue
            e['no'] = str(int(float(no))) if no.replace('.', '').isdigit() else no
            if isinstance(e.get('title'), str): e['title'] = e['title'].strip('「」')
            eps.append(e)
    return eps

def box_office(wt):
    m = re.search(r'\|\s*興行収入\s*=\s*([^\n]+)', wt)
    return clean(m.group(1)) if m else None

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); budget_arg(ap); a = ap.parse_args()
    http = Http(1.0)
    wd = {r['mal']: r for r in (load('wikidata', 'works') or []) if r.get('jawiki')}
    W = [w for w in load_catalog() if w['mal'] and str(w['mal']) in wd]
    def text(title):
        d = http.json(API + urllib.parse.quote(title))
        if d is None or ('parse' not in d and 'error' not in d): raise SchemaError('위키백과 응답 형식이 바뀜')
        if 'error' in d: raise NotFound(title)
        return d['parse'].get('wikitext') or ''
    def work(w, run):
        http.run = run
        if not needs('jawiki', w, fresh_days=60, airing_days=7): return SKIP
        wt = text(wd[str(w['mal'])]['jawiki'])
        r = {'episodes': episode_tables(wt), 'box_office': box_office(wt)}
        save('jawiki', w['k'], r); return r
    run_source('jawiki', W, work, canary=(lambda: '各話リスト' in text('カウボーイビバップ') or True, '카우보이 비밥 문서'),
               budget_min=a.budget_min, max_empty=0.95)
