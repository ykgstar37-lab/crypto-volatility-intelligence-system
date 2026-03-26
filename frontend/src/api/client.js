import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const client = axios.create({ baseURL: API_BASE });

export const fetchCurrentPrice = (coin = 'BTC') => client.get(`/api/price/current?coin=${coin}`).then(r => r.data);
export const fetchMultiPrices = () => client.get('/api/price/multi').then(r => r.data);
export const fetchPriceHistory = (days = 365, coin = 'BTC') => client.get(`/api/price/history?days=${days}&coin=${coin}`).then(r => r.data);
export const fetchVolatilityPredict = (coin = 'BTC') => client.get(`/api/volatility/predict?coin=${coin}`).then(r => r.data);
export const fetchVolatilityCompare = (days = 90, coin = 'BTC') => client.get(`/api/volatility/compare?days=${days}&coin=${coin}`).then(r => r.data);
export const fetchBacktest = (start, end) => client.get(`/api/backtest?start=${start}&end=${end}`).then(r => r.data);
export const fetchSignal = () => client.get('/api/signal').then(r => r.data);
export const fetchLeaderboard = () => client.get('/api/signal/leaderboard').then(r => r.data);
export const fetchBriefing = (lang = 'ko') => client.get(`/api/briefing?lang=${lang}`).then(r => r.data);
export const fetchEthPrice = () => axios.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd&include_24hr_change=true').then(r => r.data.ethereum);
