# UTIC 신호개방 데이터 공식 서비스 명세 반영

- 수령일: 2026-07-31 KST
- 제공기관: 도로교통공단 도시교통정보센터
- 자료: `CrossRoadInfoService.hwp`, `PlanCrossRoadInfoService.hwp`, `sig_code.hwp`
- 원본 HWP는 공개 저장소에 복제하지 않고 파일명과 SHA-256만 기록한다.

## 새로 확인된 실제 서비스

### 교차로 기반정보 파일 다운로드

- `CrossRoadInfoService/download/crossInfo`
  - 지역코드, 교차로번호, 교차로명, X/Y 좌표
- `CrossRoadInfoService/download/crossDetailInfo`
  - 맵번호, A/B링 현시별 방향설정코드

두 서비스는 JSON 조회가 아니라 지역별 XLSX/ZIP 다운로드형이다.

### 계획정보 API

- `getPlanCRHDInfo`: 특수일 계획
- `getPlanCRWDInfo`: 요일별 계획번호
- `getPlanCRRSInfo`: 예약제어 계획
- `getPlanCROPInfo`: 운영 시작시각, 주기, 옵셋, A/B링 1~8현시 값

### 시그널맵 API

- `SigMapCrossRoadInfoService/getSigMapCRInfo`
- 링번호, 계획구분, 스텝, 차량등 1~8, 보행등 1~8, 최소·최대시간, 현시종료 필드 제공

## 구현

- `utic_signal_service_contract.json`에 endpoint, 요청변수, 응답필드, 코드, 오류코드와 원본 해시를 기계판독 형태로 고정했다.
- `normalize_operating_plan_response()`는 주기·옵셋·A/B링 현시값을 정규화하고 각 링의 현시합과 주기 불일치를 QA 플래그로 남긴다.
- `normalize_signal_map_response()`는 차량등·보행등 8채널과 계획구분을 canonical 구조로 변환한다.
- `GET /api/reference/utic-signal-service-contract`로 React·백엔드 담당이 공식 계약을 조회할 수 있다.

## 실제 활용

가능:

- 외부 도시의 실제 신호계획 parser
- TOD·주기·옵셋·A/B링 현시 시각화
- crossDetailInfo와 SIGNALMAP을 결합한 이동류 의미 해석
- 온라인 API와 오프라인 fixture 동일성 검증

불가능:

- 인천·대구 신호값을 세종 신호값으로 사용
- 실시간 점등상태 또는 잔여시간으로 표현
- 시우가 단독으로 simulator runtime을 활성화
- provisional 안전·공정성 임계값 승인

## 남은 실제 수집

1. `crossInfo`와 `crossDetailInfo` XLSX/ZIP 다운로드
2. `getPlanCROPInfo` 샘플 JSON
3. `getSigMapCRInfo` 샘플 JSON
4. 동일 교차로의 기반정보·현시구성·요일계획·운영계획·시그널맵 조인 검증
5. 네트워크 차단 상태 fixture 재생

현재 문서만으로 schema와 parser는 구현 가능하지만, 실제 레코드 단위 기능검증은 위 원자료 수집 후 완료한다.
