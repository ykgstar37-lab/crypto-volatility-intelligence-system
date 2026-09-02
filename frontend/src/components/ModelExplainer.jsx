import { useState } from 'react';

const MODELS = [
    {
        name: 'GARCH(1,1)',
        color: '#2b4fcb',
        formula: 'σ²ₜ = ω + α · r²ₜ₋₁ + β · σ²ₜ₋₁',
        params: ['ω (omega): 장기 평균 분산', 'α (alpha): 직전 충격의 영향', 'β (beta): 이전 분산의 지속성'],
        desc: {
            en: 'The baseline model. Captures volatility clustering — large price moves tend to be followed by large moves. Simple but effective for stable markets.',
            ko: '기본 변동성 모형. 변동성 군집 현상(큰 가격 변동 후 큰 변동이 지속)을 포착. 안정적인 시장에서 단순하지만 효과적.',
        },
        insight: {
            en: 'Use when: Market is relatively calm and symmetric. α + β close to 1 means volatility is highly persistent.',
            ko: '활용: 시장이 비교적 안정적이고 대칭적일 때. α + β ≈ 1이면 변동성이 오래 지속됨을 의미.',
        },
    },
    {
        name: 'TGARCH',
        color: '#5878dd',
        formula: 'σ²ₜ = ω + α · r²ₜ₋₁ + γ · r²ₜ₋₁ · I(rₜ₋₁ < 0) + β · σ²ₜ₋₁',
        params: ['γ (gamma): 하락 시 추가 변동성 (레버리지 효과)', 'I(rₜ₋₁ < 0): 이전 수익률이 음수일 때 1'],
        desc: {
            en: 'Adds asymmetric leverage effect. Bad news (price drops) increases volatility more than good news (price rises). Critical for crypto markets where crashes are sharper than rallies.',
            ko: '비대칭 레버리지 효과 추가. 나쁜 뉴스(가격 하락)가 좋은 뉴스(가격 상승)보다 변동성을 더 크게 증가시킴. 급락이 급등보다 급격한 암호화폐 시장에 필수적.',
        },
        insight: {
            en: 'Use when: Market shows asymmetric behavior. γ = 0.0990 (reproduced as 0.0986 under the original spec) means crashes amplify volatility ~10% more than rallies. Note the sign flips under a Student-t error distribution.',
            ko: '활용: 시장이 비대칭 행동을 보일 때. γ = 0.0990(원 사양 재현값 0.0986)은 급락 시 변동성이 급등 대비 약 10% 더 증폭됨을 의미. 단, 오차분포를 t분포로 바꾸면 부호가 뒤집힌다.',
        },
    },
    {
        name: 'GARCH+E.V',
        color: '#0ea5e9',
        formula: 'GARCH(1,1) + 외생변수(거래량, FNG)',
        params: ['x₀: 표준화된 거래량', 'x₁: 표준화된 공포탐욕지수(FNG)'],
        desc: {
            en: 'GARCH(1,1) with exogenous variables. In the 2023 source paper this row was left blank — the estimates were never produced. It is fitted here for the first time.',
            ko: 'GARCH(1,1)에 외생변수를 추가한 모형. 2023년 원 논문에서는 이 행이 공란이었고 추정치가 산출된 적이 없다. 여기서 처음으로 적합했다.',
        },
        insight: {
            en: 'Note: the arch package cannot take exogenous regressors in the variance equation, so they enter the mean equation instead. This differs from the paper’s specification.',
            ko: '참고: arch 패키지가 분산식 외생변수를 지원하지 않아 평균식에 투입했다. 논문 수식과는 다른 사양이다.',
        },
    },
    {
        name: 'HAR-GARCH',
        color: '#e8609c',
        formula: 'HARCH(lags = [1, 7, 30])',
        params: ['RV_d: 일별 실현 변동성 (1일)', 'RV_w: 주간 실현 변동성 (7일)', 'RV_m: 월간 실현 변동성 (30일)'],
        desc: {
            en: 'Heterogeneous Autoregressive model. Captures multi-scale volatility — daily traders, weekly swing traders, and monthly institutional investors all affect volatility differently.',
            ko: 'HAR(이질적 자기회귀) 모형. 다중 스케일 변동성 포착 — 데이트레이더(1일), 스윙트레이더(7일), 기관투자자(30일)가 변동성에 다르게 영향.',
        },
        insight: {
            en: 'Use when: You need to understand which time horizon drives current volatility. If RV_m dominates, structural shift is happening.',
            ko: '활용: 어떤 시간대가 현재 변동성을 주도하는지 파악할 때. RV_m이 지배적이면 구조적 변화가 진행 중.',
        },
    },
    {
        name: 'HAR-TGARCH',
        color: '#f59e0b',
        formula: 'rₜ = c + β₁·RV_d + β₂·RV_w + β₃·RV_m + β₄·NEG + β₅·σ_lag + εₜ',
        params: ['NEG: 음수 수익률 × 실현변동성', 'σ_lag: 이전 5일 평균 변동성'],
        desc: {
            en: 'Combines HAR multi-scale structure with TGARCH asymmetry. Best of both worlds — captures time-horizon effects AND crash amplification simultaneously.',
            ko: 'HAR 다중 스케일 구조와 TGARCH 비대칭성 결합. 시간대 효과와 급락 증폭을 동시에 포착하는 두 모형의 장점 결합.',
        },
        insight: {
            en: 'Use when: Market is volatile with clear directional bias. Particularly effective during trend reversals.',
            ko: '활용: 시장이 변동성이 크면서 방향성 편향이 명확할 때. 특히 추세 반전 시 효과적.',
        },
    },
    {
        name: 'HAR-TGARCH-X',
        color: '#1b3fab',
        formula: '... + β₆·Volume_lag + β₇·FNG_lag',
        params: ['Volume_lag: 전일 거래량 (정규화)', 'FNG_lag: 전일 공포탐욕지수'],
        desc: {
            en: 'The most comprehensive model. Adds exogenous variables (trading volume + Fear & Greed Index) to HAR-TGARCH. Volume captures market activity intensity, FNG captures market psychology.',
            ko: '가장 포괄적인 모형. HAR-TGARCH에 외생변수(거래량 + 공포탐욕지수) 추가. 거래량은 시장 활동 강도, FNG는 시장 심리를 반영.',
        },
        insight: {
            en: 'Use when: You want the most informed prediction. P-semester research confirmed FNG correlation with BTC at r=0.72 (p<0.001).',
            ko: '활용: 가장 정보가 풍부한 예측을 원할 때. P학기 연구에서 FNG-BTC 상관계수 r=0.72 (p<0.001) 확인.',
        },
    },
];

export default function ModelExplainer({ t = {} }) {
    const [selected, setSelected] = useState(0);
    const lang = t.priceTitle === '비트코인 가격' ? 'ko' : 'en';
    const m = MODELS[selected];

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="mb-5">
                <h3 className="text-sm font-bold text-gray-800">
                    {lang === 'ko' ? 'GARCH 모형 상세 설명' : 'GARCH Model Details'}
                </h3>
                <p className="text-[11px] text-gray-400 mt-0.5">
                    {lang === 'ko' ? '각 모형의 수식, 파라미터, 활용 인사이트' : 'Formula, parameters, and usage insights for each model'}
                </p>
            </div>

            {/* Model tabs */}
            <div className="flex flex-wrap gap-1.5 mb-6">
                {MODELS.map((model, i) => (
                    <button key={i} onClick={() => setSelected(i)}
                        className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition border ${selected === i ? 'text-white border-transparent' : 'text-gray-500 border-gray-200 bg-white hover:bg-gray-50'}`}
                        style={selected === i ? { background: model.color } : {}}>
                        {model.name}
                    </button>
                ))}
            </div>

            {/* Selected model detail */}
            <div className="space-y-4">
                {/* Formula */}
                <div className="bg-gray-900 rounded-xl p-4">
                    <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-2">
                        {lang === 'ko' ? '수식' : 'Formula'}
                    </p>
                    <p className="text-lg font-mono text-white tracking-wide">{m.formula}</p>
                </div>

                {/* Parameters */}
                <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                        {lang === 'ko' ? '파라미터' : 'Parameters'}
                    </p>
                    <div className="space-y-1.5">
                        {m.params.map((p, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm text-gray-700">
                                <span className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: m.color }}></span>
                                <span>{p}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Description */}
                <div>
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
                        {lang === 'ko' ? '설명' : 'Description'}
                    </p>
                    <p className="text-sm text-gray-600 leading-relaxed">{m.desc[lang]}</p>
                </div>

                {/* Insight */}
                <div className="border-l-3 pl-4" style={{ borderLeftColor: m.color, borderLeftWidth: 3 }}>
                    <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: m.color }}>
                        {lang === 'ko' ? '인사이트' : 'Insight'}
                    </p>
                    <p className="text-sm text-gray-600 leading-relaxed">{m.insight[lang]}</p>
                </div>
            </div>
        </div>
    );
}
