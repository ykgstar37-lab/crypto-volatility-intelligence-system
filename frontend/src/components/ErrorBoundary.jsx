import { Component } from 'react';

/**
 * 렌더 중 발생한 예외가 앱 전체를 흰 화면으로 만들지 않게 막는 마지막 방어선.
 * Suspense는 로딩만 처리하고 에러는 잡지 못하므로 별도로 필요하다.
 */
export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error) {
        return { error };
    }

    componentDidCatch(error, info) {
        console.error('[ErrorBoundary]', error, info?.componentStack);
    }

    render() {
        if (!this.state.error) return this.props.children;

        return (
            <div className="flex min-h-[240px] flex-col items-center justify-center gap-3 rounded-2xl border border-gray-200 bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800">
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    이 영역을 불러오지 못했습니다
                </p>
                <p className="max-w-md text-xs text-gray-500 dark:text-gray-400">
                    {String(this.state.error?.message || this.state.error)}
                </p>
                <button
                    onClick={() => window.location.reload()}
                    className="mt-1 rounded-lg bg-[#2b4fcb] px-4 py-2 text-xs font-semibold text-white hover:opacity-90"
                >
                    새로고침
                </button>
            </div>
        );
    }
}
