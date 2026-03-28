import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const PERIODS = [
    { label: '7d', days: 7 },
    { label: '1m', days: 30 },
    { label: '1y', days: 365 },
    { label: 'All', days: 2000 },
];

export default function PriceChart({ data, onPeriodChange, t = {}, coinName = 'Bitcoin', livePrice }) {
    const [active, setActive] = useState(365);

    const handlePeriod = (days) => {
        setActive(days);
        onPeriodChange?.(days);
    };

    const formatPrice = (v) => v >= 1000 ? `$${(v / 1000).toFixed(0)}K` : `$${v}`;

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-6 shadow-sm h-full">
            <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-bold text-gray-800">{coinName} {t.priceTitle === '비트코인 가격' ? '가격' : 'Price'}</h3>
                <div className="flex gap-0.5 bg-gray-50 rounded-lg p-0.5">
                    {PERIODS.map(p => (
                        <button key={p.days} onClick={() => handlePeriod(p.days)}
                            className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition ${active === p.days ? 'bg-white text-[#2b4fcb] shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}>
                            {p.label}
                        </button>
                    ))}
                </div>
            </div>
            {(livePrice || data.length > 0) && (
                <p className="text-2xl font-bold text-gray-900 mb-4">${(livePrice ?? data[data.length - 1]?.close)?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
            )}
            <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#2b4fcb" stopOpacity={0.12} />
                            <stop offset="100%" stopColor="#2b4fcb" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                    <YAxis tickFormatter={formatPrice} tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} width={50} domain={['dataMin', 'dataMax']} />
                    <Tooltip formatter={(v) => [`$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })}`, 'Price']} contentStyle={{ borderRadius: 10, border: '1px solid #e5e7eb', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.06)' }} />
                    <Area type="monotone" dataKey="close" stroke="#2b4fcb" strokeWidth={2} fill="url(#priceGrad)" dot={false} isAnimationActive={false} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
