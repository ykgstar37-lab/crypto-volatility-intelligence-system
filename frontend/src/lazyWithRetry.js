import { lazy } from 'react';

/**
 * 배포하면 Vite가 청크 파일명 해시를 새로 만든다. 그전에 열려 있던 탭은
 * 옛 파일명을 들고 있어서 동적 import가 404로 실패하고, 그 예외가 렌더
 * 경로에서 던져지면 트리 전체가 언마운트되어 흰 화면이 된다.
 *
 * 실패하면 새 index.html을 받도록 한 번만 새로고침한다. 세션 플래그로
 * 무한 새로고침을 막고, 정상 로드되면 플래그를 지워 다음 배포 때 다시
 * 동작하게 한다.
 */
const RELOAD_KEY = 'chunk-reload-at';

const get = (k) => { try { return sessionStorage.getItem(k); } catch { return null; } };
const set = (k, v) => { try { sessionStorage.setItem(k, v); } catch { /* 저장 불가여도 진행 */ } };
const del = (k) => { try { sessionStorage.removeItem(k); } catch { /* 무시 */ } };

export default function lazyWithRetry(factory) {
    return lazy(async () => {
        try {
            const mod = await factory();
            del(RELOAD_KEY);
            return mod;
        } catch (err) {
            if (!get(RELOAD_KEY)) {
                set(RELOAD_KEY, String(Date.now()));
                window.location.reload();
                // 새로고침이 진행되는 동안 렌더할 것이 없도록 빈 컴포넌트를 준다.
                return { default: () => null };
            }
            throw err;
        }
    });
}
