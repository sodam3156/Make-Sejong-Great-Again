# 정보공개청구 회신 보관 규칙

정부·공공기관 회신이 도착하면 다음 구조로 원문을 추가한다.

```text
data/public/information_requests/
└─ <request_id>/
   ├─ response-original.<ext>
   ├─ attachments/
   └─ README.md
```

각 요청의 현재 상태와 내부 `request_id`는 [`docs/evidence/government_information_request_tracker_20260729.md`](../../../docs/evidence/government_information_request_tracker_20260729.md)에서 관리한다.

## 회신 추가 체크리스트

1. 접수번호·청구인 성명·전화번호·이메일·주소 등 개인정보가 보이면 공개 저장소용 사본에서 제거한다.
2. 기관 원문은 내용 변경 없이 보존하되 파일의 SHA-256을 기록한다.
3. `README.md`에 발신기관, 담당부서, 회신일, 자료 기준일, 공개·부분공개·비공개·부존재·이송 여부를 기록한다.
4. 회신의 기준일과 집계 단위를 확인한 뒤 팩트시트의 `[미확인]` 항목만 갱신한다.
5. 기관이 새로 작성하지 않은 기존 문서와 기관의 설명·의견을 구분한다.
6. 제어기 IP·계정·인증키·망 구성·취약점 등 보안정보가 포함되면 저장소에 올리지 않는다.
