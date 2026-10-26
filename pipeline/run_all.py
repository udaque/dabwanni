"""전체 파이프라인 실행기. 단계마다 시간 예산을 나눠 주고, 한 단계가 실패해도 나머지는 계속합니다.
끝나면 logs/summary.md에 결과표를 만들고, 실패한 출처가 있으면 종료 코드 1.
  python3 run_all.py --budget-min 320            # 정기 실행 (GitHub Actions 한 번 6시간 안)
  python3 run_all.py --only syoboi,tmdb          # 일부만
  python3 run_all.py --home                      # 집 PC 전용 단계(쇼보이)만, 병합은 하지 않음"""
import os, sys, json, time, subprocess, argparse, shutil, datetime
ROOT = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(ROOT, 'logs')

# (이름, 명령, 최대 시간 비율, 실행 주기 일수: 이 기간 안에 성공했으면 건너뜀)
STEPS = [
 ('catalog',        ['bash', '-c', './fetch_sources.sh && python3 build_catalog.py && python3 pack_catalog.py'], 0.03, 1),
 ('wikidata',       ['python3', 'collect_wikidata.py'], 0.05, 7),
 ('syoboi',         ['python3', 'collect_syoboi.py'], 0.20, 0),
 ('jawiki',         ['python3', 'collect_jawiki.py'], 0.12, 0),
 ('animethemes',    ['python3', 'collect_animethemes.py'], 0.05, 0),
 ('tmdb',           ['python3', 'collect_tmdb.py'], 0.12, 0),
 ('anilist',        ['python3', 'collect_anilist.py'], 0.60, 0),
 ('anilist_people', ['python3', 'collect_anilist_people.py'], 0.10, 0),
 ('music',          ['python3', 'collect_extra.py', 'music'], 0.08, 0),
 ('anitabi',        ['python3', 'collect_extra.py', 'pilgrimage'], 0.05, 0),
 ('laftel',         ['python3', 'collect_laftel.py'], 0.05, 0),
 ('namu',           ['python3', 'collect_namu.py'], 0.10, 25),
]
# 깃허브 액션 서버에서는 막히는 출처: 집 PC에서 home_syoboi.sh(run_all.py --home)로 따로 돌림
HOME_ONLY = {'syoboi', 'laftel'}      # 라프텔도 깃허브 서버에서는 403 차단 화면이 와서 집 PC에서
BUDGETED = {'wikidata', 'syoboi', 'jawiki', 'animethemes', 'tmdb', 'anilist', 'anilist_people', 'music', 'anitabi', 'laftel'}

def last_ok(name):
    p = os.path.join(ROOT, 'raw', '_runs.json')
    d = json.load(open(p)) if os.path.exists(p) else {}
    return d.get(name)
# 단계의 코드가 바뀌면 실행 주기와 상관없이 다시 돌림 (예: 중복 합치기를 고친 날 작품 목록을 바로 다시 만들게)
CODE = {'catalog': ['fetch_sources.sh', 'build_catalog.py', 'pack_catalog.py', 'names_ko.py', 'translit.py']}
def code_hash(name, cmd):
    import hashlib
    files = CODE.get(name) or [x for x in cmd if x.endswith(('.py', '.sh'))]
    h = hashlib.sha1()
    for f in files:
        p = os.path.join(ROOT, f)
        if os.path.exists(p): h.update(open(p, 'rb').read())
    return h.hexdigest()[:12]
def last_code(name):
    p = os.path.join(ROOT, 'raw', '_runs.json')
    return (json.load(open(p)) if os.path.exists(p) else {}).get(name + '#code')
def mark_ok(name, code=None):
    p = os.path.join(ROOT, 'raw', '_runs.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    d = json.load(open(p)) if os.path.exists(p) else {}
    d[name] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if code: d[name + '#code'] = code
    json.dump(d, open(p, 'w'), indent=1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--budget-min', type=float, default=320); ap.add_argument('--only', default='')
    ap.add_argument('--force', action='store_true', help='실행 주기와 상관없이 실행')
    ap.add_argument('--home', action='store_true', help='집 PC 전용 단계만 실행 (병합·배포는 클라우드 실행이 맡음)'); a = ap.parse_args()
    shutil.rmtree(LOGS, ignore_errors=True); os.makedirs(os.path.join(LOGS, 'summary'))
    only = set(x for x in a.only.split(',') if x)
    if a.home: only = set(HOME_ONLY)
    cat, cat_bak = os.path.join(ROOT, '..', 'site', 'data', 'catalog.json'), os.path.join(ROOT, 'raw', '_catalog.json')
    # 마지막으로 성공한 카탈로그(raw/_catalog.json)를 늘 우선 사용. 카탈로그 단계를 건너뛰는 날에도 저장소에 커밋된 옛 catalog.json이 배포되지 않게.
    if os.path.exists(cat_bak): os.makedirs(os.path.dirname(cat), exist_ok=True); shutil.copy(cat_bak, cat)
    t0, deadline = time.time(), time.time() + a.budget_min * 60
    results = []
    for name, cmd, share, every in STEPS:
        if only and name not in only: continue
        if name in HOME_ONLY and not only:
            results.append((name, 'skipped', '집 PC에서 따로 실행 (home_syoboi.sh)')); continue
        lo = last_ok(name); code = code_hash(name, cmd)
        if every and lo and not a.force and last_code(name) == code and (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(lo)).days < every:
            results.append((name, 'skipped', f'{every}일 주기, 최근 성공 {lo[:10]}')); continue
        left = (deadline - time.time()) / 60 - 15          # 마지막 병합·배포 몫 15분
        if left < 3: results.append((name, 'skipped', '시간 예산 없음')); continue
        c = [sys.executable if x == 'python3' else x for x in cmd]
        if name in BUDGETED: c += ['--budget-min', str(round(max(3, min(left, a.budget_min * share if name != 'anilist' else left - 30)), 1))]
        print(f'\n===== {name} 시작 =====', flush=True)
        with open(os.path.join(LOGS, f'{name}.out'), 'w', encoding='utf-8') as out:
            p = subprocess.run(c, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
        print(open(os.path.join(LOGS, f'{name}.out'), encoding='utf-8').read()[-3000:], flush=True)
        if p.returncode == 0:
            sm = os.path.join(LOGS, 'summary', f'{name}.json')
            st = json.load(open(sm))['status'] if os.path.exists(sm) else 'ok'
            if st == 'ok': mark_ok(name, code)
            if name == 'catalog': os.makedirs(os.path.dirname(cat_bak), exist_ok=True); shutil.copy(cat, cat_bak)
            results.append((name, st, ''))
        else:
            results.append((name, 'failed', f'종료 코드 {p.returncode}, 로그 {name}.out 참고'))
    if not a.home:
        print('\n===== 병합 =====', flush=True)
        with open(os.path.join(LOGS, 'build.out'), 'w', encoding='utf-8') as out:
            p = subprocess.run([sys.executable, 'build_details.py'], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
        results.append(('build', 'ok' if p.returncode == 0 else 'failed', '' if p.returncode == 0 else '로그 build.out 참고'))
        print(open(os.path.join(LOGS, 'build.out'), encoding='utf-8').read()[-2000:], flush=True)
    json.dump({'results': results, 'minutes': round((time.time() - t0) / 60, 1)}, open(os.path.join(LOGS, 'run.json'), 'w'), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, 'report.py'], cwd=ROOT)
    sys.exit(1 if any(r[1] == 'failed' for r in results) else 0)

if __name__ == '__main__': main()
