import { useState, useEffect } from 'react';
import { fetchSignal } from '../api/client';

const SIGNAL_STYLES = {
    buy: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-[#2b4fcb]', badge: 'bg-[#2b4fcb]', label: 'BUY', emoji: '📈' },
    sell: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-500', label: 'SELL', emoji: '📉' },
    neutral: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', badge: 'bg-gray-500', label: 'NEUTRAL', emoji: '➖' },
};

const REASON_COLORS = {
    bullish: 'text-green-600',
    bearish: 'text-red-600',
    neutral: 'text-gray-500',
    warning: 'text-orange-500',
};

export default function SignalCard({ coin = 'BTC', t = {} }) {
    const [data, setData] = useState(null);

    useEffect(() => {
        setData(null);
        fetchSignal(coin).then(setData).catch(() => {});
    }, [coin]);

    if (!data) return null;

    const s = SIGNAL_STYLES[data.signal] || SIGNAL_STYLES.neutral;

    return (
        <div className={`rounded-2xl border p-6 shadow-sm h-full flex flex-col ${s.bg} ${s.border}`}>
            <div className="flex items-center justify-between mb-5">
                <h3 className="text-base font-bold text-gray-800">{t.signalTitle || 'Trading Signal'}</h3>
                <div className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-white text-sm font-bold ${s.badge}`}>
                    <span>{s.emoji}</span>
                    <span>{s.label}</span>
                </div>
            </div>

            {/* Score bar */}
            <div className="mb-5">
                <div className="flex justify-between text-xs font-semibold text-gray-400 mb-1.5">
                    <span>{t.strongSell || 'Strong Sell'}</span>
                    <span className="text-gray-600">Score: {data.score}</span>
                    <span>{t.strongBuy || 'Strong Buy'}</span>
                </div>
                <div className="h-2 bg-white/60 rounded-full overflow-hidden relative">
                    <div className="absolute inset-0 flex">
                        <div className="w-1/2 bg-gradient-to-r from-red-300 to-yellow-200"></div>
                        <div className="w-1/2 bg-gradient-to-r from-yellow-200 to-green-300"></div>
                    </div>
                    <div className="absolute top-0 h-full w-1 bg-gray-800 rounded-full transition-all duration-500"
                        style={{ left: `${((data.score + 100) / 200) * 100}%` }}></div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-5">
                <div className="text-center">
                    <p className="text-xs text-gray-400 font-semibold mb-1">FNG 7d Avg</p>
                    <p className="text-lg font-bold text-gray-800">{data.fng_avg_7d}</p>
                </div>
                <div className="text-center">
                    <p className="text-xs text-gray-400 font-semibold mb-1">Vol 7d</p>
                    <p className="text-lg font-bold text-gray-800">{data.vol_7d}%</p>
                </div>
                <div className="text-center">
                    <p className="text-xs text-gray-400 font-semibold mb-1">Price 7d</p>
                    <p className={`text-lg font-bold ${data.price_7d_change >= 0 ? 'text-[#2b4fcb]' : 'text-red-600'}`}>{data.price_7d_change > 0 ? '+' : ''}{data.price_7d_change}%</p>
                </div>
            </div>

            {/* Reasons */}
            <div className="space-y-2 flex-1">
                {data.reasons.map((r, i) => (
                    <div key={i} className={`text-[13px] font-medium flex items-start gap-2 ${REASON_COLORS[r.type] || 'text-gray-500'}`}>
                        <span className="mt-0.5">{r.type === 'bullish' ? '▲' : r.type === 'bearish' ? '▼' : r.type === 'warning' ? '⚠' : '•'}</span>
                        <span>{r.text}</span>
                    </div>
                ))}
            </div>

            <p className="text-[9px] text-gray-400 mt-3 italic">{t.notFinancialAdvice || '※ This is not financial advice. Based on GARCH model analysis only.'}</p>
        </div>
    );
}
