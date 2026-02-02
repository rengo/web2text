import React, { useEffect, useState } from 'react';
import { fetchSites, toggleSite, createSite, request } from '../api';

export default function SiteList() {
    const [sites, setSites] = useState<any[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [newSite, setNewSite] = useState({
        name: '',
        base_url: '',
        enabled: true
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
            <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
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
                <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 animate-in fade-in slide-in-from-top-4 duration-300">
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

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-100">
                    <thead className="bg-gray-50/50">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Name</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">URL</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Strategy</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Indexed Pages</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Pending</th>
                            <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-widest">Status</th>
                            <th className="px-6 py-4 text-right text-xs font-bold text-gray-400 uppercase tracking-widest">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                        {sites.map(site => (
                            <tr key={site.id} className="hover:bg-gray-50/50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">{site.name}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-sm">{site.base_url}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="bg-purple-50 text-purple-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                                        {site.crawl_strategy}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-700">
                                    {site.pages_count || 0}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-orange-600">
                                    {site.pending_count || 0}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full border ${site.enabled
                                        ? 'bg-green-50 text-green-700 border-green-100'
                                        : 'bg-red-50 text-red-700 border-red-100'
                                        }`}>
                                        {site.enabled ? 'Active' : 'Disabled'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right space-x-3">
                                    <button
                                        onClick={() => handleToggle(site.id, site.enabled)}
                                        className={`font-bold text-sm ${site.enabled ? 'text-orange-600 hover:text-orange-700' : 'text-green-600 hover:text-green-700'}`}
                                    >
                                        {site.enabled ? 'Disable' : 'Enable'}
                                    </button>
                                    <button
                                        onClick={() => handleRun(site.id)}
                                        className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-sm font-bold hover:bg-gray-200 transition-colors"
                                    >
                                        Run
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
        </div>
    );
}
