import { useState, useEffect } from 'react';
import { fetchSignalAccuracy } from '../api/client';

export default function SignalAccuracy({ coin = 'BTC', t = {} }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const lang = t.priceTitle === '비트코인 가격' ? 'ko' : 'en';

    useEffect(() => {
        setData(null);
        setLoading(true);
        fetchSignalAccuracy(coin)
            .then(setData)
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [coin]);

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-5 shadow-sm h-full flex flex-col">
            <h3 className="text-sm font-bold text-gray-800 mb-3">
                {lang === 'ko' ? '시그널 적중률' : 'Signal Accuracy'}
            </h3>
            {data && data.total > 0 ? (
                <>
                    <div className="text-center mb-3">
                        <p className="text-3xl font-bold text-[#2b4fcb]">{data.accuracy}%</p>
                        <p className="text-xs text-gray-400">{data.correct}/{data.total} {lang === 'ko' ? '적중' : 'correct'}</p>
                    </div>
                    <div className="flex gap-0.5 justify-center flex-wrap">
                        {data.history.map((h, i) => (
                            <div key={i} className={`w-3 h-3 rounded-sm ${h.correct ? 'bg-[#2b4fcb]' : 'bg-red-400'}`}
                                title={`${h.date}: ${h.signal} → ${h.actual_7d > 0 ? '+' : ''}${h.actual_7d}%`}></div>
                        ))}
                    </div>
                    <div className="flex justify-center gap-3 mt-2 text-[9px] text-gray-400">
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[#2b4fcb]"></span>{lang === 'ko' ? '적중' : 'Correct'}</span>
                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-red-400"></span>{lang === 'ko' ? '미적중' : 'Wrong'}</span>
                    </div>
                </>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                    <p className="text-3xl font-bold text-[#2b4fcb]">—</p>
                    <p className="text-xs text-gray-400 mt-1">
                        {loading
                            ? (lang === 'ko' ? '로딩 중...' : 'Loading...')
                            : (lang === 'ko' ? '데이터 수집 중' : 'Collecting data')}
                    </p>
                </div>
            )}
        </div>
    );
}
