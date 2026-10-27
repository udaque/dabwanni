# 다봤니

일본 애니메이션 전 작품 데이터베이스와 시청 기록 사이트입니다.
`site/`는 사이트, `pipeline/`은 데이터 수집기, `.github/workflows/update.yml`은 매일 자동 갱신입니다.

## 처음 설정 (한 번만)

### 1. GitHub 저장소
이 폴더를 새 저장소로 올립니다. **공개 저장소를 추천합니다.** 공개 저장소는 GitHub Actions 실행 시간이 무료이고,
비밀 키와 수집 데이터는 저장소에 들어가지 않습니다(비밀 설정과 R2에 보관).

### 2. Cloudflare
- **Pages 프로젝트**: Workers & Pages → 만들기 → Pages → 직접 업로드로 `dabwanni` 프로젝트를 만듭니다 (이름을 바꾸면 아래 `CF_PAGES_PROJECT` 변수에 적기).
- **API 토큰**: 내 프로필 → API 토큰 → 「Cloudflare Pages 편집」 권한으로 만듭니다.
- **R2 버킷**: R2 → 버킷 만들기(예: `dabwanni-raw`) → R2 API 토큰 만들기(객체 읽기·쓰기). 수집 원본과 로그를 보관합니다.
  R2를 설정하지 않으면 GitHub 캐시에 보관하는데, 7일 동안 쓰지 않으면 지워지고 10GB 제한이 있어 권장하지 않습니다.

### 3. TMDB
themoviedb.org 가입 → 설정 → API에서 키(v3)를 받습니다. 없으면 한국어 제목·회차 제목·OTT 수집만 건너뜁니다.

### 4. GitHub 비밀 설정
저장소 → Settings → Secrets and variables → Actions
- Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `TMDB_API_KEY`
- Variables (선택): `CF_PAGES_PROJECT`(기본 dabwanni), `NAMU_DUMP_URL`(나무위키 덤프 파일 주소, JSON 또는 Parquet)

### 5. 첫 실행
Actions → 다봤니 데이터 갱신 → Run workflow. 한 번에 최대 약 5시간 반 동안 받고 멈추며, 이후 매일 이어 받습니다.
전체를 처음 다 받는 데는 며칠 걸립니다(AniList가 가장 오래 걸림). 받은 만큼은 매번 사이트에 바로 반영됩니다.

## 아이폰에서 실행
- **GitHub 앱**: 저장소 → Actions → 다봤니 데이터 갱신 → Run workflow
- **단축어 버튼** (홈 화면에서 한 번 누르기):
  1. GitHub → Settings → Developer settings → Fine-grained tokens에서 이 저장소만, 권한 「Actions: Read and write」로 토큰 생성
  2. 단축어 앱 → 새 단축어 → 「URL 콘텐츠 가져오기」 추가
     - URL: `https://api.github.com/repos/<계정>/<저장소>/actions/workflows/update.yml/dispatches`
     - 방법: POST
     - 헤더: `Accept` = `application/vnd.github+json`, `Authorization` = `Bearer <토큰>`
     - 본문(JSON): `ref` = `main`
  3. 이어서 「알림 보기」에 「갱신을 시작했습니다」를 넣고, 홈 화면에 추가
  - 일부 단계만: 본문에 `inputs` 사전을 추가하고 `only` = `syoboi,tmdb`

## 갱신 규칙
- 새 작품: 아직 안 받은 작품은 모두 받음
- 방영 중·예정 작품과 올해·작년 작품: 3~7일마다 다시 받음 (새 회차·스태프 반영)
- OTT: 7일마다 전체 다시
- Wikidata(한국어 이름): 7일마다, 나무위키 덤프: 25일마다, 작품 목록: 매일
- 받아 둔 좋은 데이터는 빈 응답으로 덮어쓰지 않음

## 실패 감지와 로그
- 출처마다 결과를 아는 요청으로 먼저 시험해, 주소가 바뀌었거나 차단되면 그 출처만 중단하고 나머지는 계속
- 응답 형식이 바뀌거나, 실패율 20% 초과, 빈 응답만 계속되면 그 출처를 중단하고 실패로 기록
- 개별 작품 오류는 기록만 하고 계속 진행 (다음 실행에서 다시 시도)
- 결과 확인
  - Actions 실행 화면 맨 위에 출처별 결과표
  - 실행 첨부 파일 `logs-…`(90일 보관), R2의 `logs/날짜시각/`(계속 보관)
    - `<단계>.log` 진행 기록, `<단계>.jsonl` 오류 상세(요청 주소·응답 코드·응답 앞부분·오류 위치), `<단계>.out` 출력 전체
  - 저장소의 `status/last-run.md`에 마지막 결과
- 실패하면 「수집 실패」 이슈가 자동으로 생기고(이미 열려 있으면 댓글 추가), GitHub 앱 푸시와 메일이 옵니다.

## 집 PC 수집 (쇼보이 캘린더·라프텔·애니메테마즈·Anitabi·나무위키 실시간)
이 네 출처는 GitHub 서버에서 접속을 막아서, 집 PC에서 받아 R2에 올려 둡니다. 새벽 클라우드 갱신(한국 시간 3시 30분)이 그걸 내려받아 병합·배포합니다.

**준비 (한 번만)**
1. 파이썬 3.10 이상 설치
2. 이 저장소를 받기: `git clone https://github.com/udaque/dabwanni.git` (git이 있으면 실행할 때마다 코드를 최신으로 받습니다)
3. 라이브러리: 윈도우 `py -m pip install boto3 zstandard`, 맥 `python3 -m pip install boto3 zstandard`
   - 나무위키 실시간(실제 브라우저로 문서를 여는 단계)도 쓰려면 한 번 더: 윈도우 `py -m pip install playwright` 다음 `py -m playwright install chromium`, 맥 `python3 -m pip install playwright` 다음 `python3 -m playwright install chromium`. 설치하지 않으면 이 단계만 건너뜁니다.
4. 홈 폴더(윈도우 `C:\Users\사용자이름`, 맥 `~`)에 `.dabwanni.env` 파일을 만들고, GitHub Secrets와 같은 값을 넣기
   ```
   R2_ACCOUNT_ID=...
   R2_ACCESS_KEY_ID=...
   R2_SECRET_ACCESS_KEY=...
   R2_BUCKET=...
   ```

**실행**
- 윈도우(파워셸): `pipeline` 폴더에서 `.\home_syoboi.ps1`. 기록은 홈 폴더 `dabwanni-home.log`
- 맥·리눅스: `pipeline/home_syoboi.sh`
- 끝나면 화면에 출처별 결과표가 나오고, `pipeline/logs/summary.md`에도 남습니다.

**윈도우에서 「이 시스템에서 스크립트를 실행할 수 없습니다」(UnauthorizedAccess)가 뜰 때**
윈도우는 기본으로 파워셸 스크립트 실행을 막아 둡니다. 둘 중 하나로 합니다.
- 그때그때 허용하며 실행 (설정을 바꾸지 않음): `powershell -ExecutionPolicy Bypass -File .\home_syoboi.ps1`
- 내 계정에서만 영구 허용 (한 번만): `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 를 실행하고 `Y`. 그다음부터는 `.\home_syoboi.ps1` 로 바로 실행됩니다.
- 저장소를 압축 파일로 내려받아 풀었다면 「인터넷에서 받은 파일」 표시 때문에 계속 막힐 수 있습니다. `pipeline` 폴더에서 `Get-ChildItem -Recurse | Unblock-File` 을 한 번 실행하세요. git으로 받았다면 필요 없습니다.
- 아래 작업 스케줄러 등록 줄에는 이미 실행 정책 우회가 들어 있어서, 자동 실행에는 따로 할 일이 없습니다.

**실행 시간(최대 시간) 정하기**
- 첫 번째 값이 수집에 쓸 최대 시간(분)입니다. 비우면 90분.
- 예) 60분: 윈도우 `.\home_syoboi.ps1 60`, 맥 `pipeline/home_syoboi.sh 60`
- 다섯 단계가 이 시간을 나눠 씁니다: 나무위키 실시간 40%, 쇼보이 20%, 라프텔·애니메테마즈 15%씩, Anitabi 10%. 시간이 다 되면 그 단계는 멈추고 다음 실행에서 이어 받습니다.

**일부 단계만 실행하기**
- 두 번째 값에 단계 이름을 쉼표로 적습니다. 단계 이름: `syoboi`(쇼보이), `laftel`(라프텔), `animethemes`(애니메테마즈), `anitabi`(Anitabi), `namu_live`(나무위키 실시간)
- 예) 라프텔과 나무위키만 60분: 윈도우 `.\home_syoboi.ps1 60 laftel,namu_live`, 맥 `pipeline/home_syoboi.sh 60 laftel,namu_live`
- 고른 단계만 돌아도 시간 몫은 위 비율대로라, 하나만 돌릴 땐 첫 번째 값을 넉넉히 주세요.

**매일 자동으로 (시각 정하기)**
- 윈도우: 파워셸에서 `pipeline` 폴더로 이동한 뒤 아래 한 줄을 한 번 실행하면 매일 새벽 1시에 돕니다(`home_syoboi.ps1` 맨 위 주석에도 있음).
  ```
  Register-ScheduledTask -TaskName "다봤니 집 PC 수집" -Trigger (New-ScheduledTaskTrigger -Daily -At 1am) -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$((Resolve-Path .\home_syoboi.ps1).Path)`"") -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)
  ```
  - 시각: `-At 1am` 을 바꿉니다(예: `-At 2am`, `-At 12:30am`).
  - 최대 시간·단계: 줄 끝 `` `"") `` 의 `` `" `` 와 `"` 사이에 값을 넣습니다. 예) 60분: `` …Path)`" 60") ``, 라프텔·나무위키만 60분: `` …Path)`" 60 laftel,namu_live") ``
  - 이미 등록했다면 먼저 `Unregister-ScheduledTask -TaskName "다봤니 집 PC 수집" -Confirm:$false` 로 지우고 다시 등록합니다. 작업 스케줄러 앱에서 트리거 시각만 고쳐도 됩니다. 예전에 「다봤니 쇼보이 수집」이라는 이름으로 등록했다면 그 이름으로 지웁니다.
- 맥: `crontab -e`에 `0 1 * * * /경로/dabwanni/pipeline/home_syoboi.sh >> ~/dabwanni-home.log 2>&1`
  - 시각: 앞의 `0 1` 이 1시 0분입니다(2시 30분이면 `30 2`).
  - 최대 시간·단계: `home_syoboi.sh 60 laftel,namu_live` 처럼 붙입니다.
- 클라우드 갱신(한국 시간 새벽 3시 30분)보다 먼저 끝나게, 시작 시각 + 최대 시간이 3시 30분 전이 되도록 정하는 게 좋습니다. 겹쳐도 서로 지우지는 않지만(출처 묶음은 따로 올리고, 실행 기록은 올리기 직전에 합침), 겹치면 그날 집 PC 결과는 다음 날 반영됩니다.

**확인**
- 실행 결과표에서 syoboi·laftel·animethemes·anitabi·namu_live 줄이 모두 성공인지 봅니다.
- namu_live가 「Cloudflare 확인 화면이 풀리지 않음」으로 실패하면, 집 인터넷에서도 나무위키가 자동 브라우저를 막는 것입니다. 이 경우 확인 화면을 우회하지 않고 그 단계는 멈춥니다.
- 다음 클라우드 갱신부터 사이트에 반영됩니다. 기다리기 싫으면 Actions에서 「다봤니 데이터 갱신」을 「일부 단계만」에 catalog를 넣고 실행하면 병합·배포만 바로 합니다.

## 내 컴퓨터에서 직접 실행
```sh
pip install pykakasi pyarrow
cd pipeline
python3 run_all.py --budget-min 60              # 전부 (시간 예산 안에서)
python3 run_all.py --only syoboi --force        # 한 단계만
```

## 출처
manami-project/anime-offline-database (ODbL), AniDB 제목 덤프 (CC BY-NC-SA), Fribb/anime-lists, kawaiioverflow/arm, bangumi-data,
AniList, 쇼보이 캘린더, 일본어 위키백과, Wikidata, AnimeThemes, TMDB, MusicBrainz, Anitabi, 나무위키 (CC BY-NC-SA). 비상업 개인 이용 전제입니다.
