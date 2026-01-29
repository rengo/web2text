import { NavLink } from 'react-router-dom';

export default function Sidebar() {
    const navLinkClass = ({ isActive }: { isActive: boolean }) =>
        `w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
            ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
            : 'text-gray-400 hover:bg-gray-800 hover:text-white'
        }`;

    const iconClass = (isActive: boolean) =>
        `w-5 h-5 transition-colors ${isActive ? 'text-white' : 'text-gray-500 group-hover:text-blue-400'}`;

    return (
        <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col shadow-xl transition-all duration-300">
            <div className="p-6 border-b border-gray-800">
                <h1 className="text-2xl font-black bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Web2Text
                </h1>
                <p className="text-xs text-gray-500 mt-1 uppercase tracking-widest font-bold">Scraper Platform</p>
            </div>

            <nav className="flex-1 mt-6 px-3 space-y-2">
                <NavLink to="/feed" className={navLinkClass}>
                    {({ isActive }) => (
                        <>
                            <svg className={iconClass(isActive)} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                            </svg>
                            <span className="font-semibold text-sm">Contenido</span>
                        </>
                    )}
                </NavLink>

                <NavLink to="/sites" className={navLinkClass}>
                    {({ isActive }) => (
                        <>
                            <svg className={iconClass(isActive)} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                            </svg>
                            <span className="font-semibold text-sm">Sitios</span>
                        </>
                    )}
                </NavLink>

                <NavLink to="/logs" className={navLinkClass}>
                    {({ isActive }) => (
                        <>
                            <svg className={iconClass(isActive)} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <span className="font-semibold text-sm">Logs en Vivo</span>
                        </>
                    )}
                </NavLink>

                <NavLink to="/settings" className={navLinkClass}>
                    {({ isActive }) => (
                        <>
                            <svg className={iconClass(isActive)} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <span className="font-semibold text-sm">Configuración</span>
                        </>
                    )}
                </NavLink>
            </nav>

            <div className="p-4 mt-auto">
                <div className="bg-gray-800/50 rounded-2xl p-4 border border-gray-700/50">
                    <p className="text-xs text-gray-500 font-medium">System Status</p>
                    <div className="flex items-center mt-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse mr-2"></div>
                        <span className="text-xs text-gray-300">Workers Active</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}
