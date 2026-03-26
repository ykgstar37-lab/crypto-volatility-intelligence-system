import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000`;

/**
 * useRealtimePrice — WebSocket hook for Binance real-time ticks via backend relay.
 *
 * Returns: { btc, eth, connected }
 *   btc = { price, ts }
 *   eth = { price, ts }
 *   connected = boolean
 */
export default function useRealtimePrice(addLog) {
    const [btc, setBtc] = useState(null);
    const [eth, setEth] = useState(null);
    const [sol, setSol] = useState(null);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef(null);
    const reconnectTimer = useRef(null);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const url = `${WS_BASE}/ws/ticks`;
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
            setConnected(true);
            if (addLog) addLog('success', 'WebSocket connected to Binance relay');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'tick') {
                    if (data.symbol === 'BTC') {
                        setBtc({ price: data.price, ts: data.ts });
                    } else if (data.symbol === 'ETH') {
                        setEth({ price: data.price, ts: data.ts });
                    } else if (data.symbol === 'SOL') {
                        setSol({ price: data.price, ts: data.ts });
                    }
                }
            } catch {
                // ignore parse errors
            }
        };

        ws.onclose = () => {
            setConnected(false);
            if (addLog) addLog('info', 'WebSocket disconnected. Reconnecting in 3s...');
            reconnectTimer.current = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
            ws.close();
        };
    }, [addLog]);

    useEffect(() => {
        connect();
        return () => {
            clearTimeout(reconnectTimer.current);
            wsRef.current?.close();
        };
    }, [connect]);

    return { btc, eth, sol, connected };
}
