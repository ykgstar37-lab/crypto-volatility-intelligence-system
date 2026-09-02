export const translations = {
    en: {
        title: 'Real-Time Bitcoin Volatility Dashboard',
        subtitle: 'Real-time volatility prediction and market sentiment analysis based on 6 GARCH models',
        btcPrice: 'Bitcoin Price',
        volume: '24h Volume',
        fngIndex: 'FNG Index',
        riskScore: 'Risk Score',
        live: 'Live',
        // Price Chart
        priceTitle: 'Bitcoin Price',
        // FNG
        fngGaugeTitle: 'Fear & Greed Index',
        fngChartTitle: 'Fear & Greed Index',
        fngChartDesc: 'CMC Crypto Fear & Greed trend',
        extremeFear: 'Extreme Fear',
        fear: 'Fear',
        neutral: 'Neutral',
        greed: 'Greed',
        extremeGreed: 'Extreme Greed',
        // Volatility
        volTitle: 'Volatility Model Comparison',
        volDesc: 'Rolling daily predicted volatility comparison (annualized, %)',
        // Log Returns
        logReturnsTitle: 'Daily Log Returns',
        logReturnsDesc: 'Last 60 days daily log returns (%)',
        // Model Table
        modelDetailTitle: 'Model Predictions Detail',
        modelCol: 'Model',
        dailySigma: 'Daily σ',
        annualVol: 'Annualized Vol',
        // Signal
        signalTitle: 'Trading Signal',
        strongSell: 'Strong Sell',
        strongBuy: 'Strong Buy',
        notFinancialAdvice: '※ This is not financial advice. Based on GARCH model analysis only.',
        // Leaderboard
        leaderboardTitle: 'Model Accuracy Leaderboard',
        leaderboardDesc: 'Prediction accuracy ranking based on last 30 days (lower RMSE = better)',
        basedOn: 'Based on',
        rollingPredictions: 'rolling predictions over last 30 days',
        // Backtest
        backtestTitle: 'Backtest',
        backtestDesc: 'Compare model performance by period (select dates and Run)',
        runBacktest: 'Run Backtest',
        running: 'Running...',
        bestModel: 'Best performing model in this period:',
        notEnoughData: 'Not enough data. Please select a period of at least 60 days.',
        // API Log
        apiLogTitle: 'API Debug Log',
        apiLogDesc: 'Real-time data collection status',
        // Footer
        footer1: 'Data from CoinGecko & Alternative.me · GARCH models via arch Python package',
        footer2: 'Extended from P-semester team project (GARCH volatility analysis) to a personal full-stack service',
    },
    ko: {
        title: '실시간 비트코인 변동성 대시보드',
        subtitle: '6개 GARCH 모형 기반 실시간 변동성 예측 및 시장 심리 분석',
        btcPrice: '비트코인 가격',
        volume: '24시간 거래량',
        fngIndex: '공포탐욕지수',
        riskScore: '위험도 점수',
        live: '실시간',
        // Price Chart
        priceTitle: '비트코인 가격',
        // FNG
        fngGaugeTitle: '공포탐욕지수',
        fngChartTitle: '공포탐욕지수 추이',
        fngChartDesc: 'CMC Crypto Fear & Greed 추이',
        extremeFear: '극단적 공포',
        fear: '공포',
        neutral: '중립',
        greed: '탐욕',
        extremeGreed: '극단적 탐욕',
        // Volatility
        volTitle: '변동성 모형 비교',
        volDesc: '일별 롤링 예측 변동성 비교 (연간화, %)',
        // Log Returns
        logReturnsTitle: '일별 로그수익률',
        logReturnsDesc: '최근 60일 일별 로그수익률 (%)',
        // Model Table
        modelDetailTitle: '모형 예측 상세',
        modelCol: '모형',
        dailySigma: '일별 σ',
        annualVol: '연간화 변동성',
        // Signal
        signalTitle: '매매 시그널',
        strongSell: '매도 강력',
        strongBuy: '매수 강력',
        notFinancialAdvice: '※ 투자 권유가 아닙니다. GARCH 모형 분석 기반 참고 지표입니다.',
        // Leaderboard
        leaderboardTitle: '모형 정확도 리더보드',
        leaderboardDesc: '최근 30일 예측 정확도 기준 (RMSE 낮을수록 정확)',
        basedOn: '기반:',
        rollingPredictions: '개 롤링 예측 (최근 30일)',
        // Backtest
        backtestTitle: '백테스트',
        backtestDesc: '기간별 모형 성능 비교 (날짜 선택 후 실행)',
        runBacktest: '백테스트 실행',
        running: '실행 중...',
        bestModel: '이 기간 최적 모형:',
        notEnoughData: '데이터가 부족합니다. 최소 60일 이상의 기간을 선택해주세요.',
        // API Log
        apiLogTitle: 'API 디버그 로그',
        apiLogDesc: '실시간 데이터 수집 상태 확인',
        // Footer
        footer1: 'Data from CoinGecko & Alternative.me · GARCH models via arch Python package',
        footer2: 'P학기 팀 프로젝트(GARCH 변동성 분석)를 개인 프로젝트로 확장한 실서비스',
    },
};
