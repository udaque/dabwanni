"""logs/의 실행 결과를 표로 정리 → logs/summary.md (GitHub Actions 실행 화면 요약과 실패 이슈 본문으로 씀)"""
import os, json, glob
ROOT = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(ROOT, 'logs')
ST = {'ok': '✅ 성공', 'partial': '⏸ 일부 (다음에 이어 받음)', 'failed': '❌ 실패', 'skipped': '⏭ 건너뜀'}
run = json.load(open(os.path.join(LOGS, 'run.json'))) if os.path.exists(os.path.join(LOGS, 'run.json')) else {'results': [], 'minutes': 0}
sm = {os.path.basename(f)[:-5]: json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(LOGS, 'summary', '*.json'))}
lines = [f"## 다봤니 데이터 갱신 결과", '', f"전체 {run['minutes']}분", '',
         '| 단계 | 결과 | 새로 받음 | 빈 결과 | 실패 | 최신이라 건너뜀 | 시간(분) |', '|---|---|---|---|---|---|---|']
fails = []
for name, status, note in run['results']:
    s = sm.get(name, {}); c = s.get('counts', {})
    status = s.get('status', status) if status != 'failed' else 'failed'
    lines.append(f"| {name} | {ST.get(status, status)} | {c.get('ok', '')} | {c.get('empty', '')} | {c.get('fail', '')} | {c.get('skip', '')} | {s.get('minutes', '')} |")
    if status == 'failed' or s.get('reason') or note:
        fails.append((name, status, s.get('reason') or note, s.get('examples', [])))
if fails:
    lines += ['', '### 자세한 내용']
    for name, status, reason, ex in fails:
        lines.append(f"- **{name}** ({ST.get(status, status)}): {reason}")
        lines += [f"  - `{e}`" for e in ex]
    lines += ['', '전체 로그는 이 실행의 첨부 파일(logs)에 있습니다. 출처별 오류 상세는 `<단계>.jsonl`, 출력 전체는 `<단계>.out`을 보세요.']
md = '\n'.join(lines) + '\n'
open(os.path.join(LOGS, 'summary.md'), 'w', encoding='utf-8').write(md)
if os.environ.get('GITHUB_STEP_SUMMARY'): open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8').write(md)
print(md)
