# 윈도우(파워셸)에서 집 PC 수집(쇼보이 캘린더·라프텔·애니메테마즈·Anitabi). WSL 없이 동작합니다.
# 준비: 파이썬 설치 후  py -m pip install boto3 zstandard
# R2 열쇠는 홈 폴더(C:\Users\사용자이름)의 .dabwanni.env 파일에 (home_syoboi.py 설명 참고)
# 작업 스케줄러 등록은 pipeline 폴더로 이동한 뒤(cd), 아래 한 줄을 관리자 권한이 아닌 파워셸에서 한 번 실행:
#   Register-ScheduledTask -TaskName "다봤니 집 PC 수집" -Trigger (New-ScheduledTaskTrigger -Daily -At 1am) -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$((Resolve-Path .\home_syoboi.ps1).Path)`"") -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
$ErrorActionPreference = 'Continue'
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location $PSScriptRoot
$log = Join-Path $HOME 'dabwanni-home.log'
$py = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
& $py -X utf8 home_syoboi.py @args 2>&1 | Tee-Object -FilePath $log -Append
