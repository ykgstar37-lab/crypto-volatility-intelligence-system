import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { simulatePortfolio } from '../api/client';

const COINS = [
    { id: 'BTC', name: 'Bitcoin', icon: '₿', color: '#f7931a' },
    { id: 'ETH', name: 'Ethereum', icon: 'Ξ', color: '#627eea' },
    { id: 'SOL', name: 'Solana', icon: '◎', color: '#00d18c' },
];

export default function PortfolioSimulator({ t = {} }) {
    const [weights, setWeights] = useState({ BTC: 50, ETH: 30, SOL: 20 });
    const [investment, setInvestment] = useState(10000);
    const [horizon, setHorizon] = useState(7);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const lang = t.priceTitle === '비트코인 가격' ? 'ko' : 'en';

    const handleWeight = (coin, val) => {
        const v = Math.max(0, Math.min(100, parseInt(val) || 0));
        setWeights(prev => ({ ...prev, [coin]: v }));
    };

    const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

    const runSimulation = async () => {
        if (totalWeight === 0) return;
        setLoading(true);
        try {
            const w = {};
            for (const c of COINS) {
                if (weights[c.id] > 0) w[c.id] = weights[c.id] / 100;
            }
            const data = await simulatePortfolio(w, investment, horizon);
            setResult(data);
        } catch {
            setResult(null);
        }
        setLoading(false);
    };

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="text-sm font-bold text-gray-800 mb-1">
                {lang === 'ko' ? '포트폴리오 시뮬레이터' : 'Portfolio Simulator'}
            </h3>
            <p className="text-xs text-gray-400 mb-5">
                {lang === 'ko'
                    ? 'BTC/ETH/SOL 비중 설정 → GARCH 기반 VaR + Monte Carlo 시뮬레이션'
                    : 'Set BTC/ETH/SOL allocation → GARCH-based VaR + Monte Carlo simulation'}
            </p>

            {/* Input controls */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Weights */}
                <div>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                        {lang === 'ko' ? '비중 설정' : 'Allocation'}
                        <span className={`ml-2 ${totalWeight === 100 ? 'text-green-500' : 'text-amber-500'}`}>
                            ({totalWeight}%)
                        </span>
                    </p>
                    <div className="space-y-3">
                        {COINS.map(c => (
                            <div key={c.id} className="flex items-center gap-3">
                                <span className="text-base w-6 text-center">{c.icon}</span>
                                <span className="text-xs font-semibold text-gray-600 w-8">{c.id}</span>
                                <input
                                    type="range"
                                    min="0" max="100" step="5"
                                    value={weights[c.id]}
                                    onChange={e => handleWeight(c.id, e.target.value)}
                                    className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer"
                                    style={{
                                        background: `linear-gradient(to right, ${c.color} ${weights[c.id]}%, #e5e7eb ${weights[c.id]}%)`,
                                    }}
                                />
                                <input
                                    type="number"
                                    value={weights[c.id]}
                                    onChange={e => handleWeight(c.id, e.target.value)}
                                    className="w-14 px-2 py-1 text-xs text-center border border-gray-200 rounded-lg"
                                />
                                <span className="text-[10px] text-gray-400">%</span>
                            </div>
                        ))}
                    </div>

                    {/* Visual pie indicator */}
                    <div className="flex gap-1 mt-3 h-2 rounded-full overflow-hidden bg-gray-100">
                        {COINS.map(c => (
                            weights[c.id] > 0 && (
                                <div key={c.id} style={{ width: `${(weights[c.id] / Math.max(totalWeight, 1)) * 100}%`, backgroundColor: c.color }}
                                    className="rounded-full transition-all duration-300" />
                            )
                        ))}
                    </div>
                </div>

                {/* Investment & Horizon */}
                <div>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                        {lang === 'ko' ? '시뮬레이션 설정' : 'Simulation Settings'}
                    </p>
                    <div className="space-y-3">
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">{lang === 'ko' ? '투자금 (USD)' : 'Investment (USD)'}</label>
                            <input type="number" value={investment} onChange={e => setInvestment(Math.max(100, parseInt(e.target.value) || 0))}
                                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-[#2b4fcb]" />
                        </div>
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">{lang === 'ko' ? '예측 기간' : 'Horizon'}</label>
                            <div className="flex gap-2">
                                {[1, 7, 14, 30].map(d => (
                                    <button key={d} onClick={() => setHorizon(d)}
                                        className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                                            horizon === d ? 'bg-[#2b4fcb] text-white' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
                                        }`}>
                                        {d}{lang === 'ko' ? '일' : 'd'}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <button onClick={runSimulation} disabled={loading || totalWeight === 0}
                            className={`w-full py-2.5 text-xs font-bold rounded-xl transition ${
                                loading ? 'bg-gray-200 text-gray-400' : 'bg-[#2b4fcb] text-white hover:bg-[#2340b0] active:scale-[0.98]'
                            }`}>
                            {loading
                                ? (lang === 'ko' ? '시뮬레이션 중...' : 'Simulating...')
                                : (lang === 'ko' ? '시뮬레이션 실행' : 'Run Simulation')}
                        </button>
                    </div>
                </div>
            </div>

            {/* Results */}
            {result && !result.error && (
                <div className="border-t border-gray-100 pt-6">
                    {/* Key metrics */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                        <MetricCard
                            label={lang === 'ko' ? 'GARCH 변동성' : 'GARCH Vol'}
                            value={`${result.portfolio.garch_vol}%`}
                            sub={lang === 'ko' ? '연간화' : 'Annualized'}
                            color="#2b4fcb"
                        />
                        <MetricCard
                            label="VaR (95%)"
                            value={`-$${result.var.var_95_usd.toLocaleString()}`}
                            sub={`${result.horizon}${lang === 'ko' ? '일' : 'd'} / -${result.var.var_95_pct}%`}
                            color="#f59e0b"
                        />
                        <MetricCard
                            label="VaR (99%)"
                            value={`-$${result.var.var_99_usd.toLocaleString()}`}
                            sub={`${result.horizon}${lang === 'ko' ? '일' : 'd'} / -${result.var.var_99_pct}%`}
                            color="#ef4444"
                        />
                        <MetricCard
                            label={lang === 'ko' ? '샤프 비율' : 'Sharpe Ratio'}
                            value={result.portfolio.sharpe.toFixed(2)}
                            sub={`${lang === 'ko' ? '수익률' : 'Return'}: ${result.portfolio.ann_return > 0 ? '+' : ''}${result.portfolio.ann_return}%`}
                            color="#00d18c"
                        />
                    </div>

                    {/* Monte Carlo Distribution */}
                    <div className="mb-6">
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                            Monte Carlo {lang === 'ko' ? '손익 분포' : 'P&L Distribution'} (1,000 {lang === 'ko' ? '시나리오' : 'scenarios'})
                        </p>
                        <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={result.distribution} margin={{ top: 5, right: 5, left: -15, bottom: 5 }}>
                                    <XAxis
                                        dataKey="x"
                                        tick={{ fontSize: 9, fill: '#999' }}
                                        tickFormatter={v => `$${v >= 0 ? '+' : ''}${v}`}
                                        interval="preserveStartEnd"
                                    />
                                    <YAxis tick={{ fontSize: 9, fill: '#999' }} />
                                    <Tooltip
                                        contentStyle={{ fontSize: 11, borderRadius: 12, border: '1px solid #eee' }}
                                        formatter={(v) => [v, lang === 'ko' ? '시나리오' : 'Scenarios']}
                                        labelFormatter={v => `P&L: $${v >= 0 ? '+' : ''}${v}`}
                                    />
                                    <ReferenceLine x={0} stroke="#ef4444" strokeDasharray="3 3" />
                                    <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                                        {result.distribution.map((d, i) => (
                                            <Cell key={i} fill={d.x >= 0 ? '#2b4fcb' : '#ef4444'} opacity={0.7} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="flex justify-between text-[9px] text-gray-400 mt-1 px-2">
                            <span>5%: ${result.monte_carlo.p5.toLocaleString()}</span>
                            <span>Median: ${result.monte_carlo.p50 >= 0 ? '+' : ''}{result.monte_carlo.p50.toLocaleString()}</span>
                            <span>95%: +${result.monte_carlo.p95.toLocaleString()}</span>
                        </div>
                    </div>

                    {/* Coin breakdown */}
                    <div className="grid grid-cols-3 gap-3">
                        {result.coins.map(c => {
                            const coinMeta = COINS.find(m => m.id === c.symbol);
                            return (
                                <div key={c.symbol} className="rounded-xl p-3 bg-gray-50 border border-gray-100">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-base">{coinMeta?.icon}</span>
                                        <span className="text-xs font-bold text-gray-700">{c.symbol}</span>
                                        <span className="text-[10px] text-gray-400 ml-auto">{c.weight}%</span>
                                    </div>
                                    <div className="space-y-1 text-[10px]">
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">{lang === 'ko' ? '연간 수익률' : 'Ann. Return'}</span>
                                            <span className={`font-semibold ${c.ann_return >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                                                {c.ann_return >= 0 ? '+' : ''}{c.ann_return}%
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-400">{lang === 'ko' ? 'GARCH 변동성' : 'GARCH Vol'}</span>
                                            <span className="font-semibold text-gray-700">{c.ann_vol}%</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {result?.error && (
                <div className="text-center py-8">
                    <p className="text-xs text-red-500">{result.error}</p>
                </div>
            )}
        </div>
    );
}

function MetricCard({ label, value, sub, color }) {
    return (
        <div className="rounded-xl p-3 bg-gray-50 border border-gray-100">
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">{label}</p>
            <p className="text-lg font-bold" style={{ color }}>{value}</p>
            <p className="text-[10px] text-gray-400">{sub}</p>
        </div>
    );
}
