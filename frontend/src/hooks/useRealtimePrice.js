import { useState, useEffect, useRef, useCallback } from 'react';

// HTTPS 페이지에서 ws://로 WebSocket을 만들면 브라우저가 SecurityError를 던진다.
// 그 예외가 렌더 중에 발생하면 대시보드 전체가 언마운트되어 흰 화면이 되므로,
// 페이지 프로토콜에 맞춰 스킴을 고른 뒤 생성 자체도 try/catch로 감싼다.
const WS_BASE =
    import.meta.env.VITE_WS_URL ||
    `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

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

        let ws;
        try {
            ws = new WebSocket(url);
        } catch (e) {
            // 잘못된 스킴/주소여도 실시간 시세만 포기하고 대시보드는 살린다.
            setConnected(false);
            if (addLog) addLog('error', `WebSocket 연결 실패 (${url}): ${e.message}`);
            return;
        }
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
