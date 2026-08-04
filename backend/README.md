# TATS backend

현재 루트에는 실행 가능한 RainFlow backend를 유지하지 않는다. TATS backend는 승인된 A/B Street headless 엔진을 `game-v2` adapter 뒤에 격리한다. 세종 기술 스파이크는 대표 결정 전까지 보류한다.

## 책임

- master tick과 city clock
- SignalPlan 검증·영향 미리보기·적용 예약·안전 전환
- OverlaySnapshot 생성
- 포인트 정산, 도로 개방, 개별 건물 성장
- 선택 알고리즘의 AI 초안과 비교 기록
- 저장/재개용 버전·seed·map version 기록
- A/B Street pinned commit과 headless 응답 버전을 TATS 계약으로 변환

## 플레이 가능 지도

`content/map_eojin_playable.json` — 시뮬레이션이 도는 그래프다. Unity의
`StreamingAssets/map/eojin_map.json`(도로 884개)은 **표시 전용**이고 이 파일과 역할이 다르다.

교차로 11곳(4지), 도로 링크 28개, 경계 유입·유출구 14개, 건물 33개를 담는다.
교차로마다 접근로 4개, 회전 이동 12개, 교차상충 16쌍과 상충 없는 기본 신호 계획이 들어 있다.

```bash
python scripts/build_playable_map.py && python -m pytest backend/tests -q
```

공개 표준노드링크에서 오는 것은 **도로 형상과 연결 관계뿐**이다. 회전 이동·신호 현시·
교통량·건물 수요는 게임용 합성값이며 `realityLevel` 필드로 구분해 표시한다.
같은 입력이면 같은 바이트가 나오므로 `mapVersion`으로 결정론을 보장할 수 있다.

## 첫 구현 게이트

1. 대표가 보류한 세종 기술 스파이크의 착수 여부 결정
2. 논리 계약의 필드·단위·오류 상태 승인
3. OpenAPI와 JSON Schema 생성
4. 같은 입력·seed 결정론 테스트
5. 직접 편집과 AI 초안의 동일 검증 경로 테스트
6. 연결 끊김·중복 명령·stale tick 거부 테스트

과거 구현은 `archive/legacy-rainflow-v1/backend/`에 있으며 현재 import 경로로 사용하지 않는다.
A/B Street fork와 기준 SHA는 `third_party/abstreet.lock.json`을 따른다.
