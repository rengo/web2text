import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import SiteList from './components/SiteList';
import Feed from './components/Feed';
import Sidebar from './components/Sidebar';
import LogViewer from './components/LogViewer';
import Settings from './components/Settings';
import Login from './components/Login';
import ApiKeys from './components/ApiKeys';
import { checkAuth, logout } from './api';

function App() {
    const location = useLocation();
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

    const authChecked = useRef(false);

    useEffect(() => {
        if (authChecked.current) return;
        authChecked.current = true;

        checkAuth().then(user => {
            setIsAuthenticated(!!user);
        });
    }, []);

    if (isAuthenticated === null) {
        return null; // Loading state
    }

    if (!isAuthenticated) {
        return (
            <Routes>
                <Route path="*" element={<Login />} />
            </Routes>
        );
    }

    const getPageDetails = () => {
        switch (location.pathname) {
            case '/':
            case '/feed':
                return { title: 'Content Dashboard', subtitle: 'Real-time data stream' };
            case '/sites':
                return { title: 'Site Management', subtitle: 'Source configurations' };
            case '/logs':
                return { title: 'System Logs', subtitle: 'Live worker events' };
            case '/settings':
                return { title: 'Global Configuration', subtitle: 'System-wide settings' };
            case '/api-keys':
                return { title: 'API Keys', subtitle: 'Manage access tokens' };
            default:
                return { title: 'Dashboard', subtitle: 'Monitoring' };
        }
    };

    const details = getPageDetails();

    return (
        <div className="flex min-h-screen bg-[#F8FAFC]">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-20 bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-10 px-8 flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                            {details.title}
                        </h2>
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mt-0.5">
                            {details.subtitle}
                        </p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden md:flex items-center bg-slate-100 rounded-full px-4 py-1.5 border border-slate-200">
                            <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>
                            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-tight">Live Session</span>
                        </div>
                        <button
                            className="w-10 h-10 bg-white hover:bg-slate-50 text-slate-400 hover:text-red-500 border border-slate-200 rounded-2xl flex items-center justify-center transition-all shadow-sm hover:shadow-md cursor-pointer group"
                            onClick={async () => {
                                await logout();
                                localStorage.removeItem('token');
                                window.location.reload();
                            }}
                            title="Logout"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 group-hover:translate-x-0.5 transition-transform">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                            </svg>
                        </button>
                    </div>
                </header>

                <main className="flex-1 p-8 overflow-y-auto">
                    <div className="max-w-7xl mx-auto">
                        <Routes>
                            <Route path="/" element={<Navigate to="/feed" replace />} />
                            <Route path="/feed" element={<Feed />} />
                            <Route path="/sites" element={<SiteList />} />
                            <Route path="/logs" element={<LogViewer />} />
                            <Route path="/settings" element={<Settings />} />
                            <Route path="/api-keys" element={<ApiKeys />} />
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    </div>
                </main>

                <footer className="px-8 py-4 bg-white border-t border-slate-100 flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    <span>© 2026 Web2Text Scraper</span>
                    <div className="flex gap-6">
                        <a href="#" className="hover:text-blue-500 transition-colors">Documentation</a>
                        <a href="#" className="hover:text-blue-500 transition-colors">API Keys</a>
                        <a href="#" className="hover:text-blue-500 transition-colors">Support</a>
                    </div>
                </footer>
            </div>
        </div>
    );
}

export default App;
