# 개선 TODO

> 프로젝트 아쉬운 점 정리. 하나씩 체크하며 개선할 것.

---

## README 개선

- [x] **스크린샷 추가** — 메인 스크린샷 + 기능별 GIF 6개 인라인 배치 완료
- [ ] **배포 데모 URL 추가** — Render + Vercel URL을 README 상단에 배치. 라이브 데모가 없으면 "배포했다"는 말이 신뢰를 얻지 못한다.
- [ ] **영문 README 작성** — 최소한 영문 요약(About 섹션)이라도 추가. 외국계/글로벌 팀 지원 시 영문 README가 있으면 인상이 다르다.
- [ ] **개발자 섹션 보강** — 이메일, 블로그, 한 줄 자기소개 추가. GitHub 링크만으로는 부족하다.

## 프로젝트 기술 개선

- [x] **테스트 코드 작성** — pytest 28개 (GARCH 서비스, risk score, API 엔드포인트) 완료
- [x] **CI/CD 구축** — GitHub Actions (backend pytest + frontend lint) 완료
- [x] **.env.example 작성** — 환경변수 템플릿 파일 추가 완료
- [x] **캐시 TTL 전략** — 5분 TTL 인메모리 캐시 적용 (volatility, signal, leaderboard)
- [x] **멀티코인 전체 연동** — signal, leaderboard, accuracy, backtest에 coin 파라미터 추가 완료
- [ ] **HAR-TGARCH-X 외생변수 수정** — 현재 코드에서 Volume/FNG가 실제로 `arch_model()`에 전달되지 않음. 모형 이름과 실제 구현이 불일치.
- [ ] **AI 브리핑 캐싱** — 매 요청마다 OpenAI API 호출 중. 일일 1회 생성 후 캐싱하면 비용 절감 + 응답 속도 개선.
- [ ] **WebSocket 지수 백오프** — 현재 고정 3초 재연결. 지수 백오프(exponential backoff)로 전환하여 장애 시 과도한 재연결 방지.
- [ ] **Monte Carlo 시나리오 수 증가** — 1,000개는 99% VaR 꼬리에 ~10개 샘플. 10,000개 이상 + t-분포 적용 필요.
- [ ] **서버 콜드스타트 개선** — 365일 백필이 서버 시작을 블로킹. 백그라운드 태스크로 전환 + health check에서 데이터 준비 상태 노출.
- [ ] **에러 핸들링 통일** — GARCH는 0.0 반환, 브리핑은 에러 문자열, 스케줄러는 로그만 남김. HTTPException + 구조화된 에러 응답 포맷으로 통일 필요.
- [ ] **인증/Rate Limiting 추가** — 모든 엔드포인트가 공개 상태. 최소한 AI 브리핑, 포트폴리오 API에 rate limit 또는 API 키 인증.
- [ ] **SQLite → PostgreSQL 전환 검토** — SQLite는 단일 인스턴스 한정. 동시 쓰기가 필요해지면 PostgreSQL 또는 TimescaleDB.
- [ ] **Docker/docker-compose** — `venv + pip install` 대신 `docker-compose up` 한 줄로 실행 가능하게. 면접관이 바로 돌려볼 수 있음.
- [ ] **Alembic 마이그레이션** — 현재 `create_all()`로 테이블 생성. 스키마 변경 시 데이터 손실 위험. Alembic으로 버전 관리 필요.
- [ ] **모바일 대응** — 코인 셀렉터가 `hidden lg:flex`라 모바일에서 코인 전환 불가. 햄버거 메뉴 또는 모바일 탭 추가 필요.
- [ ] **TypeScript 전환** — 26개 컴포넌트에 PropTypes도 없어서 props 타입 실수 잡기 어려움.
- [ ] **프론트엔드 코드 스플리팅** — React.lazy() + Suspense로 26개 컴포넌트 지연 로딩. 초기 번들 사이즈 줄이기.
- [ ] **접근성(a11y)** — aria-label, 시맨틱 HTML, 키보드 내비게이션 부족. WCAG 2.1 AA 기본 대응 필요.

## 프로세스 개선

- [ ] **이슈 기반 개발** — 위 항목들을 GitHub Issues로 등록하고, feature branch → PR → merge 워크플로우로 진행.
- [ ] **커밋 단위 쪼개기** — 기능 하나당 커밋 하나. v0.1.0처럼 전체 코드가 한 커밋에 들어가지 않도록.
- [x] **CI/CD 구축** — GitHub Actions로 테스트 자동 실행 + 린팅 완료.
