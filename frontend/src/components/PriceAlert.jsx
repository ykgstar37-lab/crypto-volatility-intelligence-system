import { useState, useEffect, useRef } from 'react';

export default function PriceAlert({ currentPrice, coin = 'BTC', t = {}, addToast }) {
    const [enabled, setEnabled] = useState(false);
    const [threshold, setThreshold] = useState('');
    const [direction, setDirection] = useState('below');
    const prevPrice = useRef(currentPrice);
    const lang = t.priceTitle === '비트코인 가격' ? 'ko' : 'en';

    const enableAlert = () => {
        if (!threshold) return;
        setEnabled(true);
        if (addToast) {
            addToast({
                type: 'success',
                title: lang === 'ko' ? '알림 설정 완료' : 'Alert Set',
                message: lang === 'ko'
                    ? `${coin} $${Number(threshold).toLocaleString()} ${direction === 'below' ? '이하 하락' : '이상 상승'} 시 알림`
                    : `Alert when ${coin} ${direction === 'below' ? 'drops below' : 'rises above'} $${Number(threshold).toLocaleString()}`,
            });
        }
    };

    useEffect(() => {
        if (!enabled || !threshold || !currentPrice) return;
        const target = parseFloat(threshold);
        if (isNaN(target)) return;

        const triggered = direction === 'below'
            ? currentPrice <= target && prevPrice.current > target
            : currentPrice >= target && prevPrice.current < target;

        if (triggered && addToast) {
            addToast({
                type: 'alert',
                title: lang === 'ko' ? `${coin} 가격 알림` : `${coin} Price Alert`,
                message: direction === 'below'
                    ? (lang === 'ko'
                        ? `${coin}가 $${currentPrice.toLocaleString()}로 하락 (기준: $${target.toLocaleString()})`
                        : `${coin} dropped to $${currentPrice.toLocaleString()} (threshold: $${target.toLocaleString()})`)
                    : (lang === 'ko'
                        ? `${coin}가 $${currentPrice.toLocaleString()}로 상승 (기준: $${target.toLocaleString()})`
                        : `${coin} rose to $${currentPrice.toLocaleString()} (threshold: $${target.toLocaleString()})`),
                duration: 8000,
            });
        }
        prevPrice.current = currentPrice;
    }, [currentPrice, enabled, threshold, direction, addToast, lang]);

    // Test alert
    const testAlert = () => {
        if (addToast) {
            addToast({
                type: 'alert',
                title: lang === 'ko' ? `${coin} 가격 알림 (테스트)` : `${coin} Price Alert (Test)`,
                message: lang === 'ko'
                    ? `${coin} $${(currentPrice || 87445).toLocaleString()} → 설정 가격 $${Number(threshold || 65000).toLocaleString()} ${direction === 'below' ? '하락 돌파' : '상승 돌파'}`
                    : `${coin} $${(currentPrice || 87445).toLocaleString()} → crossed $${Number(threshold || 65000).toLocaleString()} ${direction === 'below' ? 'downward' : 'upward'}`,
                duration: 6000,
            });
        }
    };

    return (
        <div className="card bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-gray-800">
                    {lang === 'ko' ? '가격 알림' : 'Price Alert'}
                </h3>
                <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
            </div>
            <div className="flex gap-2 mb-3">
                <select value={direction} onChange={e => setDirection(e.target.value)}
                    className="px-2 py-1.5 text-xs border border-gray-200 rounded-lg bg-white">
                    <option value="below">{lang === 'ko' ? '이하로 하락 시' : 'Drops below'}</option>
                    <option value="above">{lang === 'ko' ? '이상으로 상승 시' : 'Rises above'}</option>
                </select>
                <input type="number" value={threshold} onChange={e => setThreshold(e.target.value)}
                    placeholder="$65,000"
                    className="flex-1 px-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-[#2b4fcb]" />
            </div>
            <div className="flex gap-2">
                <button onClick={enableAlert}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${enabled ? 'bg-[#2b4fcb] text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}>
                    {enabled
                        ? `✓ ${lang === 'ko' ? '활성화됨' : 'Active'}`
                        : (lang === 'ko' ? '알림 활성화' : 'Enable Alert')}
                </button>
                <button onClick={testAlert}
                    className="px-3 py-2 text-xs font-medium rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition"
                    title={lang === 'ko' ? '테스트 알림' : 'Test alert'}>
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </button>
            </div>
        </div>
    );
}
