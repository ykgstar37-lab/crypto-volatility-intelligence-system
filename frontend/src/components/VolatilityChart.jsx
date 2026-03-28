import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchVolatilityCompare } from '../api/client';

const MODELS = [
    { key: 'realized', name: 'Realized', color: '#94a3b8', dash: '5 3' },
    { key: 'garch', name: 'GARCH(1,1)', color: '#2b4fcb', dash: '' },
    { key: 'tgarch', name: 'TGARCH', color: '#5878dd', dash: '' },
    { key: 'har_garch', name: 'HAR-GARCH', color: '#e8609c', dash: '' },
    { key: 'har_tgarch', name: 'HAR-TGARCH', color: '#f59e0b', dash: '' },
];

export default function VolatilityChart({ coin = 'BTC', t = {} }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeModels, setActiveModels] = useState(new Set(MODELS.map(m => m.key)));
    const [period, setPeriod] = useState(90);

    useEffect(() => {
        setLoading(true);
        fetchVolatilityCompare(period, coin)
            .then(setData)
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [period, coin]);

    const toggle = (key) => {
        setActiveModels(prev => {
            const next = new Set(prev);
            next.has(key) ? next.delete(key) : next.add(key);
            return next;
        });
    };

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-1">
                <div>
                    <h3 className="text-sm font-bold text-gray-800">{t.volTitle || 'Volatility Model Comparison'}</h3>
                    <p className="text-[11px] text-gray-400 mt-0.5">{t.volDesc || 'Rolling daily predicted volatility comparison (annualized, %)'}</p>
                </div>
                <div className="flex gap-0.5 bg-gray-50 rounded-lg p-0.5">
                    {[30, 60, 90].map(d => (
                        <button key={d} onClick={() => setPeriod(d)}
                            className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition ${period === d ? 'bg-white text-[#2b4fcb] shadow-sm' : 'text-gray-400'}`}>
                            {d}d
                        </button>
                    ))}
                </div>
            </div>

            {/* Model toggles */}
            <div className="flex flex-wrap gap-1.5 my-4">
                {MODELS.map(m => {
                    const active = activeModels.has(m.key);
                    return (
                        <button key={m.key} onClick={() => toggle(m.key)}
                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold transition border ${active ? 'border-transparent text-white' : 'border-gray-200 text-gray-400 bg-white'}`}
                            style={active ? { background: m.color } : {}}>
                            <span className="w-2 h-2 rounded-full" style={{ background: active ? '#fff' : m.color }}></span>
                            {m.name}
                        </button>
                    );
                })}
            </div>

            {loading ? (
                <div className="h-72 flex items-center justify-center text-gray-300 text-sm">
                    <div className="w-6 h-6 border-2 border-gray-200 border-t-[#2b4fcb] rounded-full animate-spin mr-2"></div>
                    Computing models...
                </div>
            ) : (
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                        <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={v => `${v}%`} axisLine={false} tickLine={false} />
                        <Tooltip
                            contentStyle={{ borderRadius: 10, border: '1px solid #e5e7eb', fontSize: 11, boxShadow: '0 4px 12px rgba(0,0,0,0.06)' }}
                            formatter={(v, name) => [v != null ? `${v}%` : '—', name]}
                        />
                        {MODELS.map(m => (
                            activeModels.has(m.key) && (
                                <Line
                                    key={m.key}
                                    type="monotone"
                                    dataKey={m.key}
                                    name={m.name}
                                    stroke={m.color}
                                    strokeWidth={m.key === 'realized' ? 1.5 : 2}
                                    strokeDasharray={m.dash}
                                    dot={false}
                                    connectNulls
                                    isAnimationActive={false}
                                />
                            )
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}
