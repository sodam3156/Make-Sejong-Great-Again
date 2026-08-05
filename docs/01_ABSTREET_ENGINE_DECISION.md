# A/B Street 엔진 채택 결정

상태: 2026-08-04 승인

## 결정

TATS는 **A/B Street headless 교통 시뮬레이션 + Unity UI Toolkit 게임 클라이언트** 구조를 채택한다.

- 승인됨: A/B Street의 지도·교통 시뮬레이션을 서버 권위 엔진 후보로 사용
- 승인됨: 별도 GitHub fork와 기준 commit·라이선스 고정
- 보류됨: 세종 지도 import와 신호 변경 E2E 기술 스파이크

보류된 스파이크는 대표의 추가 승인 전까지 착수하거나 완료로 간주하지 않는다.

## 고정된 소스

| 항목 | 값 |
|---|---|
| upstream | `a-b-street/abstreet` |
| TATS fork | `sodam3156/abstreet` |
| default branch | `main` |
| pinned commit | `0964f29315820c91b171b585eb51e300164e9197` |
| commit date | `2025-09-10T09:11:25Z` |
| license | Apache License 2.0 |
| license blob | `d645695673349e3947e8e5ae42332d0ac3164cd7` |

기계 판독 정본은 `third_party/abstreet.lock.json`이다.

## 아키텍처 경계

```text
OSM·세종 공개 도로 데이터
        ↓
A/B Street importer / map_model / sim
        ↓ JSON/HTTP
TATS game-v2 adapter
        ↓
Unity TATSGame
```

### A/B Street fork 책임

- OSM 지도 import와 차선·도로·교차로 모델
- 차량·보행자 이동과 신호 단계 실행
- 지체·대기·통과량·agent 위치 원시 결과
- headless 실행과 결정론에 필요한 seed·scenario

### TATS 저장소 책임

- 안정적인 `game-v2` adapter와 오류·버전·idempotency 계약
- 포인트 정산, 도로 개방, 건물 성장, 스킬북, AI 비교
- hard safety/soft risk 제품 규칙
- Unity 지도 표현, 진단 오버레이, UX와 로컬 저장

A/B Street의 불안정한 headless API를 Unity가 직접 호출하지 않는다. adapter가 upstream 형식을 격리하고 TATS 계약만 노출한다.

## 라이선스 경계

- A/B Street 코드는 Apache-2.0 고지와 기존 저작권 표시를 유지한다.
- 수정 파일은 fork에서 변경 사실을 표시한다.
- A/B Street 코드나 binary를 TATS 배포물에 포함할 때 전체 LICENSE를 함께 넣는다.
- OSM 데이터는 코드 라이선스와 별개로 ODbL 출처·라이선스 고지를 제공한다.

현재 TATS 저장소에는 A/B Street 소스나 binary를 vendoring하지 않았으며 fork와 commit만 고정했다.

## 보류된 스파이크의 향후 판단 항목

대표가 재개를 승인하면 별도 작업으로 다음만 검증한다.

1. 세종 소규모 경계 import 성공 여부
2. headless에서 신호 조회·변경·시간 진행·지체/통과량 조회
3. Unity adapter 왕복과 오프라인 Windows 패키징 비용
4. 복잡한 교차로·OSM 품질·gridlock 실패율

