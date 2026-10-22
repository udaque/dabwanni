#!/bin/sh
# 카탈로그 원천 데이터 내려받기 (모두 공개 덤프)
set -e
mkdir -p "$(dirname "$0")/sources" && cd "$(dirname "$0")/sources"
curl -sL -o aod.json   https://github.com/manami-project/anime-offline-database/releases/latest/download/anime-offline-database-minified.json
curl -sL -o at.json    https://raw.githubusercontent.com/c032/anidb-animetitles-archive/main/data/animetitles.json
curl -sL -o fribb.json https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-full.json
curl -sL -o arm.json   https://raw.githubusercontent.com/kawaiioverflow/arm/master/arm.json
npm pack bangumi-data --silent >/dev/null && tar xzf bangumi-data-*.tgz package/dist/data.json && mv package/dist/data.json bangumi-data.json && rm -rf package bangumi-data-*.tgz
echo "내려받기 완료"
