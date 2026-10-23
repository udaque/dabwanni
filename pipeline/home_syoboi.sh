#!/bin/bash
# 맥·리눅스에서 쇼보이 캘린더 수집 (윈도우는 home_syoboi.ps1). 실제 일은 home_syoboi.py가 합니다.
# 준비: python3 -m pip install boto3 zstandard ,  R2 열쇠는 ~/.dabwanni.env
cd "$(dirname "$0")" && exec python3 -X utf8 home_syoboi.py "$@"
