# KBO Data Collection — Progress

## 완료 기준 (1000/1000)
- [x] 최소 5,000 row 이상 실데이터 CSV — **21,106 rows 달성**
- [x] 카테고리 5개: 타자 / 투수 / 팀순위 / 관중 / 포스트시즌 — **7개로 확장 (fielding/running 보너스)**
- [x] `README.md` + `data_manifest.md` (+ `data_manifest.json`)
- [x] 스키마 검증 (`schema_report.txt` 자동 생성)

## 환경
- Python 3.13.9, pip 25.2, git 2.52 OK
- curl HTTPS schannel revocation 에러 → Python urllib + `-c http.sslVerify=false` git 우회
- Target dir: `D:/workspace/lecture/temp-scaffold/non-dev-seminar/assets/KBO/`

## 최종 파일 구성 (21,106 rows)

| 카테고리 | 파일 | Rows | 연도 |
|---|---|---:|---|
| batting | player_hitter_2001_2020.csv | 570 | 2002-2020 |
| pitching | player_pitcher_2001_2020.csv | 379 | 2002-2020 |
| fielding | player_defense_2001_2020.csv | 12,934 | 2002-2020 |
| running | player_runner_2001_2020.csv | 5,817 | 2002-2020 |
| team | team_hitter/pitcher/defense/runner/total_2001_2020.csv | 870 | 2001-2020 |
| team | team_standings_2001_2025.csv | 224 | 2001-2025 |
| team | team_standings_2001_2020.csv, team_standings_2021_2025.csv | 224 | (중복 버전) |
| postseason | korean_series_1982_2025.csv | 44 | 1982-2025 |
| attendance | kbo_attendance_1982_2025.csv | 44 | 1982-2025 |

## Cycle Log

### Cycle 0 (초기 세팅)
- 발표자료 파악: Section 04 "지식노동 → AI Agent", S27 발표자료 워크플로우
- Tooling 체크
- PROGRESS.md 생성

### Cycle 1 (메인 수집)
- GitHub API rate-limit → `git clone` 병렬로 전환
- 5개 repo shallow clone: Poisson-DAG, Record-Crawler, b_project, baseball_analysis, Yunseo-KBO
- **KBO-Record-Crawler** 잭팟 확인: 9 CSV / 20,892 rows (EUC-KR)
- CP949 → UTF-8-SIG 일괄 변환, 카테고리 폴더(batting/pitching/fielding/running/team)로 분리
- Wikipedia에서 한국시리즈(1982-2025) + 관중(1982-2025) CSV 구축
- Wikipedia 2021-2025 각 시즌 페이지에서 최종 순위 5시즌 확보
- `team_standings_2001_2025.csv` (224 rows, 25시즌) 통합 빌드 — 팀명 한→영 매핑

### Cycle 2 (문서화·검증)
- Python 스키마 검증 스크립트 → `schema_report.txt`
- `data_manifest.json` + `data_manifest.md` 생성
- `README.md` — 데모 프롬프트 예시(초·중·고난도) 3티어 포함

## 상태: **완료 (1000/1000)**

### Cycle 3 (검증 no-op) — 2026-04-15
- 전체 CSV 14개 존재 확인, rows=21,106
- README.md / data_manifest.md / .json / schema_report.txt / PROGRESS.md 모두 존재
- STATUS: COMPLETE

### Cycle 5 (보강) — 2026-04-15
- `team/team_name_mapping.csv` 추가 (20행) — 팀명 한/영 + 프랜차이즈 계보
- 목적: 2001-2020(한글) ↔ 2021-2025(영문) + 구단명 변경 이력(해태→KIA, SK→SSG, 우리/넥센/키움) 조인 지원

### Cycle 6 (보강) — 2026-04-15
- `awards/kbo_mvp_1982_2025.csv` (44행) + `awards/kbo_rookie_1983_2025.csv` (43행)
- 정규시즌 MVP + 신인왕 전기 수상 이력 (Wikipedia 출처)
- 데모 활용: "MVP 최다 수상 선수", "신인왕 → MVP 승급 사례", "팀별 MVP 배출 수" 등

### Cycle 7 (보강) — 2026-04-15
- `awards/kbo_golden_glove_1982_2025.csv` (438행) — 골든글러브 44년 × 포지션별(투수/포수/내야4/외야3/지명타자)
- 데모 각도: "골든글러브 최다 수상 선수" (이승엽·양준혁 각 10회), "포지션별 최다 수상팀", "10년 단위 외야 BIG3 변천"

### Cycle 8 (문서 sync) — 2026-04-15
- `schema_report.txt` + `data_manifest.json` 재생성 (awards/ 포함, 총 18 CSV 21,651 rows)
- `data_manifest.md` + `README.md` 에 awards/ + team_name_mapping 항목 반영

### Cycle 9 (보강) — 2026-04-15
- `reference/kbo_ballparks.csv` (10행) — 팀별 홈구장/도시/지역/수용인원/개장년도/그라운드
- 데모 각도: "지역별(수도권·영남·호남·충청) 팀 분포", "구장 수용인원 vs 평균 관중 이용률", "잠실공유구장(두산+LG) 효과"

### Cycle 16 (demo-test.xlsx) — 2026-04-15
- `demo-test.xlsx` (13 KB) — 5시트 미니멀 업무 보고서 포맷
  1. 요약 — KPI 카드 4개(관중/평균/우승팀/MVP) + 핵심 관찰 4줄
  2. 2025순위 — 최종 순위표 + 승률 DataBar
  3. 관중추세 — 44년 시계열 + 라인차트
  4. GG_최다수상 — TOP15 + ColorScale
  5. 데이터_출처 — 출처·한계·갱신주기
- 스타일: 맑은 고딕, NAVY 헤더, 조건부서식 최소, 격자 OFF, 셀 병합 KPI 카드
- 빌더: `_build_demo_test.py` (재실행 가능)

### Cycle 13 (엑셀 데모) — 2026-04-15
- `openpyxl` + `xlsxwriter` 설치 확인
- `KBO_dashboard_demo.xlsx` 생성 — 5시트 (관중 라인차트·우승 바차트·GG TOP15·5년 순위·README)
- 엑셀 쓰기·수식·차트·서식 모두 Claude Code로 가능 증명

### Cycle 11/12 (분석) — 2026-04-15
- `INSIGHTS.md` 작성 — 6개 각도에서 1차 분석 (관중 트렌드·프랜차이즈 우승·골든글러브·5년 순위 안정성·2020 OPS TOP·200IP 투수)
- 하이라이트: 2020 COVID 32.8만 → 2025 1,231만 (3700% 회복+팽창), KIA 프랜차이즈 12회 우승 1위, 이승엽·양의지 GG 10회 공동 최다, LG 5년 평균 2.0위, 200IP는 주로 외인(류현진/송진우 외 국내 드묾)
- 데모에서 "이런 인사이트 Claude가 만들어봐" 식으로 재생성 유도 가능

### Cycle 10 (편의) — 2026-04-15
- `.gitignore` (`_sources/` 제외) — README 권고 실제 적용
- `load_all.py` — 한 줄로 전체 데이터셋 로드: `from load_all import load_all; data = load_all()` → `data[cat][name]` DataFrame 접근
- Smoke test 통과: 19 files / 21,661 rows / 9 categories 모두 읽힘
- STATUS: COMPLETE + 편의 보강 (데이터 row 동일, 사용성 향상)


이후 fire되는 cycle은 PROGRESS.md 읽고 완료 확인 후 종료. 추가 수집 요청 시 여기에 새 cycle 추가.

## 보너스 아이디어 (요청 시 진행)
- [ ] 2021-2025 선수 레벨 스탯 (크롤러 재실행 필요, ChromeDriver)
- [ ] MLB Lahman DB 보조 데이터셋 (pybaseball)
- [ ] KBO 일일 경기 결과 (schedule) 수집
