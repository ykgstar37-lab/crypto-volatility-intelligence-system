# 개선 TODO

> 프로젝트 아쉬운 점 정리. 하나씩 체크하며 개선할 것.

---

## README 개선

- [ ] **영문 README 작성** — 최소한 영문 요약(About 섹션)이라도 추가. 외국계/글로벌 팀 지원 시 영문 README가 있으면 인상이 다르다.

## 프로젝트 기술 개선

- [ ] **TypeScript 전환** — 26개 컴포넌트에 PropTypes도 없어서 props 타입 실수 잡기 어려움.
- [ ] **접근성(a11y)** — aria-label, 시맨틱 HTML, 키보드 내비게이션 부족. WCAG 2.1 AA 기본 대응 필요.

## 프로세스 개선

- [ ] **이슈 기반 개발** — 위 항목들을 GitHub Issues로 등록하고, feature branch → PR → merge 워크플로우로 진행.
- [ ] **커밋 단위 쪼개기** — 기능 하나당 커밋 하나. v0.1.0처럼 전체 코드가 한 커밋에 들어가지 않도록.

---

<details>
<summary>완료된 항목</summary>

### README 개선
- [x] **재현 부록 작성** — 원자료로 6개 모형 재적합, 원문과 어긋나는 지점까지 기록해 docs/paper에 수록
- [x] **배포 데모 URL 추가** — Vercel(웹) + Render(API) + Neon(DB)로 배포하고 README 상단에 링크 배치 완료
- [x] **스크린샷 추가** — 메인 스크린샷 + 기능별 GIF 6개 인라인 배치 완료
- [x] **개발자 섹션 보강** — 이메일 추가, 영문 한 줄 소개 추가

### 프로젝트 기술 개선
- [x] **테스트 코드 작성** — pytest 28개 (GARCH 서비스, risk score, API 엔드포인트) 완료
- [x] **CI/CD 구축** — GitHub Actions (backend pytest + frontend lint) 완료
- [x] **.env.example 작성** — 환경변수 템플릿 파일 추가 완료
- [x] **캐시 TTL 전략** — 5분 TTL 인메모리 캐시 적용 (volatility, signal, leaderboard)
- [x] **멀티코인 전체 연동** — signal, leaderboard, accuracy, backtest에 coin 파라미터 추가 완료
- [x] **HAR-TGARCH-X 외생변수** — `arch_model(x=exog)` + `forecast(x=last_exog)`로 Volume/FNG 실제 전달
- [x] **AI 브리핑 일일 캐싱** — (date, lang) 키 기반, 하루 1회만 OpenAI 호출
- [x] **서버 콜드스타트** — `asyncio.create_task()`로 백필 비동기화, 서버 즉시 응답 가능
- [x] **Rate Limiting** — IP 기반 슬라이딩 윈도우 (브리핑 5/60s, 포트폴리오 10/60s)
- [x] **WebSocket exponential backoff** — 1s → 2s → ... → 60s, 연결 성공 시 리셋
- [x] **에러 핸들링 통일** — GARCH 응답에 `status` ("ok"/"error"/"no_data") + `error` 메시지 필드
- [x] **Monte Carlo 10K** — 1,000 → 10,000 시나리오 (99% VaR 꼬리 ~100개 샘플 확보)
- [x] **SQLite/PostgreSQL 호환** — database.py 자동 감지, PostgreSQL pool_size=10
- [x] **Alembic 마이그레이션** — 초기 스키마 마이그레이션 + init_db() 연동
- [x] **Docker/docker-compose** — PostgreSQL + Backend + Frontend/nginx 원커맨드 실행
- [x] **모바일 반응형** — 코인 셀렉터 전 화면 표시, 그리드 sm/lg 반응형 대응
- [x] **코드 스플리팅** — React.lazy() 7개 heavy 컴포넌트 (총 ~53KB 초기 번들에서 제외)
- [x] **상태 관리 Context** — AppProvider + useApp() hook, localStorage 영속화 (다크모드/언어)

### 프로세스 개선
- [x] **CI/CD 구축** — GitHub Actions로 테스트 자동 실행 + 린팅 완료

</details>
