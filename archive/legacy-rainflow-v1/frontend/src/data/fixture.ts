import type { DemoRun } from '../types/demo';

// demo_run.js 가 window.DEMO_RUN 에 주입한 fixture 데이터
export const FIXTURE_DATA: DemoRun = (window as unknown as { DEMO_RUN: DemoRun }).DEMO_RUN;
