import { useState, useEffect } from 'react';
import { fetchBacktest } from '../api/client';

const METRIC_INFO = [
    { key: 'MSE', title: 'Mean Squared Error', desc: '예측값과 실제값 차이의 제곱 평균. 낮을수록 예측이 정확합니다.' },
    { key: 'RMSE', title: 'Root Mean Squared Error', desc: 'MSE의 제곱근. 원래 단위와 같아서 해석이 직관적. 낮을수록 좋습니다.' },
    { key: 'MAE', title: 'Mean Absolute Error', desc: '예측 오차의 절대값 평균. 이상치에 덜 민감. 낮을수록 좋습니다.' },
    { key: 'MAPE', title: 'Mean Absolute Percentage Error', desc: '오차를 백분율로 표현. 100%면 예측이 실제의 2배 차이. 낮을수록 좋습니다.' },
    { key: 'R²', title: 'R-squared (결정계수)', desc: '모형이 데이터 변동을 얼마나 설명하는지. 1에 가까울수록 좋고, 음수면 평균보다 못한 예측입니다.' },
];

function MetricHeader({ col }) {
    const [show, setShow] = useState(false);
    return (
        <th className="text-right py-2 px-3 font-semibold text-gray-500 relative">
            <span className="inline-flex items-center gap-1">
                {col.key}
                <button
                    onMouseEnter={() => setShow(true)}
                    onMouseLeave={() => setShow(false)}
                    onClick={() => setShow(!show)}
                    className="w-3.5 h-3.5 rounded-full border border-gray-300 text-gray-400 text-[8px] font-bold inline-flex items-center justify-center hover:bg-gray-100 cursor-pointer"
                >?</button>
            </span>
            {show && (
                <div className="absolute top-full right-0 mt-2 w-60 bg-gray-900 text-white text-[11px] font-normal rounded-xl p-3.5 z-50 shadow-xl text-left normal-case tracking-normal"
                    onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
                    <p className="font-bold mb-1 text-xs">{col.title}</p>
                    <p className="text-gray-300 leading-relaxed">{col.desc}</p>
                    <div className="absolute -top-1.5 right-4 w-3 h-3 bg-gray-900 rotate-45"></div>
                </div>
            )}
        </th>
    );
}

export default function BacktestPanel({ coin = 'BTC', t = {} }) {
    const [start, setStart] = useState('');
    const [end, setEnd] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    // Reset result when coin changes
    useEffect(() => { setResult(null); }, [coin]);

    const run = async () => {
        if (!start || !end) return;
        setLoading(true);
        try {
            const data = await fetchBacktest(start, end, coin);
            setResult(data);
        } catch {
            setResult(null);
        } finally {
            setLoading(false);
        }
    };

    const bestModel = result?.models?.length ? result.models.reduce((a, b) => a.r2 > b.r2 ? a : b) : null;

    return (
        <div id="backtest" className="card bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="text-center mb-6">
                <h3 className="text-sm font-bold text-gray-800">{t.backtestTitle || 'Backtest'}</h3>
                <p className="text-[11px] text-gray-400 mt-0.5">{t.backtestDesc || 'Compare model performance by period (select dates and Run)'}</p>
            </div>

            <div className="flex flex-wrap items-end gap-3 mb-6 justify-center">
                <div>
                    <label className="text-[10px] font-semibold text-gray-400 uppercase block mb-1">Start</label>
                    <input type="date" value={start} onChange={e => setStart(e.target.value)}
                        className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-[#2b4fcb]" />
                </div>
                <div>
                    <label className="text-[10px] font-semibold text-gray-400 uppercase block mb-1">End</label>
                    <input type="date" value={end} onChange={e => setEnd(e.target.value)}
                        className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-[#2b4fcb]" />
                </div>
                <button onClick={run} disabled={loading || !start || !end}
                    className="px-5 py-2 bg-[#2b4fcb] text-white text-sm font-semibold rounded-lg hover:bg-[#1b3fab] transition disabled:opacity-40 disabled:cursor-not-allowed">
                    {loading ? (t.running || 'Running...') : (t.runBacktest || 'Run Backtest')}
                </button>
            </div>

            {result && result.models?.length > 0 && (
                <>
                    {bestModel && (
                        <div className="bg-[#2b4fcb]/5 border border-[#2b4fcb]/20 rounded-xl p-4 mb-4">
                            <p className="text-xs text-gray-500">{t.bestModel || 'Best performing model in this period:'}</p>
                            <p className="text-lg font-bold text-[#2b4fcb]">🏆 {bestModel.model} <span className="text-sm font-normal text-gray-500">(R² = {bestModel.r2.toFixed(4)})</span></p>
                        </div>
                    )}
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-100">
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Model</th>
                                    {METRIC_INFO.map(col => <MetricHeader key={col.key} col={col} />)}
                                </tr>
                            </thead>
                            <tbody>
                                {result.models.map((m, i) => (
                                    <tr key={i} className={`border-b border-gray-50 ${m.model === bestModel?.model ? 'bg-[#2b4fcb]/5' : ''}`}>
                                        <td className="py-2 px-3 font-semibold text-gray-800">{m.model}</td>
                                        <td className="py-2 px-3 text-right font-mono text-gray-600">{m.mse.toFixed(8)}</td>
                                        <td className="py-2 px-3 text-right font-mono text-gray-600">{m.rmse.toFixed(6)}</td>
                                        <td className="py-2 px-3 text-right font-mono text-gray-600">{m.mae.toFixed(6)}</td>
                                        <td className="py-2 px-3 text-right font-mono text-gray-600">{m.mape.toFixed(2)}%</td>
                                        <td className="py-2 px-3 text-right font-mono font-bold text-[#2b4fcb]">{m.r2.toFixed(4)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {result && (!result.models || result.models.length === 0) && (
                <p className="text-sm text-gray-400">{t.notEnoughData || 'Not enough data. Please select a period of at least 60 days.'}</p>
            )}
        </div>
    );
}
