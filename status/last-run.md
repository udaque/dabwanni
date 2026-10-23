## 다봤니 데이터 갱신 결과

전체 309.6분

| 단계 | 결과 | 새로 받음 | 빈 결과 | 실패 | 최신이라 건너뜀 | 시간(분) |
|---|---|---|---|---|---|---|
| catalog | ⏭ 건너뜀 |  |  |  |  |  |
| wikidata | ⏭ 건너뜀 |  |  |  |  |  |
| syoboi | ❌ 실패 | 0 | 0 | 0 | 0 | 0.0 |
| jawiki | ❌ 실패 | 24 | 4 | 12 | 681 | 0.7 |
| animethemes | ❌ 실패 | 0 | 0 | 0 | 0 | 0.5 |
| tmdb | ⏸ 일부 (다음에 이어 받음) | 2309 | 25 | 0 | 3186 | 38.4 |
| anilist | ⏸ 일부 (다음에 이어 받음) | 2152 | 0 | 1 | 2069 | 235.3 |
| anilist_people | ✅ 성공 | 261 | 0 | 0 | 0 | 9.1 |
| music | ⏸ 일부 (다음에 이어 받음) | 65 | 412 | 0 | 136 | 20.6 |
| anitabi | ⏭ 건너뜀 |  |  |  |  |  |
| namu | ⏭ 건너뜀 |  |  |  |  |  |
| build | ✅ 성공 |  |  |  |  |  |

### 자세한 내용
- **catalog** (⏭ 건너뜀): 1일 주기, 최근 성공 2026-10-22
- **wikidata** (⏭ 건너뜀): 7일 주기, 최근 성공 2026-10-22
- **syoboi** (❌ 실패): 시험 요청 실패 (방송국 목록과 TID 1): 403 https://cal.syoboi.jp/db.php?Command=ChLookup <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/htm
- **jawiki** (❌ 실패): 실패율 12/40이 기준(20%)을 넘음
  - `a113051: IndexError: string index out of range`
  - `a1799: IndexError: string index out of range`
  - `a21552: IndexError: string index out of range`
  - `a4181: IndexError: string index out of range`
  - `a21249: IndexError: string index out of range`
- **animethemes** (❌ 실패): 시험 요청 실패 (작품 1개 조회): https://api.animethemes.moe/anime?page[size]=1 반복 실패: 520 error code: 520

- **tmdb** (⏸ 일부 (다음에 이어 받음)): 시간 예산 소진, 다음 실행에서 이어 받음
- **anilist** (⏸ 일부 (다음에 이어 받음)): 시간 예산 소진, 다음 실행에서 이어 받음
  - `a142080: IncompleteRead: IncompleteRead(12225 bytes read)`
- **music** (⏸ 일부 (다음에 이어 받음)): 시간 예산 소진, 다음 실행에서 이어 받음
- **anitabi** (⏭ 건너뜀): 시간 예산 없음
- **namu** (⏭ 건너뜀): 시간 예산 없음

전체 로그는 이 실행의 첨부 파일(logs)에 있습니다. 출처별 오류 상세는 `<단계>.jsonl`, 출력 전체는 `<단계>.out`을 보세요.
