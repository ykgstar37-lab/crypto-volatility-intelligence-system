import { useState, useEffect } from 'react';
import { fetchLeaderboard } from '../api/client';

const MEDAL = ['🥇', '🥈', '🥉'];

export default function Leaderboard({ coin = 'BTC', t = {} }) {
    const [data, setData] = useState([]);

    useEffect(() => {
        setData([]);
        fetchLeaderboard(coin).then(setData).catch(() => {});
    }, [coin]);

    if (!data.length) return null;

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="mb-4">
                <h3 className="text-sm font-bold text-gray-800">{t.leaderboardTitle || 'Model Accuracy Leaderboard'}</h3>
                <p className="text-[11px] text-gray-400 mt-0.5">{t.leaderboardDesc || 'Prediction accuracy ranking based on last 30 days (lower RMSE = better)'}</p>
            </div>
            <div className="space-y-2">
                {data.map((m, i) => {
                    const maxRmse = Math.max(...data.map(d => d.rmse));
                    const barW = maxRmse > 0 ? ((maxRmse - m.rmse) / maxRmse) * 100 : 0;
                    return (
                        <div key={i} className={`flex items-center gap-3 p-3 rounded-xl transition ${i === 0 ? 'bg-[#2b4fcb]/5 border border-[#2b4fcb]/20' : 'hover:bg-gray-50'}`}>
                            <span className="text-lg w-8 text-center">{MEDAL[i] || `#${m.rank}`}</span>
                            <div className="flex-1">
                                <div className="flex items-center justify-between mb-1">
                                    <span className={`text-sm font-semibold ${i === 0 ? 'text-[#2b4fcb]' : 'text-gray-700'}`}>{m.model}</span>
                                    <span className="text-xs font-mono text-gray-500">RMSE: {m.rmse.toFixed(6)}</span>
                                </div>
                                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                    <div className="h-full rounded-full transition-all duration-700"
                                        style={{ width: `${Math.max(20, barW)}%`, background: i === 0 ? '#2b4fcb' : i === 1 ? '#5878dd' : '#a0aec0' }}></div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
            <p className="text-[9px] text-gray-400 mt-3">{t.basedOn || 'Based on'} {data[0]?.samples || 0} {t.rollingPredictions || 'rolling predictions over last 30 days'}</p>
        </div>
    );
}
