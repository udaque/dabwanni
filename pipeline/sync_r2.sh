#!/bin/bash
# 수집 원본(pipeline/raw)과 로그를 Cloudflare R2에 보관/복원합니다. 출처별로 압축해 주고받습니다.
#   ./sync_r2.sh pull      R2 → raw
#   ./sync_r2.sh push      raw → R2
#   ./sync_r2.sh logs      logs → R2 logs/날짜시각/
# 필요한 환경 변수: R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET
set -euo pipefail
cd "$(dirname "$0")"
if [ -z "${R2_BUCKET:-}" ]; then echo "R2 설정이 없어 건너뜁니다."; exit 0; fi
export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" AWS_DEFAULT_REGION=auto
EP="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
S3="aws s3 --endpoint-url $EP --only-show-errors"
mkdir -p raw .r2
case "$1" in
  pull)
    $S3 sync "s3://$R2_BUCKET/raw/" .r2/ || { echo "R2에서 받지 못했습니다 (첫 실행이면 정상)"; exit 0; }
    for f in .r2/*.tar.zst; do [ -e "$f" ] || continue; tar --zstd -xf "$f" -C raw; done
    cp -f .r2/_runs.json .r2/_catalog.json raw/ 2>/dev/null || true
    echo "복원: $(ls raw | wc -l)개 항목" ;;
  push)
    rm -rf .r2 && mkdir .r2
    for d in raw/*/; do
      n=$(basename "$d")
      # 집 PC가 따로 모아 올리는 출처는 여기서 올리지 않음 (도중에 집 PC가 올린 새 판을 옛 판으로 덮어쓰지 않게)
      case "$n" in syoboi|laftel|animethemes|anitabi|namu_live) continue ;; esac
      tar --zstd -cf ".r2/$n.tar.zst" -C raw "$n"
    done
    cp -f raw/_catalog.json .r2/ 2>/dev/null || true
    # 실행 기록: 올리기 직전 R2 최신판을 받아, 집 PC 단계 기록은 R2 쪽 것을 살리고 나머지만 이번 실행 것으로 (집 PC가 도중에 올린 기록을 덮지 않게)
    if [ -f raw/_runs.json ]; then
      $S3 cp "s3://$R2_BUCKET/raw/_runs.json" .r2/_runs.remote.json 2>/dev/null || echo '{}' > .r2/_runs.remote.json
      python3 - << 'PY'
import json
mine = json.load(open('raw/_runs.json')); cur = json.load(open('.r2/_runs.remote.json'))
HOME = {'syoboi', 'laftel', 'animethemes', 'anitabi', 'namu_live'}
out = {k: v for k, v in mine.items() if k.split('#')[0] not in HOME}
out.update({k: v for k, v in cur.items() if k.split('#')[0] in HOME})
json.dump(out, open('.r2/_runs.json', 'w'), indent=1)
PY
      rm -f .r2/_runs.remote.json
    fi
    $S3 sync .r2/ "s3://$R2_BUCKET/raw/"
    echo "보관 완료: $(du -sh .r2 | cut -f1)" ;;
  logs)
    $S3 cp --recursive logs/ "s3://$R2_BUCKET/logs/$(date -u +%Y%m%d-%H%M)/" ;;
esac
