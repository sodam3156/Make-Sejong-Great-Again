# RainFlow Sejong 데모 화면

`index.html`을 더블클릭해서 브라우저로 열면 됩니다 (인터넷 연결 불필요, 서버 불필요).

`backend/fixtures/demo_run.json`의 고정 데이터를 `demo_run.js`에 복사해 `window.DEMO_RUN`으로 로드하므로 `file://`로 열어도 정상 동작합니다. 7단계(normal → rain_warning → spillback → policy_compare → safety_review → operator_approval → recovery_compare)가 3분 스케일로 자동 재생되며, 상단 버튼으로 수동 이동도 가능합니다.

fixture를 갱신하려면 `backend/fixtures/demo_run.json`을 `demo_run.js`에 `window.DEMO_RUN = {...};` 형태로 다시 복사하세요.
