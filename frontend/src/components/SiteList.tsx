import React, { useEffect, useState } from 'react';
import { fetchSites, toggleSite, createSite, request } from '../api';

export default function SiteList() {
    const [sites, setSites] = useState<any[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [newSite, setNewSite] = useState({
        name: '',
        base_url: '',
        enabled: true
    });

    const [editingSite, setEditingSite] = useState<any | null>(null);
    const [editForm, setEditForm] = useState({
        name: '',
        sitemap_url: ''
    });

    const load = async () => {
        const data = await fetchSites();
        setSites(data);
    };

    useEffect(() => { load(); }, []);

    const handleToggle = async (id: string, current: boolean) => {
        await toggleSite(id, !current);
        load();
    };

    const handleRun = async (id: string) => {
        try {
            await request(`/sites/${id}/run`, { method: 'POST' });
            alert("Run triggered");
        } catch (e) {
            alert("Failed to trigger run: " + (e as Error).message);
        }
    }

    const openEdit = (site: any) => {
        setEditingSite(site);
        setEditForm({
            name: site.name,
            sitemap_url: site.sitemap_url || ''
        });
    };

    const handleSaveEdit = async () => {
        if (!editingSite) return;
        try {
            const { updateSite } = await import('../api');
            await updateSite(editingSite.id, editForm);
            setEditingSite(null);
            load();
        } catch (e) {
            alert("Failed to update site: " + (e as Error).message);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const siteToCreate = {
            ...newSite,
            crawl_strategy: 'sitemap' // Keep default for schema compatibility
        };
        await createSite(siteToCreate);
        setNewSite({ name: '', base_url: '', enabled: true });
        setShowForm(false);
        load();
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 md:p-6 rounded-2xl shadow-sm border border-gray-100">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">Configured Sites</h2>
                    <p className="text-gray-500 text-sm mt-1">Manage the websites to be scraped and their discovery settings.</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center space-x-2"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                    </svg>
                    <span>Add New Site</span>
                </button>
            </div>

            {showForm && (
                <div className="bg-white p-4 md:p-8 rounded-2xl shadow-lg border border-gray-100 animate-in fade-in slide-in-from-top-4 duration-300">
                    <h3 className="text-lg font-bold mb-6 text-gray-800">New Site Configuration</h3>
                    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700">Site Name</label>
                            <input
                                required
                                value={newSite.name}
                                onChange={e => setNewSite({ ...newSite, name: e.target.value })}
                                placeholder="e.g. TechCrunch"
                                className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-700">Base URL</label>
                            <input
                                required
                                value={newSite.base_url}
                                onChange={e => setNewSite({ ...newSite, base_url: e.target.value })}
                                placeholder="https://example.com"
                                className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                            />
                        </div>
                        <div className="md:col-span-2 flex items-end">
                            <button type="submit" className="w-full bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200">
                                Create Configuration
                            </button>
                        </div>
                    </form>
                    <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
                        <p className="text-xs text-blue-700 leading-relaxed">
                            <strong>Note:</strong> Just provide the name and the URL. The system automatically finds the sitemap, RSS feed, or discovers links to extract the content.
                        </p>
                    </div>
                </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-100">
                    <thead className="bg-gray-50/50">
                        <tr>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Name</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest hidden xl:table-cell">ID</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest hidden 2xl:table-cell">URL</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest hidden lg:table-cell">Strategy</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Indexed</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Pending</th>
                            <th className="px-4 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Status</th>
                            <th className="px-4 py-4 text-right text-xs font-bold text-gray-400 uppercase tracking-widest">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                        {sites.map(site => (
                            <tr key={site.id} className="hover:bg-gray-50/50 transition-colors">
                                <td className="px-4 py-4 whitespace-nowrap">
                                    <div className="flex items-center space-x-2">
                                        <span className="font-semibold text-gray-900">{site.name}</span>
                                        {site.config_warning && (
                                            <div className="group relative">
                                                <svg className="w-5 h-5 text-orange-500 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                                </svg>
                                                <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 w-48 p-2 bg-gray-900 text-white text-[10px] rounded shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                                                    {site.config_warning}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </td>
                                <td className="px-4 py-4 whitespace-nowrap hidden xl:table-cell">
                                    <div className="flex items-center space-x-2">
                                        <code className="bg-gray-50 px-2 py-1 rounded text-xs text-gray-600 font-mono">{site.id.substring(0, 8)}...</code>
                                        <button
                                            onClick={() => {
                                                navigator.clipboard.writeText(site.id);
                                                setCopiedId(site.id);
                                                setTimeout(() => setCopiedId(null), 2000);
                                            }}
                                            className={`${copiedId === site.id ? 'text-green-600' : 'text-gray-400 hover:text-blue-600'} transition-colors`}
                                            title="Copy full ID"
                                        >
                                            {copiedId === site.id ? (
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                                </svg>
                                            ) : (
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                                                </svg>
                                            )}
                                        </button>
                                    </div>
                                </td>
                                <td className="px-4 py-4 whitespace-nowrap text-gray-500 text-sm hidden 2xl:table-cell max-w-[200px] truncate">{site.base_url}</td>
                                <td className="px-4 py-4 whitespace-nowrap hidden lg:table-cell">
                                    <span className="bg-purple-50 text-purple-600 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider">
                                        {site.crawl_strategy}
                                    </span>
                                </td>
                                <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-gray-700">
                                    {site.pages_count || 0}
                                </td>
                                <td className="px-4 py-4 whitespace-nowrap text-sm font-semibold text-orange-600">
                                    {site.pending_count || 0}
                                </td>
                                <td className="px-4 py-4 whitespace-nowrap">
                                    <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full border ${site.enabled
                                        ? 'bg-green-50 text-green-700 border-green-100'
                                        : 'bg-red-50 text-red-700 border-red-100'
                                        }`}>
                                        {site.enabled ? 'Active' : 'Disabled'}
                                    </span>
                                </td>
                                <td className="px-4 py-4 whitespace-nowrap text-right space-x-1 sm:space-x-3">
                                    <button
                                        onClick={() => openEdit(site)}
                                        className="text-blue-600 hover:text-blue-700 p-1.5"
                                        title="Edit Site"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                        </svg>
                                    </button>
                                    <button
                                        onClick={() => handleToggle(site.id, site.enabled)}
                                        className={`p-1.5 transition-colors ${site.enabled ? 'text-orange-600 hover:text-orange-700' : 'text-green-600 hover:text-green-700'}`}
                                        title={site.enabled ? 'Disable Site' : 'Enable Site'}
                                    >
                                        {site.enabled ? (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                                            </svg>
                                        ) : (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => handleRun(site.id)}
                                        className="bg-gray-100 text-gray-700 px-2.5 py-1.5 rounded-lg text-xs font-bold hover:bg-gray-200 transition-colors hidden sm:inline-block"
                                    >
                                        Run
                                    </button>
                                    <button
                                        onClick={() => handleRun(site.id)}
                                        className="text-gray-600 hover:text-gray-900 p-1.5 sm:hidden"
                                        title="Run Now"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </button>
                                    <button
                                        onClick={async () => {
                                            if (window.confirm(`Are you sure you want to delete ${site.name}?`)) {
                                                const { deleteSite } = await import('../api');
                                                await deleteSite(site.id);
                                                load();
                                            }
                                        }}
                                        className="text-red-500 hover:text-red-700 p-1.5"
                                        title="Delete Site"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-4v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {sites.length === 0 && (
                    <div className="p-12 text-center">
                        <p className="text-gray-400 font-medium">No sites configured yet.</p>
                    </div>
                )}
            </div>

            {/* Edit Modal */}
            {editingSite && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100] animate-in fade-in duration-200">
                    <div className="bg-white p-8 rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg mx-4 scale-in-center animate-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold text-gray-900">Edit Site: {editingSite.name}</h3>
                            <button onClick={() => setEditingSite(null)} className="text-gray-400 hover:text-gray-600">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l18 18" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700">Name</label>
                                <input
                                    value={editForm.name}
                                    onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                                    className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700">Sitemap URL</label>
                                <input
                                    value={editForm.sitemap_url}
                                    onChange={e => setEditForm({ ...editForm, sitemap_url: e.target.value })}
                                    placeholder="https://example.com/sitemap.xml"
                                    className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                                />
                                <p className="text-[10px] text-gray-400 italic">Leave empty to allow the system to auto-discover it.</p>
                            </div>

                            <div className="space-y-2 opacity-60">
                                <label className="text-sm font-semibold text-gray-700">Base URL (Read Only)</label>
                                <input
                                    disabled
                                    value={editingSite.base_url}
                                    className="w-full border border-gray-100 bg-gray-50 rounded-xl px-4 py-3 cursor-not-allowed"
                                />
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => setEditingSite(null)}
                                    className="flex-1 px-6 py-3 rounded-xl font-bold text-gray-600 hover:bg-gray-100 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSaveEdit}
                                    className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200"
                                >
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
