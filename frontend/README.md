# RainFlow Sejong 데모 화면

실행 정본은 정적 `frontend/index.html`이다. Node나 프론트 빌드 없이 동작한다.

## 데이터 모드

- FastAPI에서 열면 `POST /api/simulations`와 `GET /api/simulations/{run_id}`로 합성 결과를 계산한다. 성공 시 `result_source: live_simulation`을 표시한다.
- 백엔드가 검증된 저장 결과를 반환하면 `cached_simulation`을 표시한다.
- 백엔드 호출이 실패하거나 `index.html`을 `file://`로 직접 열면 `frontend/demo_run.js`의 검증된 fixture를 재생한다.
- 세 모드 모두 `synthetic-v0`, `provisional`이다. `live_simulation`은 실시간 세종 데이터를 썼다는 뜻이 아니라 실행 시점에 합성 큐 모델을 계산했다는 뜻이다.

7단계 `normal → rain_warning → spillback → policy_compare → safety_review → operator_approval → recovery_compare`가 3분 스케일로 자동 재생된다. live 모드에서 승인·거절 버튼은 실제 승인 API를 호출하고, 성공 후 저장된 run을 다시 조회해 적용 결과를 갱신한다.

## fixture 갱신

JSON이나 JavaScript를 직접 복사하지 않는다. 저장소 루트에서 다음 생성기를 사용한다.

```bash
python scripts/generate_contract_artifacts.py
python scripts/generate_contract_artifacts.py --check
```

이 명령은 백엔드 fixture·cache, `frontend/demo_run.js`, OpenAPI, 데모 대본, seed 검증자료와 동결 manifest를 같은 계산 결과에서 동기화한다.

## `src/` 상태

`frontend/src/`의 React 파일은 초기 구조 참고용이며 `package.json`이 없어 현재 실행·빌드 경로가 아니다. 제출 정본을 수정할 때는 `index.html`과 생성된 `demo_run.js`를 기준으로 한다.
