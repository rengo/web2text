import { useEffect, useState } from 'react';
import { fetchFeed, fetchSites } from '../api';

export default function Feed() {
    const [pages, setPages] = useState<any[]>([]);
    const [sites, setSites] = useState<any[]>([]);
    const [selectedSite, setSelectedSite] = useState<string>('');
    const [search, setSearch] = useState('');
    const [since, setSince] = useState(new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 16));
    const [selectedPage, setSelectedPage] = useState<any | null>(null);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [loading, setLoading] = useState(false);

    const load = async () => {
        setLoading(true);
        try {
            const data = await fetchFeed(new Date(since).toISOString(), selectedSite, page, 50, search);
            setPages(data.items);
            setTotalPages(data.total_pages);
        } finally {
            setLoading(false);
        }
    };

    const loadSites = async () => {
        const data = await fetchSites();
        setSites(data);
    };

    useEffect(() => {
        load();
    }, [since, selectedSite, page]);

    useEffect(() => { loadSites(); }, []);

    // Scroll to top when page changes
    useEffect(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, [page]);

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Latest Content</h2>
                    <p className="text-gray-500 text-sm mt-1">Discover recently scraped content from your configured sites.</p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex flex-col gap-1 min-w-[200px]">
                        <label className="text-[10px] uppercase font-bold text-gray-400 ml-1">Search</label>
                        <div className="relative">
                            <input
                                type="text"
                                value={search}
                                onChange={e => { setSearch(e.target.value); setPage(1); }}
                                onKeyDown={e => { if (e.key === 'Enter') load(); }}
                                placeholder="Title or content..."
                                className="w-full border border-gray-200 rounded-xl pl-10 pr-10 py-2.5 text-sm bg-gray-50/50 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                            />
                            <svg className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            {loading && (
                                <div className="absolute right-3.5 top-1/2 -translate-y-1/2">
                                    <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex flex-col gap-1">
                        <label className="text-[10px] uppercase font-bold text-gray-400 ml-1">Filter by Site</label>
                        <select
                            value={selectedSite}
                            onChange={e => { setSelectedSite(e.target.value); setPage(1); }}
                            className="border border-gray-200 rounded-xl px-4 py-2.5 text-sm bg-gray-50/50 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        >
                            <option value="">All Sites</option>
                            {sites.map(site => (
                                <option key={site.id} value={site.id}>{site.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex flex-col gap-1">
                        <label className="text-[10px] uppercase font-bold text-gray-400 ml-1">Since</label>
                        <input
                            type="datetime-local"
                            value={since}
                            onChange={e => setSince(e.target.value)}
                            className="border border-gray-200 rounded-xl px-4 py-2.5 text-sm bg-gray-50/50 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        />
                    </div>

                    <button
                        onClick={load}
                        disabled={loading}
                        className={`mt-5 bg-gray-900 border border-gray-800 text-white p-2.5 rounded-xl hover:bg-gray-800 transition-colors shadow-lg shadow-gray-200 disabled:opacity-50 disabled:cursor-not-allowed`}
                        title="Refresh"
                    >
                        <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {pages.map(page => (
                    <article key={page.id} className="group bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl hover:border-blue-100 transition-all duration-300 flex flex-col">
                        <div className="p-8 flex-1">
                            <div className="flex justify-between items-start mb-6">
                                <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full">
                                    {page.site_name || 'Generic'}
                                </span>
                                <time className="text-xs font-semibold text-gray-400" dateTime={page.published_at || page.scraped_at}>
                                    {new Date(page.published_at || page.scraped_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                </time>
                            </div>

                            <h3 className="text-xl font-bold text-gray-900 mb-4 leading-tight group-hover:text-blue-600 transition-colors">
                                <a href={page.url} target="_blank" rel="noopener noreferrer">
                                    {page.title || page.url}
                                </a>
                            </h3>

                            <div className="prose prose-sm max-w-none text-gray-600 line-clamp-4 leading-relaxed">
                                {page.latest_content ? (
                                    <p>{page.latest_content.extracted_text}</p>
                                ) : (
                                    <p className="italic text-gray-400">No content extracted yet...</p>
                                )}
                            </div>
                        </div>

                        <div className="px-6 py-4 bg-gray-50/50 border-t border-gray-50 flex items-center justify-between gap-2 overflow-hidden">
                            <div className="flex items-center gap-1.5 min-w-0">
                                <span className="text-[9px] font-bold text-gray-500 uppercase flex items-center bg-white px-2 py-1 rounded-lg border border-gray-100 whitespace-nowrap shrink-0">
                                    <svg className="w-2.5 h-2.5 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                                    </svg>
                                    {page.discovered_via}
                                </span>
                                {page.latest_content?.metadata_?.date_source && (
                                    <span
                                        className="text-[9px] font-bold text-blue-500 uppercase flex items-center bg-blue-50/50 px-2 py-1 rounded-lg border border-blue-100/30 min-w-0 max-w-[100px] sm:max-w-[140px]"
                                        title={`Verified via: ${page.latest_content.metadata_.date_source}`}
                                    >
                                        <svg className="w-2.5 h-2.5 mr-1 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                        <span className="truncate">V: {page.latest_content.metadata_.date_source}</span>
                                    </span>
                                )}
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                                {page.latest_content && (
                                    <button
                                        onClick={() => setSelectedPage(page)}
                                        className="inline-flex items-center text-[10px] font-bold text-blue-600 hover:text-blue-700 transition-colors bg-blue-50 hover:bg-blue-100 px-2.5 py-1.5 rounded-lg whitespace-nowrap"
                                    >
                                        <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                        </svg>
                                        Full Text
                                    </button>
                                )}
                                <a
                                    href={page.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-gray-400 hover:text-blue-600 transition-colors p-1.5 hover:bg-white rounded-lg border border-transparent hover:border-gray-100 shrink-0"
                                    title="Open Original Link"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </article>
                ))}
            </div>

            {/* Pagination Controls */}
            {pages.length > 0 && (
                <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
                    <div className="text-sm text-gray-500">
                        Page <span className="font-semibold text-gray-900">{page}</span> of <span className="font-semibold text-gray-900">{totalPages}</span>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page >= totalPages}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}

            {pages.length === 0 && (
                <div className="bg-white p-20 rounded-3xl border border-dashed border-gray-200 text-center">
                    <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                        </svg>
                    </div>
                    <h3 className="text-gray-900 font-bold">No results found</h3>
                    <p className="text-gray-500 text-sm mt-1">Try changing the filters or dates.</p>
                </div>
            )}

            {/* Modal */}
            {selectedPage && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10">
                    <div
                        className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm animate-in fade-in duration-300"
                        onClick={() => setSelectedPage(null)}
                    ></div>
                    <div className="relative bg-white w-full max-w-4xl max-h-[90vh] rounded-[2rem] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
                        {/* Modal Header */}
                        <div className="px-8 py-6 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
                            <div>
                                <div className="flex items-center gap-3 mb-1">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full">
                                        {selectedPage.site_name || 'Generic'}
                                    </span>
                                    <span className="text-xs font-semibold text-gray-400">
                                        {new Date(selectedPage.published_at || selectedPage.scraped_at).toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' })}
                                    </span>
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 line-clamp-1">{selectedPage.title || selectedPage.url}</h3>
                            </div>
                            <button
                                onClick={() => setSelectedPage(null)}
                                className="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-400 hover:text-gray-600"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {/* Modal Content */}
                        <div className="flex-1 overflow-y-auto p-8 md:p-12">
                            <div className="prose prose-blue max-w-none">
                                {selectedPage.latest_content?.extracted_text ? (
                                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed text-lg">
                                        {selectedPage.latest_content.extracted_text}
                                    </div>
                                ) : (
                                    <p className="italic text-gray-400">No content available.</p>
                                )}
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="px-8 py-5 border-t border-gray-100 bg-gray-50/50 flex items-center justify-between">
                            <div className="flex items-center gap-4 text-xs text-gray-400 font-medium">
                                <span>URL Original:</span>
                                <a
                                    href={selectedPage.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-500 hover:underline line-clamp-1"
                                >
                                    {selectedPage.url}
                                </a>
                            </div>
                            <button
                                onClick={() => setSelectedPage(null)}
                                className="bg-gray-900 text-white px-6 py-2 rounded-xl font-bold text-sm hover:bg-gray-800 transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
