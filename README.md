# CryptoVol Dashboard

> **GARCH 변동성 모형을 실시간 웹 서비스로 전환한 멀티코인 변동성 예측 대시보드**

## 스크린샷 & 데모

### 메인 대시보드

![메인 대시보드](image/cryptovol/cryptovol-main.png)
*BTC/ETH/SOL 실시간 가격, GARCH 변동성 예측, Risk Score, 공포탐욕지수를 한눈에 확인*

### 코인 전환 실시간 반응

<p align="center">
  <img src="image/cryptovol/coin-switch-eth.gif" width="49%" alt="ETH 전환" />
  <img src="image/cryptovol/coin-switch-sol.gif" width="49%" alt="SOL 전환" />
</p>

*BTC → ETH → SOL 탭 클릭 시 가격, 차트, 변동성 예측, 시그널 등 전체 대시보드 데이터가 실시간 전환*

### 매매 시그널 + 모형 정확도

![매매 시그널](image/cryptovol/cryptovol-signal.png)
*FNG + 변동성 추세 기반 매매 시그널(BUY/SELL/NEUTRAL)과 모형별 RMSE 리더보드*

### 포트폴리오 Monte Carlo 시뮬레이션

![포트폴리오 시뮬레이션](image/cryptovol/portfolio-sim.gif)
*BTC/ETH/SOL 비중 조절 → 투자금액·기간 설정 → Monte Carlo 시뮬레이션 실행 → VaR, Sharpe Ratio 결과 확인*

### 공포탐욕지수 + 변동성 비교

![FNG 차트](image/cryptovol/cryptovol-fng.png)
*Fear & Greed Index 게이지 및 추이 차트, 5개 GARCH 모형 변동성 비교*

### 다크모드 + AI 브리핑

![다크모드 AI 브리핑](image/cryptovol/dark-ai-briefing.gif)
*다크모드 전환 후 AI 마스코트 클릭 → GPT-4o-mini 기반 시장 브리핑 말풍선 표시*

<p align="center">
  <img src="image/cryptovol/cryptovol-darkmode.png" width="49%" alt="다크모드" />
  <img src="image/cryptovol/cryptovol-ai.png" width="49%" alt="AI 브리핑" />
</p>

### 포트폴리오 시뮬레이터 결과

![포트폴리오](image/cryptovol/cryptovol-portfolio.png)
*Monte Carlo 1,000회 시뮬레이션 히스토그램, VaR(95%/99%), Sharpe Ratio, 코인별 리스크 분해*

---

## 프로젝트 배경

P학기(통계 실무 프로젝트)에서 팀으로 비트코인 변동성을 GARCH 모형으로 분석했습니다. 팀에서는 CSV 데이터 기반 Jupyter 분석과 모형 비교를 수행했고, 이 프로젝트는 그 분석 결과를 **실시간 풀스택 웹 서비스로 확장한 개인 프로젝트**입니다.

| 구분 | P학기 (팀) | 이 프로젝트 (개인) |
|------|-----------|-------------------|
| 형태 | Jupyter 분석 + 논문 | 풀스택 웹 서비스 |
| 데이터 | CSV 정적 데이터 | CoinGecko API + Binance WebSocket 실시간 |
| 코인 | BTC 단일 | BTC / ETH / SOL 멀티코인 |
| 모형 | 수동 실행 | API 자동 서빙 + 정확도 추적 |
| 배포 | 로컬 | Render + Vercel 클라우드 |

**개인 확장에서 직접 설계·구현한 부분:**
- FastAPI + React 풀스택 아키텍처 설계
- Binance WebSocket 릴레이 서버 구현
- GARCH 모형 실시간 API 서빙 (캐싱, 에러 핸들링)
- Monte Carlo 포트폴리오 시뮬레이터
- 예측 정확도 트래커 / 매매 시그널 엔진 / 백테스트 시스템
- GPT-4o-mini 기반 AI 시장 브리핑
- 한/영 다국어, 다크모드, 가격 알림 등 전체 프론트엔드

---

## 핵심 기능과 기술적 의사결정

### 1. GARCH 모형 실시간 API 서빙

5개 GARCH 모형(GARCH, TGARCH, HAR-GARCH, HAR-TGARCH, HAR-TGARCH-X)으로 변동성을 예측합니다.

| 모형 | 특징 |
|------|------|
| GARCH(1,1) | 기본 조건부 분산 |
| TGARCH | 비대칭 레버리지 효과 (γ = 0.099) |
| HAR-GARCH | 단·중·장기(1/7/30일) 변동성 구조 |
| HAR-TGARCH | HAR + 비대칭 결합 |
| HAR-TGARCH-X | + 외생변수 (Volume, FNG) |

**기술적 결정**: Jupyter에서 수동 실행하던 모형을 API 요청마다 적합(fit)해야 했습니다. `arch` 라이브러리의 적합은 수십~수백ms가 걸리므로, 인메모리 캐싱으로 반복 호출을 방지하고 120일 윈도우로 입력을 제한했습니다. 개별 모형 실패 시 0.0을 반환하여 하나의 모형 실패가 전체 응답을 깨뜨리지 않도록 했습니다.

### 2. Binance WebSocket 실시간 스트리밍

BTC/ETH/SOL 실시간 거래가를 밀리초 단위로 표시합니다.

**기술적 결정**: 프론트엔드에서 Binance에 직접 연결하면 CORS와 키 노출 문제가 발생합니다. FastAPI WebSocket 엔드포인트가 Binance 스트림을 수신하고, Set 기반 클라이언트 추적으로 연결된 브라우저에 브로드캐스트하는 릴레이 구조를 설계했습니다. 죽은 연결은 브로드캐스트 루프에서 자동 제거되고, 연결 끊김 시 3초 후 자동 재연결합니다.

### 3. Monte Carlo 포트폴리오 시뮬레이터

BTC/ETH/SOL 비중을 조절하여 포트폴리오 리스크를 분석합니다.

**기술적 결정**: GARCH 예측 변동성을 기반으로 1,000개 시나리오의 Monte Carlo 시뮬레이션을 수행합니다. NumPy 행렬 연산(`df.values @ w_arr`)으로 가중 수익률을 효율적으로 계산하고, VaR(95%/99%), Sharpe Ratio, 코인별 리스크 분해, 상관행렬을 산출합니다.

### 4. AI 시장 브리핑

GPT-4o-mini가 가격 추세, FNG 지수, 변동성 상태를 종합하여 일일 시장 분석을 제공합니다.

**기술적 결정**: 7일/30일 롤링 통계를 컨텍스트로 구성하고, 구조화된 프롬프트(날씨 비유, 추세, 행동 추천)로 일관된 브리핑 포맷을 유지합니다. 한국어/영어 프롬프트를 분리하여 자연스러운 다국어 출력을 구현했습니다.

### 5. 예측 정확도 트래커 + 백테스트

모형별 예측 정확도를 60일 롤링 기준으로 시계열 추적하고, 날짜 범위를 선택하여 MSE, RMSE, MAE, MAPE, R² 성능 지표를 비교할 수 있습니다.

**기술적 결정**: 변동성 예측 서비스에서 가장 중요한 건 "어떤 모형이 지금 가장 정확한가"입니다. 최근 30일 롤링 기준 리더보드로 실시간 랭킹을 제공하고, 백테스트로 특정 시장 구간에서의 최적 모형을 탐색할 수 있게 했습니다.

---

## 기타 기능

| 기능 | 설명 |
|------|------|
| **매매 시그널** | FNG + 변동성 추세 + 가격 모멘텀 종합 (BUY/SELL/NEUTRAL), 적중률 추적 |
| **위험도 점수** | 5개 모형 가중평균 → 0~100 스코어 (Low/Moderate/High/Extreme) |
| **FNG + 거래량 차트** | Fear & Greed Index와 거래량 듀얼축 시각화 |
| **모형 인터랙티브 설명** | 각 GARCH 모형의 수식, 파라미터, 특징을 탭 형태로 설명 |
| **가격 알림** | 상한/하한 트리거 설정 → Toast 알림 |
| **리포트 다운로드** | 대시보드 현황 텍스트 파일 다운로드 |
| **한/영 전환** | 전체 UI 다국어 지원 |
| **다크/라이트 모드** | 테마 전환 지원 |
| **하단 플로팅 독** | 주요 기능 빠른 접근 바 |
| **API 디버그 로그** | 실시간 데이터 수집 상태 터미널 로그 |

---

## 기술 스택

### Backend
| 기술 | 용도 |
|------|------|
| **FastAPI** | REST API + WebSocket 서버 |
| **SQLAlchemy** | ORM (SQLite) |
| **arch** | GARCH 모형 적합 및 예측 |
| **APScheduler** | 일일 데이터 수집 스케줄러 |
| **httpx** | CoinGecko API 비동기 호출 |
| **websockets** | Binance WebSocket 스트림 수신 |
| **pandas / numpy / scipy** | 데이터 처리 및 통계 연산 |
| **OpenAI API** | GPT-4o-mini AI 브리핑 생성 |

### Frontend
| 기술 | 용도 |
|------|------|
| **React 19** | UI 프레임워크 |
| **Vite** | 빌드 도구 |
| **Tailwind CSS v4** | 스타일링 |
| **Recharts** | 차트 시각화 |
| **Axios** | API 통신 |

### Infra
| 기술 | 용도 |
|------|------|
| **Render** | 백엔드 배포 |
| **Vercel** | 프론트엔드 배포 |
| **SQLite** | 데이터베이스 |
| **Binance WebSocket** | 실시간 거래 데이터 소스 |

---

## 시스템 아키텍처

```
Binance WebSocket ──→ FastAPI Backend ──→ React Dashboard
(BTC/ETH/SOL ticks)    │                    │
                       │                    ├── 코인 셀렉터 (BTC/ETH/SOL)
CoinGecko API ────────→│                    ├── 실시간 가격 (WebSocket)
(가격, FNG, 거래량)     │                    ├── 변동성 예측 비교 차트
                       ├── SQLite DB        ├── Risk Gauge + Score
OpenAI API ───────────→├── GARCH Models     ├── 매매 시그널 + 적중률
(GPT-4o-mini)          ├── Risk Score       ├── 정확도 트래커
                       ├── Monte Carlo      ├── 포트폴리오 시뮬레이터
                       └── APScheduler      ├── AI 마스코트 브리핑
                         (일일 데이터)       └── 백테스트 + FNG 차트
```

---

## API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 확인 |
| GET | `/api/price/current?coin=BTC` | 현재 가격 + 24h 변동 + FNG |
| GET | `/api/price/multi` | BTC/ETH/SOL 전체 현재 가격 |
| GET | `/api/price/history?days=365&coin=BTC` | 일별 OHLCV + FNG + 로그수익률 |
| GET | `/api/volatility/predict?coin=BTC` | 5개 모형 변동성 예측 + 위험도 점수 |
| GET | `/api/volatility/compare?days=90&coin=BTC` | 예측 vs 실현 변동성 비교 |
| GET | `/api/volatility/accuracy?days=60&coin=BTC` | 모형별 예측 정확도 시계열 |
| GET | `/api/backtest?start=...&end=...&coin=BTC` | 기간별 백테스트 성능 지표 |
| GET | `/api/signal?coin=BTC` | 매매 시그널 |
| GET | `/api/signal/leaderboard?coin=BTC` | 모형 정확도 리더보드 |
| GET | `/api/signal/accuracy?coin=BTC` | 시그널 적중률 |
| GET | `/api/briefing?lang=ko` | AI 시장 브리핑 |
| POST | `/api/portfolio/simulate` | 포트폴리오 VaR + Monte Carlo |
| WS | `/ws/ticks` | Binance 실시간 틱 릴레이 |

---

## 빠른 시작

### Backend

```bash
cd backend
python -m venv venv
venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

서버 시작 시 자동으로 365일 BTC/ETH/SOL 데이터를 CoinGecko에서 백필합니다.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### 환경 변수 (.env)

```
DATABASE_URL=sqlite:///./data/crypto.db
CORS_ORIGINS=http://localhost:5173
OPENAI_API_KEY=sk-...    # AI 브리핑용 (선택)
```

---

## 통계적 근거

> P학기 팀 프로젝트에서 도출한 분석 결과로, 이 서비스의 모형 선택과 외생변수 활용의 이론적 근거입니다.

<details>
<summary>사전 검정 및 상관 분석 결과</summary>

### 사전 검정

| 검정 | 목적 | 결과 |
|------|------|------|
| ADF 검정 | 시계열 정상성 확인 | 로그수익률 정상 (p < 0.05) |
| ARCH-LM 검정 | 이분산성 확인 | ARCH 효과 존재 (p < 0.05) |
| 정규성 검정 | 수익률 분포 확인 | 정규성 기각 → 두터운 꼬리 |

### 상관 분석

| 변수 쌍 | 상관계수 | p-value |
|---------|---------|---------|
| BTC ↔ FNG | 0.72 | 2.2e-16 |
| BTC ↔ KOSPI | -0.03 | 0.98 |
| BTC ↔ NASDAQ | -0.05 | 0.84 |

### 핵심 발견
1. **TGARCH 레버리지 효과** (γ = 0.099): 하락 시 변동성이 상승 시보다 약 10% 더 증가
2. **HAR 구조**: 단기/중기/장기 변동성의 다중 스케일 분석이 예측력 향상
3. **FNG 지수**: BTC 가격과 유의미한 상관 (r = 0.72) → 외생변수 활용 근거

</details>

---

## 프로젝트 구조

<details>
<summary>디렉토리 구조</summary>

```
crypto-volatility-dashboard/
├── README.md
├── DEVLOG.md
├── RETROSPECTIVE.md
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── .env
│   └── app/
│       ├── main.py              # FastAPI 앱 + CORS + lifespan + WS 릴레이
│       ├── config.py            # 환경설정 (pydantic-settings)
│       ├── database.py          # SQLite + SQLAlchemy
│       ├── scheduler.py         # APScheduler 일일 데이터 수집 (BTC/ETH/SOL)
│       ├── models/
│       │   └── price.py         # coin_daily 테이블 ORM
│       ├── schemas/
│       │   └── volatility.py    # Pydantic 응답 모델
│       ├── services/
│       │   ├── coingecko.py     # CoinGecko API 클라이언트
│       │   ├── garch.py         # 5개 GARCH 모형 서비스
│       │   └── risk_score.py    # 위험도 점수 산출
│       └── routers/
│           ├── price.py         # /api/price
│           ├── volatility.py    # /api/volatility + 정확도 추적
│           ├── backtest.py      # /api/backtest
│           ├── signal.py        # /api/signal + 리더보드 + 적중률
│           ├── briefing.py      # /api/briefing (GPT-4o-mini)
│           ├── portfolio.py     # /api/portfolio Monte Carlo
│           └── ws.py            # /ws/ticks Binance WebSocket 릴레이
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── api/client.js
│       ├── i18n.js
│       ├── hooks/
│       │   └── useRealtimePrice.js
│       ├── components/          # 26개 컴포넌트
│       └── pages/
│           └── Dashboard.jsx
│
└── image/
    └── cryptovol/               # 스크린샷 + 데모 GIF
```

</details>

---

## 개발자

**윤경은 (Yoon Gyeongeun)**
- 가천대학교 응용통계학과
- P학기 팀 프로젝트 참여 → 개인 프로젝트로 확장
- GitHub: [@ykgstar37-lab](https://github.com/ykgstar37-lab)
