"""집 PC에서 쇼보이 캘린더(syoboi)와 라프텔(laftel)을 수집해 R2에 올립니다. 윈도우·맥·리눅스 공통.
깃허브 액션 서버는 쇼보이 쪽 클라우드플레어 확인 화면에 막혀서, 이 단계만 집 인터넷에서 돌립니다.
매일 클라우드 갱신(한국 시간 03:30)보다 먼저 끝나도록 새벽 1시쯤 돌리세요. 병합·배포는 클라우드 갱신이 합니다.

준비: 파이썬 3.10 이상, 그리고  pip install boto3 zstandard
R2 열쇠: 홈 폴더의 .dabwanni.env 파일(또는 환경 변수)에 깃허브 Secrets와 같은 값
  R2_ACCOUNT_ID=...
  R2_ACCESS_KEY_ID=...
  R2_SECRET_ACCESS_KEY=...
  R2_BUCKET=...
실행: python home_syoboi.py [분]   (분: 수집에 쓸 최대 시간, 기본 90)
R2에는 sync_r2.sh와 같은 형식(raw/<출처>.tar.zst)으로 주고받습니다. 집에서는 쇼보이 묶음과 카탈로그·실행 기록만 받고 올립니다."""
import os, sys, io, json, tarfile, shutil, subprocess, datetime

ROOT = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(ROOT, 'raw')
SRCS = ('syoboi', 'laftel')      # 깃허브 서버에서 막히는 출처들 (run_all.py의 HOME_ONLY와 같게)

def say(*a): print(datetime.datetime.now().strftime('%H:%M:%S'), *a, flush=True)

def load_env():
    p = os.path.join(os.path.expanduser('~'), '.dabwanni.env')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    miss = [k for k in ('R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET') if not os.environ.get(k)]
    if miss: sys.exit('R2 설정이 없습니다: ' + ', '.join(miss) + ' (홈 폴더의 .dabwanni.env를 확인하세요)')

def client():
    try: import boto3
    except ImportError: sys.exit('boto3가 없습니다. 먼저  pip install boto3 zstandard  를 실행하세요.')
    return boto3.client('s3', endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'], region_name='auto')

def zstd():
    try: import zstandard; return zstandard
    except ImportError: sys.exit('zstandard가 없습니다. 먼저  pip install boto3 zstandard  를 실행하세요.')

def unpack(data, dest):
    """sync_r2.sh가 만든 <출처>.tar.zst를 raw 아래에 풂"""
    raw = zstd().ZstdDecompressor().stream_reader(io.BytesIO(data)).read()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as t:
        for m in t.getmembers():
            if m.name.startswith('/') or '..' in m.name.split('/'): raise SystemExit('묶음 안의 경로가 이상합니다: ' + m.name)
        t.extractall(dest)

def pack(src_dir, name):
    """raw/<name> 폴더를 tar --zstd -C raw <name> 과 같은 모양으로 묶음"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:', format=tarfile.GNU_FORMAT) as t:
        t.add(os.path.join(src_dir, name), arcname=name)
    return zstd().ZstdCompressor(level=6).compress(buf.getvalue())

def main():
    budget = sys.argv[1] if len(sys.argv) > 1 else '90'
    load_env(); s3 = client(); B = os.environ['R2_BUCKET']; os.makedirs(RAW, exist_ok=True)
    say('===== 쇼보이 수집 시작 =====')
    if shutil.which('git'):
        r = subprocess.run(['git', '-C', os.path.dirname(ROOT), 'pull', '-q', '--ff-only'])
        if r.returncode: say('코드를 최신으로 받지 못했습니다 (지금 코드로 진행)')
    # 받기: 카탈로그·실행 기록·쇼보이 묶음
    for f in ('_catalog.json', '_runs.json'):
        try: s3.download_file(B, 'raw/' + f, os.path.join(RAW, f)); say('받음:', f)
        except Exception as e: say('받지 못함:', f, '(첫 실행이면 정상)', type(e).__name__)
    for SRC in SRCS:
        try:
            data = s3.get_object(Bucket=B, Key=f'raw/{SRC}.tar.zst')['Body'].read()
            shutil.rmtree(os.path.join(RAW, SRC), ignore_errors=True); unpack(data, RAW); say(f'받음: {SRC}.tar.zst ({len(data)//1024}KB)')
        except s3.exceptions.NoSuchKey: say(f'R2에 {SRC} 묶음이 아직 없습니다 (처음부터 수집)')
    # 수집 (병합·배포는 클라우드 갱신이 함)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    r = subprocess.run([sys.executable, 'run_all.py', '--home', '--budget-min', budget], cwd=ROOT, env=env)
    if r.returncode: say('쇼보이 수집에 실패한 항목이 있습니다 (pipeline/logs/summary.md 참고)')
    # 올리기: 쇼보이 묶음 + 실행 기록
    for SRC in SRCS:
        if os.path.isdir(os.path.join(RAW, SRC)):
            z = pack(RAW, SRC); s3.put_object(Bucket=B, Key=f'raw/{SRC}.tar.zst', Body=z); say(f'올림: {SRC}.tar.zst ({len(z)//1024}KB)')
    if os.path.exists(os.path.join(RAW, '_runs.json')): s3.upload_file(os.path.join(RAW, '_runs.json'), B, 'raw/_runs.json'); say('올림: _runs.json')
    sm = os.path.join(ROOT, 'logs', 'summary.md')
    if os.path.exists(sm): print(open(sm, encoding='utf-8').read()[-1500:])
    say('===== 끝 =====')

if __name__ == '__main__': main()
