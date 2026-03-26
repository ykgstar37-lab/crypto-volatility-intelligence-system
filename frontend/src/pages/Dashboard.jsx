import { useState, useEffect } from 'react';
import StatCard from '../components/StatCard';
import PriceChart from '../components/PriceChart';
import FngGauge from '../components/FngGauge';
import FngChart from '../components/FngChart';
import VolatilityChart from '../components/VolatilityChart';
import RiskScore from '../components/RiskScore';
import ModelTable from '../components/ModelTable';
import LogReturnsChart from '../components/LogReturnsChart';
import Sidebar from '../components/Sidebar';
import ApiLog from '../components/ApiLog';
import SignalCard from '../components/SignalCard';
import Leaderboard from '../components/Leaderboard';
import BacktestPanel from '../components/BacktestPanel';
import ModelExplainer from '../components/ModelExplainer';
import AiMascot from '../components/AiMascot';
import BottomDock from '../components/BottomDock';
import PriceAlert from '../components/PriceAlert';
import SignalAccuracy from '../components/SignalAccuracy';
import ReportDownload from '../components/ReportDownload';
import ToastContainer from '../components/Toast';
import { SkeletonCard, SkeletonChart, SkeletonWide } from '../components/Skeleton';
import { translations } from '../i18n';
import { fetchCurrentPrice, fetchPriceHistory, fetchVolatilityPredict, fetchEthPrice } from '../api/client';
import useRealtimePrice from '../hooks/useRealtimePrice';

function addLog(setLogs, type, message, data) {
    const time = new Date().toLocaleTimeString('en-GB');
    setLogs(prev => [...prev.slice(-50), { time, type, message, data }]);
}

const COINS = [
    { id: 'BTC', name: 'Bitcoin', icon: '₿', color: '#f7931a' },
    { id: 'ETH', name: 'Ethereum', icon: 'Ξ', color: '#627eea' },
    { id: 'SOL', name: 'Solana', icon: '◎', color: '#00d18c' },
];

export default function Dashboard() {
    const [lang, setLang] = useState('ko');
    const [dark, setDark] = useState(false);
    const [coin, setCoin] = useState('BTC');
    const [price, setPrice] = useState(null);
    const [ethPrice, setEthPrice] = useState(null);
    const [history, setHistory] = useState([]);
    const [volatility, setVolatility] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [logs, setLogs] = useState([]);
    const [activeSection, setActiveSection] = useState('dashboard');
    const [toasts, setToasts] = useState([]);
    const [multiPrices, setMultiPrices] = useState({});

    const t = translations[lang];
    const currentCoin = COINS.find(c => c.id === coin) || COINS[0];

    const addToast = (toast) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, ...toast }]);
    };
    const dismissToast = (id) => setToasts(prev => prev.filter(t => t.id !== id));

    // WebSocket real-time ticks
    const wsLogRef = (type, msg, data) => addLog(setLogs, type, msg, data);
    const { btc: wsBtc, eth: wsEth, sol: wsSol, connected: wsConnected } = useRealtimePrice(wsLogRef);

    // Map WS ticks by symbol
    const wsTicks = { BTC: wsBtc, ETH: wsEth, SOL: wsSol };

    // Live price for the currently selected coin
    const liveCoinPrice = wsTicks[coin]?.price ?? price?.price;
    // Live prices for all coins (for the mini cards)
    const liveEthPrice = wsEth ? { usd: wsEth.price, usd_24h_change: multiPrices.ETH?.change_24h ?? ethPrice?.usd_24h_change } : ethPrice;

    const load = async (days = 365, selectedCoin = coin) => {
        try {
            setLoading(true);
            addLog(setLogs, 'info', `Fetching /api/price/current?coin=${selectedCoin}...`);
            const priceData = await fetchCurrentPrice(selectedCoin);
            addLog(setLogs, 'success', `${selectedCoin} Price: $${priceData.price.toLocaleString()}`, `FNG: ${priceData.fng}`);
            setPrice(priceData);

            addLog(setLogs, 'info', `Fetching /api/price/history?coin=${selectedCoin}&days=${days}...`);
            const historyData = await fetchPriceHistory(days, selectedCoin);
            addLog(setLogs, 'success', `Loaded ${historyData.length} data points`);
            setHistory(historyData);

            addLog(setLogs, 'info', `Fetching /api/volatility/predict?coin=${selectedCoin}...`);
            const volData = await fetchVolatilityPredict(selectedCoin);
            addLog(setLogs, 'success', `${volData.predictions.length} models predicted`, `Risk: ${volData.risk_score.toFixed(1)} (${volData.risk_label})`);
            setVolatility(volData);

            // Multi prices (non-blocking)
            fetchEthPrice().then(setEthPrice).catch(() => {});

            setError(null);
        } catch (e) {
            addLog(setLogs, 'error', `Connection failed: ${e.message}`);
            setError('서버에 연결 중입니다...');
            setTimeout(() => load(days, selectedCoin), 5000);
        } finally {
            setLoading(false);
        }
    };

    // Reload when coin changes
    useEffect(() => { load(365, coin); }, [coin]);

    // Auto-refresh
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const label = wsConnected ? 'Scheduled refresh' : 'Auto-refresh (polling)';
                addLog(setLogs, 'info', `${label}: /api/price/current?coin=${coin}...`);
                const priceData = await fetchCurrentPrice(coin);
                setPrice(priceData);
                addLog(setLogs, 'success', `${label}: $${priceData.price.toLocaleString()}`, `FNG: ${priceData.fng}`);
                fetchEthPrice().then(setEthPrice).catch(() => {});
            } catch (e) {
                addLog(setLogs, 'error', `Refresh failed: ${e.message}`);
            }
        }, wsConnected ? 300000 : 60000);
        return () => clearInterval(interval);
    }, [wsConnected]);

    // Scroll spy
    useEffect(() => {
        const handleScroll = () => {
            const sections = ['dashboard', 'models', 'fng', 'returns', 'log'];
            for (const id of sections) {
                const el = document.getElementById(id);
                if (el && el.getBoundingClientRect().top < 200) {
                    setActiveSection(id);
                }
            }
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handlePeriodChange = (days) => {
        addLog(setLogs, 'info', `Reloading ${coin} history: ${days} days...`);
        fetchPriceHistory(days, coin).then(d => {
            setHistory(d);
            addLog(setLogs, 'success', `Loaded ${d.length} data points`);
        }).catch(() => {});
    };

    if (loading && !price) {
        return (
            <div className="min-h-screen bg-[#f8f9fb]" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                <header className="bg-white border-b border-gray-100 sticky top-0 z-30">
                    <div className="max-w-[1200px] mx-auto px-6 h-14 flex items-center gap-3 lg:pl-56">
                        <div className="w-7 h-7 rounded-lg bg-[#2b4fcb] flex items-center justify-center">
                            <span className="text-white text-xs font-bold">CV</span>
                        </div>
                        <span className="text-base font-bold text-gray-900">CryptoVol</span>
                    </div>
                </header>
                <main className="lg:pl-56">
                    <div className="max-w-[1200px] mx-auto px-6 py-8">
                        <div className="h-8 bg-gray-200 rounded w-80 mb-2 animate-pulse"></div>
                        <div className="h-4 bg-gray-100 rounded w-96 mb-8 animate-pulse"></div>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                            <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                            <div className="lg:col-span-2"><SkeletonChart /></div>
                            <SkeletonCard />
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            <SkeletonWide /><SkeletonWide />
                        </div>
                        {error && <p className="text-xs text-orange-500 text-center mt-4">{error}</p>}
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className={`min-h-screen transition-colors duration-300 ${dark ? 'bg-[#0f1117] text-gray-100 dark-mode' : 'bg-[#f8f9fb] text-gray-900'}`} style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            {/* Sidebar */}
            <Sidebar activeSection={activeSection} dark={dark} />

            {/* Header */}
            <header className={`border-b sticky top-0 z-30 lg:pl-56 transition-colors ${dark ? 'bg-[#161822] border-gray-800' : 'bg-white border-gray-100'}`}>
                <div className="max-w-[1200px] mx-auto px-6 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-3 lg:hidden">
                        <div className="w-7 h-7 rounded-lg bg-[#2b4fcb] flex items-center justify-center">
                            <span className="text-white text-xs font-bold">CV</span>
                        </div>
                        <span className="text-base font-bold text-gray-900">CryptoVol</span>
                    </div>
                    {/* Coin Selector */}
                    <div className={`hidden lg:flex items-center rounded-lg p-0.5 border ${dark ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-100'}`}>
                        {COINS.map(c => (
                            <button key={c.id} onClick={() => setCoin(c.id)}
                                className={`flex items-center gap-1.5 px-3 py-1 text-[11px] font-semibold rounded-md transition ${
                                    coin === c.id
                                        ? `${dark ? 'bg-gray-700' : 'bg-white'} shadow-sm`
                                        : dark ? 'text-gray-500' : 'text-gray-400'
                                }`}
                                style={coin === c.id ? { color: c.color } : {}}>
                                <span className="text-sm">{c.icon}</span>
                                {c.id}
                            </button>
                        ))}
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Language Toggle */}
                        <div className="flex bg-gray-50 rounded-lg p-0.5 border border-gray-100">
                            <button onClick={() => setLang('en')}
                                className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition ${lang === 'en' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-400'}`}>
                                🇺🇸 EN
                            </button>
                            <button onClick={() => setLang('ko')}
                                className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition ${lang === 'ko' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-400'}`}>
                                🇰🇷 KO
                            </button>
                        </div>
                        {/* Dark mode toggle */}
                        <button onClick={() => setDark(!dark)}
                            className={`w-8 h-8 rounded-lg flex items-center justify-center transition ${dark ? 'bg-gray-700 text-yellow-300' : 'bg-gray-100 text-gray-500'}`}>
                            {dark ? '☀️' : '🌙'}
                        </button>
                        <span className={`flex items-center gap-1.5 text-xs font-medium ${wsConnected ? 'text-green-600' : 'text-amber-500'}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-amber-400'}`}></span>
                            {wsConnected ? (lang === 'ko' ? '실시간' : 'Live') : (lang === 'ko' ? 'Polling' : 'Polling')}
                        </span>
                        <a href="https://github.com/ykgstar37-lab/crypto-volatility-dashboard" target="_blank" rel="noopener noreferrer"
                            className="text-xs font-medium text-gray-400 hover:text-gray-600 transition">GitHub</a>
                    </div>
                </div>
            </header>

            {/* Content */}
            <main className="lg:pl-56">
                <div className="max-w-[1200px] mx-auto px-6 py-8">
                    {/* Title */}
                    <div id="dashboard" className="mb-8">
                        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">{t.title}</h1>
                        <p className="text-sm text-gray-400 mt-1">{t.subtitle}</p>
                    </div>

                    {/* Stats Row */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <StatCard
                            label={`${currentCoin.name} ${lang === 'ko' ? '가격' : 'Price'}`}
                            value={liveCoinPrice ? `$${liveCoinPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '—'}
                            change={price?.change_24h}
                            sub={wsConnected ? 'LIVE' : '24h'}
                            icon={currentCoin.icon}
                        />
                        <StatCard
                            label={t.volume}
                            value={price ? `$${(price.volume_24h / 1e9).toFixed(2)}B` : '—'}
                            sub="USD"
                            icon="📊"
                        />
                        <StatCard
                            label={t.fngIndex}
                            value={price?.fng ?? '—'}
                            sub={price?.fng_label || ''}
                            icon="😱"
                        />
                        <RiskScore
                            score={volatility?.risk_score || 0}
                            label={volatility?.risk_label || 'N/A'}
                        />
                    </div>

                    {/* Row 1: Price Chart + FNG Gauge */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                        <div className="lg:col-span-2">
                            <PriceChart data={history} onPeriodChange={handlePeriodChange} t={t} />
                        </div>
                        <FngGauge value={price?.fng || 50} label={price?.fng_label || 'Neutral'} t={t} />
                    </div>

                    {/* Row 2: Signal + Leaderboard */}
                    <div id="signal" className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <SignalCard t={t} />
                        <Leaderboard t={t} />
                    </div>

                    {/* Row 2.5: Accuracy + ETH + Alert + Report */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <SignalAccuracy t={t} />
                        <StatCard
                            label="Ethereum"
                            value={liveEthPrice ? `$${liveEthPrice.usd?.toLocaleString()}` : '—'}
                            change={liveEthPrice?.usd_24h_change}
                            sub={wsConnected ? 'LIVE' : 'ETH'}
                            icon="Ξ"
                        />
                        <PriceAlert currentPrice={liveCoinPrice} t={t} addToast={addToast} />
                        <ReportDownload price={price} volatility={volatility} t={t} />
                    </div>

                    {/* Row 3: Volatility (full width) */}
                    <div id="models" className="mb-6">
                        <VolatilityChart t={t} />
                    </div>

                    {/* Row 4: FNG History + Log Returns */}
                    <div id="fng" className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <FngChart data={history} t={t} />
                        <div id="returns">
                            <LogReturnsChart data={history} t={t} />
                        </div>
                    </div>

                    {/* Row 5: Model Explainer + Model Table */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <ModelExplainer t={t} />
                        <ModelTable predictions={volatility?.predictions || []} t={t} />
                    </div>

                    {/* Row 6: Backtest */}
                    <div className="mb-6">
                        <BacktestPanel t={t} />
                    </div>

                    {/* Row 7: API Log */}
                    <div className="mb-6">
                        <ApiLog logs={logs} t={t} />
                    </div>

                    {/* Footer */}
                    <footer className="text-center py-8 border-t border-gray-100 mt-4">
                        <p className="text-[11px] text-gray-400">{t.footer1}</p>
                        <p className="text-[10px] text-gray-300 mt-1">{t.footer2}</p>
                    </footer>
                </div>
            </main>

            {/* Bottom Dock - floating tools bar */}
            <BottomDock dark={dark} ethPrice={liveEthPrice} price={{ ...price, price: liveCoinPrice }} volatility={volatility} t={t} addToast={addToast} />

            {/* Toast notifications */}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            {/* AI Mascot - floating bottom right */}
            <AiMascot t={t} />
        </div>
    );
}
