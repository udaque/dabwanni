"""しょぼいカレンダー: 일본 방송국·첫 방송 시각, 회차 부제, 주제가·삽입곡(가수·작사·작곡·편곡), 캐스트.
2000년대 이후 TV 작품에 강합니다. 카탈로그의 syobocal TID(kawaiioverflow/arm 매핑)를 씁니다."""
import sys, re, xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from common import *

DB = 'https://cal.syoboi.jp/db.php?'
WD = '월화수목금토일'

def channels(http):
    try: x = ET.fromstring(http.req(DB + 'Command=ChLookup'))
    except ET.ParseError: raise SchemaError('방송국 목록 응답이 XML이 아님')
    return {c.findtext('ChID'): c.findtext('ChName') for c in x.iter('ChItem')}

def parse_comment(txt):
    songs, cast, staff, sec, cur = [], [], [], None, None
    for line in (txt or '').splitlines():
        line = line.rstrip()
        if line.startswith('*'):
            head = line[1:].strip(); cur = None
            m = re.match(r'(オープニング|エンディング|挿入歌|主題歌|イメージソング)(?:テーマ)?\s*(\d*)\s*[「『](.+?)[」』]', head)
            if m:
                kind = {'オープニング': 'OP', 'エンディング': 'ED', '挿入歌': 'IN', '主題歌': 'OP', 'イメージソング': 'IN'}[m.group(1)]
                cur = {'kind': kind, 'seq': int(m.group(2)) if m.group(2) else None, 'title': m.group(3), 'credits': [], 'eps': None}
                songs.append(cur); sec = 'song'
            elif head.startswith('キャスト'): sec = 'cast'
            elif head.startswith('スタッフ'): sec = 'staff'
            else: sec = None
            continue
        if not line.startswith(':'): continue
        parts = line[1:].split(':', 1)
        if len(parts) != 2: continue
        key, val = parts[0].strip(), parts[1].strip()
        if sec == 'song' and cur:
            roles = [r for r in re.split(r'[・/／、]', key) if r in ('歌', '作詞', '作曲', '編曲')]
            if roles:
                for n in re.split(r'[、,，/／&＆]| with |feat\.', val):
                    n = n.strip()
                    for r in roles:
                        if n: cur['credits'].append({'role': r, 'name': n})
            elif key.startswith('使用話数'): cur['eps'] = val.replace('#', '').replace('～', '-').replace('〜', '-')
        elif sec == 'staff' and key:
            for n in re.split(r'[、,，/／]', val):
                n = n.strip()
                if n: staff.append({'role': key, 'name': n})
        elif sec == 'cast' and key:
            for n in re.split(r'[、,，/／]', val):
                n = n.strip()
                if n: cast.append({'char': key, 'name': n})
    return songs, cast, staff

def parse_subtitles(txt):
    eps = []
    for m in re.finditer(r'^\*(\d+)\*(.*)$', txt or '', re.M):
        eps.append({'no': str(int(m.group(1))), 'title': {'ja': m.group(2).strip()}})
    return eps

def programs(http, tid, chmap):
    """첫 방송(방송국별), 재방송, 휴방, 연기, 회차별 엔드카드."""
    try: x = ET.fromstring(http.req(DB + f'Command=ProgLookup&TID={tid}&JOIN=SubTitles'))
    except ET.ParseError: raise SchemaError('편성 응답이 XML이 아님')
    P = []
    for p in x.iter('ProgItem'):
        st = p.findtext('StTime')
        if not st or p.findtext('Deleted') == '1': continue
        P.append({'ch': p.findtext('ChID'), 'st': datetime.strptime(st, '%Y-%m-%d %H:%M:%S'),
                  'count': p.findtext('Count'), 'flag': int(p.findtext('Flag') or 0), 'cmt': p.findtext('ProgComment') or ''})
    P.sort(key=lambda p: p['st'])
    def fmt(dt):
        late = dt.hour < 5; d0 = dt - timedelta(days=1) if late else dt
        return d0.strftime('%Y-%m-%d'), WD[d0.weekday()] + '요일', f'{dt.hour + (24 if late else 0):02d}:{dt.minute:02d}'
    first, rebro, endcard, notes = {}, [], {}, []
    for p in P:
        if p['flag'] & 8:                                     # 재방송 표시
            if not any(r['ch'] == p['ch'] for r in rebro): rebro.append({'ch': p['ch'], 'st': p['st']})
            continue
        if p['ch'] not in first: first[p['ch']] = p['st']
        m = re.search(r'エンドカード[:：]\s*([^\n/]+)', p['cmt'])
        if m and p['count']: endcard.setdefault(p['count'], m.group(1).strip())
        if '延期' in p['cmt'] or '休止' in p['cmt']:
            d, wd, t = fmt(p['st']); notes.append(f"{d} {chmap.get(p['ch'], p['ch'])}: {p['cmt'].strip()[:80]}")
    bro = []
    for ch, st in sorted(first.items(), key=lambda t: t[1]):
        d, wd, t = fmt(st); bro.append({'station': chmap.get(ch, ch), 'start': d, 'weekday': wd, 'time': t})
    # 휴방: 첫 방송국의 회차 간격이 2주 이상
    main = min(first, key=first.get) if first else None
    seq = [p for p in P if p['ch'] == main and not p['flag'] & 8 and p['count']]
    for a, b in zip(seq, seq[1:]):
        gap = (b['st'] - a['st']).days
        if gap >= 13 and a['count'] != b['count']:
            notes.append(f"{a['count']}화 뒤 {gap // 7 - 1}주 휴방")
    rb = []
    for r in rebro:
        d, wd, t = fmt(r['st']); rb.append({'station': chmap.get(r['ch'], r['ch']), 'start': d, 'weekday': wd, 'time': t})
    return bro, rb, endcard, notes

def lookup_title(http, tid):
    b = http.req(DB + f"Command=TitleLookup&TID={tid}")
    try: x = ET.fromstring(b)
    except ET.ParseError: raise SchemaError('쇼보이 캘린더 응답이 XML이 아님: ' + b[:120].decode('utf-8', 'replace'))
    if x.tag != 'TitleLookupResponse' and x.find('.//TitleItems') is None: raise SchemaError('쇼보이 캘린더 응답 형식이 바뀜: ' + x.tag)
    return x.find('.//TitleItem')

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--interval', type=float, default=1.5); budget_arg(ap); a = ap.parse_args()
    http = Http(a.interval)
    W = [w for w in load_catalog() if w.get('sy')]
    chmap = {}
    def canary():
        chmap.update(channels(http)); t = lookup_title(http, 1)
        return len(chmap) > 10 and t is not None and t.findtext('Title')
    def work(w, run):
        http.run = run
        if not needs('syoboi', w, airing_days=3): return SKIP
        t = lookup_title(http, w['sy'])
        if t is None: save('syoboi', w['k'], {}); return {}
        songs, cast, staff = parse_comment(t.findtext('Comment'))
        bro, rebro, endcard, notes = programs(http, w['sy'], chmap)
        eps = parse_subtitles(t.findtext('SubTitles'))
        for e in eps:
            if e['no'] in endcard: e['endcard'] = endcard[e['no']]
        r = {'tid': w['sy'], 'title_ja': t.findtext('Title'), 'title_en': t.findtext('TitleEN'), 'songs': songs, 'cast': cast,
             'staff': staff, 'episodes': eps, 'broadcast': bro, 'rebroadcast': rebro, 'notes': notes}
        save('syoboi', w['k'], r); return r
    run_source('syoboi', W, work, canary=(canary, '방송국 목록과 TID 1'), budget_min=a.budget_min)
