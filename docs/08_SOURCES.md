# 출처 목록

검증 기준일: 2026-07-29

## 1. 세종 ITS·스마트교차로

### 세종시 교통정보시스템

- URL: https://bis.sejong.go.kr/web/information/information_system.view
- 사용: CCTV·VDS·DSRC·VMS·BIS 등 기본 ITS 운영 체계
- 주의: 장비 보유와 고도화된 실시간 다교차로 자동제어는 구분해야 한다.

### 국토교통부 정책브리핑 — 스마트 모빌리티 서비스

- URL: https://www.korea.kr/multi/visualNewsView.do?newsId=148877347
- 사용: 1생활권 스마트교차로 14개소, 스마트횡단보도 10개소
- 주의: 2020년 실증사업 소개이며 2026년 현재 상시 운영범위는 별도 확인이 필요하다.

### 대전–세종 C-ITS 추진 경과

- URL: https://c-its.kr/introduction/history.do
- 사용: 세종이 C-ITS 실증 기반을 갖춘 도시라는 근거
- 주의: 운전자 정보제공·자율협력주행 실증과 신호 최적화 운영은 다른 기능이다.

## 2. 실시간 원격제어 운영 문제

### 세종의소리 — 346개 교차로 실시간 원격제어 문제

- URL: https://www.sjsori.com/news/articleView.html?idxno=83299
- 사용: 2020년 LH 이관, 실시간 원격제어 장애, 서버 노후화·데이터 동기화 중단, 현장 수동조작, 하드웨어 중심 유지보수
- 주의: 보도 내용이므로 세종시의회 회의록·예산자료와 교차 검증한다.

### 세종시의회 회의록·의정자료

- 2025년 문제 제기: https://council.sejong.go.kr/cms/mntsViewer.do?mntsId=6667
- 2026년 업무보고: https://council.sejong.go.kr/cms/mntsMmbrSimpleViewer.do?mntsId=6693&var08=MBR000064
- 2026년 교통국 업무보고: https://council.sejong.go.kr/cms/mntsViewer.do?mntsId=6785
- 의정소식지 PDF: https://council.sejong.go.kr/upload/councilnews/20260323035639202-04043.pdf
- 사용: 온라인 제어 시스템 운영 문제, 장비 조사, 신호체계 최적화 업무
- 주의: 346개와 366개 숫자는 집계 대상·시점이 다를 수 있으므로 발표에서 동일 집단처럼 합치지 않는다.

## 3. 교통 문제

### 국민권익위원회 세종 교통환경 조사

- URL: https://www.acrc.go.kr/boardDownload.es?bid=4A&list_no=82336&seq=2
- 사용: 불합리한 신호체계와 도로·노면표시 등 개선 필요 지점
- 주의: 조사 시점과 개선 완료 여부를 함께 확인한다.

## 4. 비교 사례

### SK텔레콤·화성시 AI 신호 최적화

- URL: https://news.sktelecom.com/196956
- 사용: 제한된 교차로 축에서 AI가 시간대별 신호주기를 산출·적용한 비교 사례
- 주의: 매 순간 자동으로 신호를 바꾸는 완전 폐루프 제어와 구분한다.

### 화성 AI 자율주행 허브

- URL: https://www.korea.kr/news/policyNewsView.do?newsId=148961129
- 사용: 정부·지자체·경찰·공공기관·민간 컨소시엄의 실도로 검증 구조

## 5. 연구기술

### KISTI 딥러닝 기반 다교차로 실시간 신호제어 기술

- 기술 소개: https://linkonbiz.com/tech/traffic-control-technology
- 관련 특허: 10-2296576, 10-2331746
- 사용: 여러 교차로 데이터를 분석해 신호 최적화를 시도하는 최신 연구 방향
- 주의: 기술소개 자료상 TRL 4 실험실 시제품 단계로 소개됐으며, 세종 도입 계약·기술이전·상용운영 근거는 확인되지 않았다.

## 6. 사실·추론·목표 표기 규칙

| 표기 | 의미 | 예시 |
|---|---|---|
| 확인 | 공식자료 또는 다수 자료로 검증 | 스마트교차로 14개소 실증 소개 |
| 보도 | 언론이 취재·보도 | 346개 교차로 원격제어 문제 |
| 추론 | 확인된 사실에서 팀이 도출 | 구축과 운영 사이 소프트웨어 공백 |
| 가설 | 인터뷰·데이터로 검증 필요 | 운영자가 후보 비교에 30초 이상 필요 |
| 목표 | 우리가 달성하려는 값 | 추천 생성 10초 이내 |
| 시뮬레이션 | 가상 환경 결과 | 평균 지체 13% 감소 |

발표와 화면에서 이 구분을 유지한다.

## 7. 2026-07-29 공개자료 원본 스냅샷

- [공개자료 인벤토리](./evidence/public_data_inventory_20260729.md)
- [정부·공공기관 자료요청 추적표](./evidence/government_information_request_tracker_20260729.md)
- [시우 Day 1·Day 2 근거·데이터 과업 기록](./evidence/siwoo_day1_day2_worklog_20260729.md)
- [원본 파일 디렉터리](../data/public/2026-07-29/)

원본 스냅샷은 교통량·신호 시설·API 계약·과거 도로구조 참고자료를 보존한다. 2023년 일회성 파일과 2017년 연구보고서를 2026년 실시간·실측값으로 사용하지 않으며, 실제 노드·링크 공간망과 최신 운영자료는 아직 미확보다.
