import { useState } from 'react';

export default function Sidebar({ activeSection, dark }) {
    const [mobileOpen, setMobileOpen] = useState(false);

    const menus = [
        { id: 'dashboard', label: 'Dashboard', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1" />
            </svg>
        )},
        { id: 'signal', label: 'Signal', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
        )},
        { id: 'models', label: 'Models', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
        )},
        { id: 'fng', label: 'FNG', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
        )},
        { id: 'returns', label: 'Returns', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
        )},
        { id: 'portfolio', label: 'Portfolio', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
            </svg>
        )},
        { id: 'backtest', label: 'Backtest', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        )},
        { id: 'log', label: 'API Log', icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
        )},
    ];

    const scrollTo = (id) => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setMobileOpen(false);
    };

    const navContent = (
        <nav className="space-y-1">
            {menus.map(m => {
                const active = activeSection === m.id;
                return (
                    <button key={m.id} onClick={() => scrollTo(m.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                            active
                                ? 'bg-[#2b4fcb]/10 text-[#2b4fcb]'
                                : dark
                                    ? 'text-gray-400 hover:bg-gray-700/50 hover:text-gray-200'
                                    : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                        }`}>
                        {m.icon}
                        {m.label}
                    </button>
                );
            })}
        </nav>
    );

    return (
        <>
            {/* Desktop sidebar */}
            <aside className={`w-56 border-r min-h-screen pt-20 px-3 hidden lg:block fixed left-0 top-0 z-20 transition-colors ${
                dark ? 'bg-[#161822] border-gray-800' : 'bg-white border-gray-100'
            }`}>
                <div className="flex items-center gap-2.5 px-3 mb-8">
                    <div className="w-8 h-8 rounded-xl bg-[#2b4fcb] flex items-center justify-center">
                        <span className="text-white text-xs font-bold">CV</span>
                    </div>
                    <span className={`text-sm font-bold tracking-tight ${dark ? 'text-gray-100' : 'text-gray-900'}`}>CryptoVol</span>
                </div>
                {navContent}
            </aside>

            {/* Mobile hamburger button */}
            <button onClick={() => setMobileOpen(!mobileOpen)}
                className={`lg:hidden fixed top-3.5 left-4 z-40 w-9 h-9 rounded-lg border shadow-sm flex items-center justify-center ${
                    dark ? 'bg-[#161822] border-gray-700' : 'bg-white border-gray-200'
                }`}>
                {mobileOpen ? (
                    <svg className={`w-5 h-5 ${dark ? 'text-gray-300' : 'text-gray-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                ) : (
                    <svg className={`w-5 h-5 ${dark ? 'text-gray-300' : 'text-gray-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                )}
            </button>

            {/* Mobile overlay */}
            {mobileOpen && (
                <>
                    <div className="lg:hidden fixed inset-0 bg-black/30 z-30" onClick={() => setMobileOpen(false)}></div>
                    <aside className={`lg:hidden fixed left-0 top-0 w-64 min-h-screen pt-16 px-4 z-30 shadow-xl ${
                        dark ? 'bg-[#161822]' : 'bg-white'
                    }`}>
                        <div className="flex items-center gap-2.5 px-3 mb-6">
                            <div className="w-8 h-8 rounded-xl bg-[#2b4fcb] flex items-center justify-center">
                                <span className="text-white text-xs font-bold">CV</span>
                            </div>
                            <span className={`text-sm font-bold ${dark ? 'text-gray-100' : 'text-gray-900'}`}>CryptoVol</span>
                        </div>
                        {navContent}
                    </aside>
                </>
            )}
        </>
    );
}
