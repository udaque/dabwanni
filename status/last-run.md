## 다봤니 데이터 갱신 결과

전체 21.9분

| 단계 | 결과 | 새로 받음 | 빈 결과 | 실패 | 최신이라 건너뜀 | 시간(분) |
|---|---|---|---|---|---|---|
| catalog | ✅ 성공 |  |  |  |  |  |
| wikidata | ❌ 실패 | 0 | 0 | 1 | 0 | 0.1 |
| syoboi | ❌ 실패 | 0 | 0 | 0 | 0 | 0.0 |
| jawiki | ✅ 성공 | 0 | 0 | 0 | 0 | 0.0 |
| animethemes | ❌ 실패 | 0 | 0 | 0 | 0 | 0.5 |
| tmdb | ⏸ 일부 (다음에 이어 받음) | 538 | 1 | 0 | 0 | 7.2 |
| anilist | ⏸ 일부 (다음에 이어 받음) | 122 | 0 | 0 | 0 | 7.1 |
| anilist_people | ❌ 실패 | 0 | 0 | 40 | 0 | 1.4 |
| music | ⏸ 일부 (다음에 이어 받음) | 17 | 61 | 0 | 0 | 4.8 |
| anitabi | ❌ 실패 | 0 | 40 | 0 | 0 | 0.3 |
| namu | ⏭ 건너뜀 | 0 | 0 | 0 | 0 | 0.0 |
| build | ✅ 성공 |  |  |  |  |  |

### 자세한 내용
- **wikidata** (❌ 실패): 출처 오류: works 결과가 7378행뿐이라 저장하지 않음
  - `works: SchemaError: works 결과가 7378행뿐이라 저장하지 않음`
- **syoboi** (❌ 실패): 시험 요청 실패 (방송국 목록과 TID 1): 403 https://cal.syoboi.jp/db.php?Command=ChLookup <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/htm
- **animethemes** (❌ 실패): 시험 요청 실패 (첫 쪽): https://api.animethemes.moe/anime?page[size]=100&include=resources,animethemes.song.artists,animethemes.animethemeentries&page[number]=1 반복 실패: 520 error code: 520

- **tmdb** (⏸ 일부 (다음에 이어 받음)): 시간 예산 소진, 다음 실행에서 이어 받음
- **anilist** (⏸ 일부 (다음에 이어 받음)): 시간 예산 소진, 다음 실행에서 이어 받음
- **anilist_people** (❌ 실패): 실패율 40/40이 기준(20%)을 넘음
  - `묶음0: AttributeError: 'int' object has no attribute 'startswith'`
  - `묶음1: AttributeError: 'int' object has no attribute 'startswith'`
  - `묶음2: AttributeError: 'int' object has no attribute 'startswith'`
  - `묶음3: AttributeError: 'int' object has no attribute 'startswith'`
  - `묶음4: AttributeError: 'int' object has no attribute 'startswith'`
- **music** (⏸ 일부 (다음에 이어 받음)): 시간 예산 소진, 다음 실행에서 이어 받음
- **anitabi** (❌ 실패): 빈 응답만 40건: 주소나 형식이 바뀌었을 가능성
- **namu** (⏭ 건너뜀): 덤프 파일 없음

전체 로그는 이 실행의 첨부 파일(logs)에 있습니다. 출처별 오류 상세는 `<단계>.jsonl`, 출력 전체는 `<단계>.out`을 보세요.
