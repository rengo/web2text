import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import SiteList from './components/SiteList';
import Feed from './components/Feed';
import Sidebar from './components/Sidebar';
import LogViewer from './components/LogViewer';
import Settings from './components/Settings';

function App() {
    const location = useLocation();

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
            default:
                return { title: 'Dashboard', subtitle: 'Monitoring' };
        }
    };

    const details = getPageDetails();

    return (
        <div className="flex min-h-screen bg-[#F8FAFC]">
            {/* Sidebar Navigation */}
            <Sidebar />

            {/* Main Content Area */}
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
                        <div className="w-10 h-10 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
                            <span className="text-white font-black text-sm">PA</span>
                        </div>
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
