# CryptoVol Dashboard

[![CI](https://github.com/ykgstar37-lab/crypto-volatility-intelligence-system/actions/workflows/ci.yml/badge.svg)](https://github.com/ykgstar37-lab/crypto-volatility-intelligence-system/actions/workflows/ci.yml)

> **GARCH 변동성 모형을 실시간 웹 서비스로 전환한 멀티코인 변동성 예측 대시보드**
>
> *A real-time multi-coin volatility forecasting dashboard powered by GARCH models, Monte Carlo simulation, and AI market briefing.*

![메인 대시보드](image/cryptovol/cryptovol-main.png)

**출발점** — 이 프로젝트는 2023년 학술제 논문 *「암호화폐 변동성 비교 및 분석: GARCH 모델 기반 예측」*(3인 팀)에서
시작했습니다. 그 논문은 결론부에 두 가지를 한계로 적었습니다.

> "HAR-TGARCH-X와 같은 더 복잡한 결합 모형의 완전한 구현이 이루어지지 못한 점이 있다.
> 향후 연구에서는 … **실시간 예측 시스템으로의 발전을 모색할 필요가 있다.**"

이 저장소는 그 두 문장에 대한 답입니다. 논문이 공란으로 남긴 모형을 실제로 적합하고,
정적 분석을 상시 서빙되는 API로 옮겼습니다.
전문과 2026년 재현 부록은 [`docs/paper/`](docs/paper/)에 있습니다.

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

6개 GARCH 모형(GARCH, TGARCH, GARCH+E.V, HAR-GARCH, HAR-TGARCH, HAR-TGARCH-X)으로 변동성을 예측합니다.

| 모형 | 특징 |
|------|------|
| GARCH(1,1) | 기본 조건부 분산 |
| TGARCH | 비대칭 레버리지 효과 (γ = 0.099) |
| HAR-GARCH | 단·중·장기(1/7/30일) 변동성 구조 |
| HAR-TGARCH | HAR + 비대칭 결합 |
| HAR-TGARCH-X | + 외생변수 (Volume, FNG) |

**기술적 결정**: Jupyter에서 수동 실행하던 모형을 API 요청마다 적합(fit)해야 했습니다. `arch` 라이브러리의 적합은 수십~수백ms가 걸리므로, 인메모리 캐싱으로 반복 호출을 방지하고 120일 윈도우로 입력을 제한했습니다. HAR-TGARCH-X는 Volume/FNG을 `arch_model(x=exog)`로 mean equation에 실제 전달하며, 개별 모형 실패 시 `status: "error"` 응답으로 실패 원인을 투명하게 노출합니다.

![FNG + 변동성 비교](image/cryptovol/cryptovol-fng.png)
*Fear & Greed Index 게이지 및 추이 차트, 6개 GARCH 모형 변동성 비교*

### 2. 멀티코인 실시간 전환

BTC/ETH/SOL 탭 클릭 시 가격, 차트, 변동성 예측, 시그널, 리더보드 등 **전체 대시보드 데이터가 실시간 전환**됩니다. Binance WebSocket 릴레이로 밀리초 단위 실시간 거래가를 표시합니다.

<p align="center">
  <img src="image/cryptovol/coin-switch-eth.gif" width="49%" alt="ETH 전환" />
  <img src="image/cryptovol/coin-switch-sol.gif" width="49%" alt="SOL 전환" />
</p>

**기술적 결정**: 프론트엔드에서 Binance에 직접 연결하면 CORS와 키 노출 문제가 발생합니다. FastAPI WebSocket 엔드포인트가 Binance 스트림을 수신하고, Set 기반 클라이언트 추적으로 연결된 브라우저에 브로드캐스트하는 릴레이 구조를 설계했습니다. 연결 끊김 시 exponential backoff(1s → 2s → ... → 60s)로 재연결하여 장애 시 과도한 재연결을 방지합니다. 코인 전환 시 `Promise.all`로 API 호출을 병렬화하고, 5분 TTL 인메모리 캐시로 GARCH 재계산을 방지합니다.

### 3. 매매 시그널 + 예측 정확도 트래커

FNG + 변동성 추세 + 가격 모멘텀을 종합하여 매매 시그널(BUY/SELL/NEUTRAL)을 생성하고, 모형별 예측 정확도를 60일 롤링 기준으로 추적합니다.

![매매 시그널](image/cryptovol/cryptovol-signal.png)
*매매 시그널 스코어와 모형별 RMSE 리더보드*

**기술적 결정**: 변동성 예측 서비스에서 가장 중요한 건 "어떤 모형이 지금 가장 정확한가"입니다. 최근 30일 롤링 기준 리더보드로 실시간 랭킹을 제공하고, 백테스트로 특정 시장 구간에서의 최적 모형을 탐색할 수 있게 했습니다.

### 4. Monte Carlo 포트폴리오 시뮬레이터

BTC/ETH/SOL 비중을 조절하여 포트폴리오 리스크를 분석합니다.

![포트폴리오 시뮬레이션](image/cryptovol/portfolio-sim.gif)
*비중 조절 → 투자금액·기간 설정 → Monte Carlo 시뮬레이션 실행 → VaR, Sharpe Ratio 결과 확인*

**기술적 결정**: GARCH 예측 변동성을 기반으로 10,000개 시나리오의 Monte Carlo 시뮬레이션을 수행합니다. NumPy 행렬 연산(`df.values @ w_arr`)으로 가중 수익률을 효율적으로 계산하고, VaR(95%/99%), Sharpe Ratio, 코인별 리스크 분해, 상관행렬을 산출합니다. 10,000개 시나리오로 99% VaR 꼬리에 약 100개 샘플을 확보하여 tail risk 추정의 신뢰도를 높였습니다.

![포트폴리오 결과](image/cryptovol/cryptovol-portfolio.png)
*히스토그램, VaR(95%/99%), Sharpe Ratio, 코인별 리스크 분해*

### 5. 다크모드 + AI 시장 브리핑

GPT-4o-mini가 가격 추세, FNG 지수, 변동성 상태를 종합하여 일일 시장 분석을 제공합니다.

![다크모드 AI 브리핑](image/cryptovol/dark-ai-briefing.gif)
*다크모드 전환 후 AI 마스코트 클릭 → 시장 브리핑 말풍선 표시*

<p align="center">
  <img src="image/cryptovol/cryptovol-darkmode.png" width="49%" alt="다크모드" />
  <img src="image/cryptovol/cryptovol-ai.png" width="49%" alt="AI 브리핑" />
</p>

**기술적 결정**: 7일/30일 롤링 통계를 컨텍스트로 구성하고, 구조화된 프롬프트(날씨 비유, 추세, 행동 추천)로 일관된 브리핑 포맷을 유지합니다. 한국어/영어 프롬프트를 분리하여 자연스러운 다국어 출력을 구현했습니다. (date, lang) 키 기반 일일 캐싱으로 동일 날짜 내 OpenAI API 중복 호출을 방지합니다.

---

## 기타 기능

| 기능 | 설명 |
|------|------|
| **위험도 점수** | 6개 모형 평균 → 0~100 스코어 (Low/Moderate/High/Extreme) |
| **백테스트** | 날짜 범위 선택 → MSE, RMSE, MAE, MAPE, R² 성능 지표 비교 |
| **모형 인터랙티브 설명** | 각 GARCH 모형의 수식, 파라미터, 특징을 탭 형태로 설명 |
| **Rate Limiting** | IP 기반 슬라이딩 윈도우 — AI 브리핑 5req/60s, 포트폴리오 10req/60s |
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
| **SQLAlchemy + Alembic** | ORM + 스키마 마이그레이션 |
| **arch** | GARCH 모형 적합 및 예측 |
| **APScheduler** | 일일 데이터 수집 스케줄러 |
| **httpx** | CoinGecko API 비동기 호출 |
| **websockets** | Binance WebSocket 스트림 수신 (exponential backoff) |
| **pandas / numpy / scipy** | 데이터 처리 및 통계 연산 |
| **OpenAI API** | GPT-4o-mini AI 브리핑 생성 (일일 캐싱) |

### Frontend
| 기술 | 용도 |
|------|------|
| **React 19** | UI 프레임워크 (Context API 상태 관리) |
| **Vite** | 빌드 도구 |
| **Tailwind CSS v4** | 스타일링 (모바일 반응형) |
| **Recharts** | 차트 시각화 |
| **Axios** | API 통신 |
| **React.lazy + Suspense** | 코드 스플리팅 (7개 heavy 컴포넌트 지연 로딩) |

### Infra
| 기술 | 용도 |
|------|------|
| **Docker / docker-compose** | 원커맨드 로컬/프로덕션 실행 |
| **PostgreSQL** | 프로덕션 데이터베이스 (SQLite 개발용 호환) |
| **Render** | 백엔드 배포 |
| **Vercel** | 프론트엔드 배포 |
| **Binance WebSocket** | 실시간 거래 데이터 소스 |

---

## 시스템 아키텍처

### 전체 시스템 구조

```mermaid
graph TB
    subgraph External["외부 데이터 소스"]
        BN["Binance WebSocket<br/>BTC/ETH/SOL 실시간 틱"]
        CG["CoinGecko API<br/>가격 · FNG · 거래량"]
        OA["OpenAI API<br/>GPT-4o-mini"]
    end

    subgraph Docker["Docker Compose"]
        subgraph Backend["FastAPI Backend :8001"]
            WS["WebSocket 릴레이<br/>exponential backoff"]
            API["REST API<br/>14 endpoints"]
            RL["Rate Limiter<br/>IP 슬라이딩 윈도우"]
            SCH["APScheduler<br/>일일 0:05 UTC"]

            subgraph Services["서비스 레이어"]
                GARCH["GARCH 모형 서비스<br/>6개 모형 · 5분 TTL 캐시"]
                RISK["Risk Score<br/>0~100 점수"]
                SIG["Signal Engine<br/>BUY / SELL / NEUTRAL"]
                MC["Monte Carlo<br/>10,000 시나리오"]
                BRIEF["AI 브리핑<br/>일일 캐싱"]
            end
        end

        DB[("PostgreSQL / SQLite<br/>Alembic 마이그레이션<br/>coin_daily 테이블")]

        subgraph Frontend["React Frontend :80"]
            NGINX["Nginx 리버스 프록시"]
            subgraph SPA["React 19 SPA"]
                CTX["AppContext<br/>dark · lang · coin"]
                LAZY["React.lazy<br/>7개 컴포넌트"]
                DASH["Dashboard<br/>26개 컴포넌트"]
            end
        end
    end

    USER["사용자 브라우저"]

    BN -->|"wss://stream.binance.com"| WS
    CG -->|"HTTPS"| API
    CG -->|"HTTPS"| SCH
    OA -->|"HTTPS"| BRIEF

    SCH -->|"일일 백필"| DB
    API -->|"SQLAlchemy ORM"| DB
    GARCH --> DB
    WS -->|"broadcast"| NGINX

    API --> RL
    RL --> Services

    USER -->|"HTTP/WS"| NGINX
    NGINX -->|"/api/* /ws/*"| Backend
    NGINX -->|"/*"| SPA
    CTX --> DASH
    LAZY --> DASH
```

### 데이터 파이프라인

```mermaid
flowchart LR
    subgraph Ingestion["데이터 수집"]
        A1["서버 시작<br/>asyncio.create_task"] -->|"비동기 백필"| A2["365일 히스토리<br/>BTC → ETH → SOL"]
        A3["APScheduler<br/>매일 0:05 UTC"] -->|"일일 수집"| A4["최근 2일 데이터<br/>+ FNG 지수"]
    end

    subgraph Storage["저장"]
        DB[("coin_daily<br/>symbol · date · close<br/>volume · fng · log_return")]
    end

    subgraph Processing["처리 & 서빙"]
        G1["GARCH(1,1)"]
        G2["TGARCH"]
        G3["HAR-GARCH"]
        G4["HAR-TGARCH"]
        G5["HAR-TGARCH-X<br/>+ Volume, FNG 외생변수"]
        CACHE["인메모리 캐시<br/>5분 TTL"]
    end

    subgraph Output["출력"]
        O1["변동성 예측<br/>일간 σ · 연간화"]
        O2["Risk Score<br/>0~100"]
        O3["매매 시그널<br/>BUY/SELL/NEUTRAL"]
        O4["백테스트<br/>MSE · RMSE · R²"]
        O5["포트폴리오 VaR<br/>95% · 99%"]
    end

    A2 --> DB
    A4 --> DB
    DB -->|"60일 윈도우"| G1 & G2 & G3 & G4 & G5
    G1 & G2 & G3 & G4 & G5 --> CACHE
    CACHE --> O1 & O2 & O3 & O4 & O5
```

### 실시간 WebSocket 흐름

```mermaid
sequenceDiagram
    participant B as Binance Stream
    participant S as FastAPI WS 릴레이
    participant C1 as 클라이언트 1
    participant C2 as 클라이언트 2

    S->>B: connect(btcusdt@trade, ethusdt@trade, solusdt@trade)
    B-->>S: {"s":"BTCUSDT", "p":"87445.12", "T":1711468800000}

    par Broadcast
        S->>C1: {"type":"tick","symbol":"BTC","price":87445.12}
        S->>C2: {"type":"tick","symbol":"BTC","price":87445.12}
    end

    Note over S: latest[symbol] 캐시 업데이트

    C2->>S: 새 클라이언트 연결
    S->>C2: 캐시된 최신 가격 즉시 전송

    B--xS: 연결 끊김
    Note over S: exponential backoff<br/>1s → 2s → 4s → ... → 60s
    S->>B: 재연결
```

### GARCH 모형 비교

```mermaid
graph LR
    subgraph Input["입력 데이터"]
        R["로그수익률<br/>60일 윈도우"]
        V["거래량<br/>z-score 정규화"]
        F["FNG 지수<br/>0~100"]
    end

    subgraph Models["6개 GARCH 모형"]
        M1["GARCH(1,1)<br/>기본 조건부 분산<br/>σ²ₜ = ω + αε²ₜ₋₁ + βσ²ₜ₋₁"]
        M2["TGARCH<br/>비대칭 레버리지<br/>+ γε²ₜ₋₁·I(εₜ₋₁<0)"]
        M3["HAR-GARCH<br/>다중 스케일<br/>RV(1d, 7d, 30d)"]
        M4["HAR-TGARCH<br/>HAR + 비대칭"]
        M5["HAR-TGARCH-X<br/>+ 외생변수(Volume, FNG)"]
    end

    subgraph Output["출력"]
        S1["일간 σ"]
        S2["연간화 σ × √365"]
        S3["status: ok / error"]
    end

    R --> M1 & M2 & M3
    R --> M4 & M5
    V --> M5
    F --> M5
    M1 & M2 & M3 & M4 & M5 --> S1 --> S2
    M1 & M2 & M3 & M4 & M5 --> S3

    style M5 fill:#e8f4fd,stroke:#2b4fcb
```

### 프론트엔드 컴포넌트 구조

```mermaid
graph TB
    subgraph Context["전역 상태 (AppContext)"]
        STATE["lang · dark · coin<br/>localStorage 영속화"]
    end

    subgraph Layout["레이아웃"]
        SIDE["Sidebar<br/>데스크톱 + 모바일 햄버거"]
        HEAD["Header<br/>코인 셀렉터 · 다크모드 · 언어"]
    end

    subgraph Eager["즉시 로드 (초기 번들)"]
        SC["StatCard ×4"]
        PC["PriceChart"]
        FG["FngGauge"]
        RS["RiskScore"]
        SIG["SignalCard"]
        LB["Leaderboard"]
    end

    subgraph Lazy["지연 로드 (React.lazy)"]
        VC["VolatilityChart<br/>3KB"]
        AT["AccuracyTracker<br/>11KB"]
        PS["PortfolioSimulator<br/>8KB"]
        BP["BacktestPanel<br/>5KB"]
        ME["ModelExplainer<br/>7KB"]
        BD["BottomDock<br/>14KB"]
        AI["AiMascot<br/>4KB"]
    end

    STATE --> Layout
    STATE --> Eager
    STATE --> Lazy
    HEAD --> SIDE

    style Lazy fill:#f0f7ff,stroke:#2b4fcb,stroke-dasharray: 5 5
```

---

## 빠른 시작

### Docker (권장)

```bash
# 전체 스택 실행 (PostgreSQL + Backend + Frontend)
docker compose up --build

# 브라우저에서 http://localhost 접속
```

### 수동 설치

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Mac / Linux
venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

서버 시작 시 백그라운드로 365일 BTC/ETH/SOL 데이터를 CoinGecko에서 백필합니다 (서버는 즉시 응답 가능).

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

### 환경 변수

백엔드와 프론트엔드 각각 `.env.example`을 복사합니다.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

**backend/.env**

```
# SQLite (개발용) 또는 PostgreSQL (프로덕션)
DATABASE_URL=sqlite:///./data/crypto.db
# DATABASE_URL=postgresql://cryptovol:cryptovol@localhost:5432/cryptovol

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CORS_ORIGIN_REGEX=       # Vercel preview 도메인 정규식 (선택)
OPENAI_API_KEY=sk-...    # AI 브리핑용 (선택)
```

**frontend/.env**

```
VITE_API_URL=    # 비우면 vite 프록시(localhost:8001) 사용
VITE_WS_URL=     # 비우면 ws://<현재 호스트> 폴백
```

### Alembic 마이그레이션

```bash
cd backend
alembic upgrade head                          # 스키마 적용
alembic revision --autogenerate -m "변경 설명"  # 새 마이그레이션 생성
```

---

## 배포

프론트엔드는 Vercel(정적 호스팅), 백엔드는 Render(상시 프로세스)로 **분리 배포**합니다.

### 왜 백엔드를 서버리스에 올리지 않는가

이 프로젝트의 백엔드는 요청 사이에도 프로세스가 살아 있어야 동작합니다. 서버리스 함수는 요청 단위로 뜨고 사라지므로 아래 네 가지가 모두 깨집니다.

| 구성 요소 | 서버리스에서 깨지는 이유 |
|---|---|
| `routers/ws.py` — `/ws/ticks` + Binance 릴레이 | 서버리스 함수는 WebSocket 서버를 유지할 수 없음 |
| `main.py` lifespan — APScheduler 일일 크론, 365일 백필 | 요청이 없는 동안 실행될 프로세스가 없음 |
| `database.py` — SQLite 파일 DB | 파일시스템이 휘발성이라 백필 데이터가 매번 소실 |
| GARCH 5분 TTL 캐시, IP 기반 rate limit | 프로세스 전역 메모리 상태 → 인스턴스가 분산되면 무효화 |

### 백엔드 — Render

루트의 `render.yaml` Blueprint를 사용합니다. `backend/Dockerfile`로 빌드되며, `/api/health`로 헬스체크합니다.

설정할 환경 변수:

| 변수 | 값 |
|---|---|
| `DATABASE_URL` | Neon/Supabase 등 외부 PostgreSQL 연결 문자열 |
| `CORS_ORIGINS` | Vercel 프로덕션 도메인 |
| `CORS_ORIGIN_REGEX` | `https://cryptovol-.*\.vercel\.app` (preview 배포 허용, 선택) |
| `COINGECKO_API_KEY` | CoinGecko Demo 키 — 무료지만 배포 환경에서는 사실상 필수 |
| `OPENAI_API_KEY` | AI 브리핑용 (선택) |

> **CoinGecko 키가 왜 필요한가** — 무료 API는 IP 기반으로 쿼터를 매기는데, 클라우드 PaaS의 공용 IP는 차단되거나 강하게 rate-limit 됩니다. 로컬에서 잘 되던 백필이 배포 후 `no_data`로 끝나는 원인이 이것입니다. [개발자 대시보드](https://www.coingecko.com/en/developers/dashboard)에서 무료로 발급받아 넣으면 키 기반 쿼터로 전환됩니다.

> **무료 플랜 주의** — persistent disk가 없어 SQLite는 재시작마다 소실되므로 외부 PostgreSQL이 필요합니다. 또한 15분 유휴 시 슬립되며, 깨어날 때 365일 백필이 다시 실행되고 WebSocket 연결이 끊깁니다.

### 프론트엔드 — Vercel

Root Directory를 `frontend`로 지정하면 `frontend/vercel.json`이 적용됩니다 (Vite 빌드 + SPA rewrite).

| 변수 | 값 |
|---|---|
| `VITE_API_URL` | `https://<render-app>.onrender.com` |
| `VITE_WS_URL` | `wss://<render-app>.onrender.com` |

> **`wss://`를 반드시 사용할 것** — `VITE_WS_URL`을 비워두면 `ws://<현재 호스트>`로 폴백하는데, HTTPS 페이지에서 `ws://`는 브라우저가 mixed content로 차단합니다. 에러 없이 실시간 시세만 조용히 멈추므로 알아채기 어렵습니다.

---

## API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health` | 서버 상태 확인 |
| GET | `/api/price/current?coin=BTC` | 현재 가격 + 24h 변동 + FNG |
| GET | `/api/price/multi` | BTC/ETH/SOL 전체 현재 가격 |
| GET | `/api/price/history?days=365&coin=BTC` | 일별 OHLCV + FNG + 로그수익률 |
| GET | `/api/volatility/predict?coin=BTC` | 6개 모형 변동성 예측 + 위험도 점수 |
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

## 통계적 근거

> 이 서비스는 2023년 학술제 논문([`docs/paper/`](docs/paper/))에서 출발했습니다. 그 논문은 기간 제약으로
> GARCH·TGARCH·TGARCH+E.V 3개까지만 실제 적합했고, Table 7의 GARCH+E.V·HAR-GARCH·HAR-TGARCH는
> 공란으로 남았습니다. 본문에 서술된 R²와 상관계수는 뒷받침하는 표가 유실되어 인용만으로는 검증할 수 없습니다.
>
> 그래서 **인용 대신 재계산**했습니다. 아래 수치는 보관된 원자료(2018-02-01 ~ 2023-11-30, 2,129일)로
> 다시 계산한 값입니다. 모형 추정치 재현은 논문 PDF의 **부록 A**에 있습니다.

<details>
<summary>사전 검정 및 상관 분석 (재계산 결과)</summary>

### 사전 검정

| 검정 | 대상 | 통계량 | p-value | 판정 |
|------|------|--------|---------|------|
| ADF | 원가격 | -1.3792 | 0.5922 | 비정상 → 로그수익률 변환 근거 |
| ADF | 로그수익률 | -21.6388 | < 1e-16 | 정상 |
| Jarque-Bera | 로그수익률 | 142,976.8 | < 1e-16 | 정규성 기각 |
| ARCH-LM (lag 1) | 로그수익률 | 4.730 | 0.0296 | ARCH 효과 있음 |
| ARCH-LM (lag 12) | 로그수익률 | 11.448 | 0.4910 | ARCH 효과 없음 |

왜도 -2.5402, 초과첨도 39.9210으로 **두터운 꼬리가 뚜렷합니다.** 모든 모형에 t분포를 쓰는 근거입니다.

ADF 원가격 결과는 논문 서술(p=0.596035)과 사실상 일치합니다. 반면 **ARCH-LM은 시차 선택에 민감해
lag 1에서만 유의**하며, 논문이 보고한 p=0.000317은 어떤 시차에서도 재현되지 않았습니다.

### 상관 분석 (BTC 로그수익률 기준, n=2,129)

| 변수 쌍 | r | p-value | 논문 서술 |
|---------|---|---------|-----------|
| BTC ↔ FNG | 0.0550 | 1.11e-02 | 0.72 — **재현되지 않음** |
| BTC ↔ KOSPI | 0.0017 | 0.938 | -0.03 (무상관 결론 일치) |
| BTC ↔ NASDAQ | -0.0272 | 0.209 | -0.05 (무상관 결론 일치) |
| BTC ↔ S&P500 | -0.0894 | 3.60e-05 | — |

### 모형 추정치 재현

원 분석 코드(`CODE(수정).pdf`)에 기록된 사양 — 로그수익률 ×10, 정규분포 — 을 그대로 따르면
논문이 보고한 TGARCH 모수가 소수점 셋째 자리까지 재현됩니다.

| | ω | α | γ | β |
|---|---|---|---|---|
| 원 코드 보고값 | 0.009384 | 0.0538 | 0.0990 | 0.8351 |
| 재현값 | 0.009392 | 0.0540 | 0.0986 | 0.8350 |

**γ가 양수로 재현되어 레버리지 효과 결론은 뒷받침됩니다.** 다만 오차분포를 Student-t로 바꾸면
γ가 −0.017로 부호가 뒤집힙니다. 초과첨도가 39.9인 자료라 t분포가 통계적으로 더 적절할 수 있으므로,
이 결론을 인용할 때는 분포 가정을 함께 밝히는 편이 안전합니다.

### 재검증 결론

1. **전통 금융시장과 무관하다는 논문의 결론은 유지됩니다.** KOSPI·NASDAQ 모두 유의하지 않았습니다.
2. **레버리지 효과 결론도 원 사양에서 재현됩니다.** 단, 분포 가정에 민감합니다.
3. **FNG가 강하게 상관한다는 주장(0.72)은 재현되지 않습니다.** 로그수익률 기준 0.055이고,
   원가격으로 올려도 0.273, FNG 30일 이동평균과 비교해도 0.329에 그칩니다.
4. 그럼에도 외생변수는 유지합니다. 최근 데이터(2025-09 ~ 2026-09)에서는
   **거래량 ↔ 절대수익률이 0.5198 (p=1.4e-26)로 가장 강했습니다.**
   `GET /api/volatility/factors`가 이 값을 요청마다 다시 계산합니다.

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
├── docker-compose.yml           # PostgreSQL + Backend + Frontend
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini              # Alembic 설정
│   ├── alembic/                 # 스키마 마이그레이션
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── main.py              # FastAPI 앱 + 비동기 백필 + WS 릴레이
│       ├── config.py            # 환경설정 (pydantic-settings)
│       ├── database.py          # SQLite/PostgreSQL 자동 감지
│       ├── scheduler.py         # APScheduler + Alembic 마이그레이션
│       ├── models/
│       │   └── price.py         # coin_daily 테이블 ORM
│       ├── schemas/
│       │   └── volatility.py    # Pydantic 응답 모델 (status 필드 포함)
│       ├── services/
│       │   ├── coingecko.py     # CoinGecko API 클라이언트
│       │   ├── garch.py         # 6개 GARCH 모형 (외생변수 포함)
│       │   ├── risk_score.py    # 위험도 점수 산출
│       │   └── rate_limit.py    # IP 기반 슬라이딩 윈도우 Rate Limiter
│       └── routers/
│           ├── price.py         # /api/price
│           ├── volatility.py    # /api/volatility + 정확도 추적
│           ├── backtest.py      # /api/backtest
│           ├── signal.py        # /api/signal + 리더보드 + 적중률
│           ├── briefing.py      # /api/briefing (일일 캐싱)
│           ├── portfolio.py     # /api/portfolio Monte Carlo (10K)
│           └── ws.py            # /ws/ticks (exponential backoff)
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf               # SPA + API 리버스 프록시
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── api/client.js
│       ├── i18n.js
│       ├── context/
│       │   ├── AppContext.jsx    # 전역 상태 Provider
│       │   └── appContextValue.js
│       ├── hooks/
│       │   ├── useRealtimePrice.js
│       │   └── useApp.js        # Context hook
│       ├── components/          # 26개 컴포넌트 (7개 lazy-loaded)
│       └── pages/
│           └── Dashboard.jsx
│
└── image/
    └── cryptovol/               # 스크린샷 + 데모 GIF
```

</details>

---

## 회고

Jupyter 분석을 실시간 서비스로 전환하면서 **분석 코드와 서비스 코드의 차이**를 체감했습니다.

- GARCH 적합 시간, 예외 전파, 동시 요청 등 Notebook에서는 고려하지 않았던 문제들을 해결
- WebSocket 연결 수명주기와 exponential backoff 등 REST와 다른 사고방식을 경험
- 여러 모형이 동시에 틀리는 상황을 보며, `status` 필드로 모형의 한계를 투명하게 노출하는 설계 학습
- Docker/Alembic/Rate Limiting 등 프로덕션 인프라 구축 과정에서 운영 관점의 설계 경험
- React Context + 코드 스플리팅으로 프론트엔드 상태 관리와 성능 최적화 실습

> 상세 회고는 [RETROSPECTIVE.md](RETROSPECTIVE.md)를 참고해 주세요.

---

## 개발자

**윤경은 (Yoon Gyeongeun)**
- 가천대학교 응용통계학과
- P학기 팀 프로젝트 참여 → 개인 프로젝트로 확장
- GitHub: [@ykgstar37-lab](https://github.com/ykgstar37-lab)
- Email: yge0307@gmail.com
