import React, { useState, useEffect } from 'react';
import { fetchSettings, updateSetting } from '../api';

interface Setting {
    key: string;
    value: string;
}

export default function Settings() {
    const [interval, setIntervalValue] = useState<number>(10);
    const [lookbackDays, setLookbackDays] = useState<number>(30);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    useEffect(() => {
        fetchSettingsData();
    }, []);

    const fetchSettingsData = async () => {
        try {
            const data = await fetchSettings();
            const intervalSetting = data.find((s: Setting) => s.key === 'scrape_interval_minutes');
            const lookbackSetting = data.find((s: Setting) => s.key === 'lookback_days');

            if (intervalSetting) setIntervalValue(parseInt(intervalSetting.value));
            if (lookbackSetting) setLookbackDays(parseInt(lookbackSetting.value));
        } catch (error) {
            console.error('Error fetching settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);

        try {
            // Save interval
            await updateSetting('scrape_interval_minutes', interval.toString());
            // Save lookback days
            await updateSetting('lookback_days', lookbackDays.toString());

            setMessage({ type: 'success', text: 'Configuración guardada correctamente' });
        } catch (error) {
            setMessage({ type: 'error', text: 'Error al guardar la configuración' });
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl bg-white rounded-3xl shadow-sm border border-slate-200 overflow-hidden transition-all duration-300 hover:shadow-md">
            <div className="p-8">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center">
                        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-slate-800">Scraper Engine</h3>
                        <p className="text-sm text-slate-500">Configure global parameters for the scraping worker</p>
                    </div>
                </div>

                <form onSubmit={handleSave} className="space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <label htmlFor="interval" className="block text-sm font-bold text-slate-700 uppercase tracking-tight mb-2">
                                Frecuencia
                            </label>
                            <div className="relative">
                                <input
                                    type="number"
                                    id="interval"
                                    value={interval}
                                    onChange={(e) => setIntervalValue(parseInt(e.target.value))}
                                    min="1"
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                                    placeholder="Ej: 10"
                                    required
                                />
                                <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                                    <span className="text-sm font-bold text-slate-400 capitalize">min</span>
                                </div>
                            </div>
                            <p className="mt-2 text-xs text-slate-400 font-medium italic">
                                Intervalo entre revisiones de sitios.
                            </p>
                        </div>

                        <div>
                            <label htmlFor="lookback" className="block text-sm font-bold text-slate-700 uppercase tracking-tight mb-2">
                                Ventana de Tiempo
                            </label>
                            <div className="relative">
                                <input
                                    type="number"
                                    id="lookback"
                                    value={lookbackDays}
                                    onChange={(e) => setLookbackDays(parseInt(e.target.value))}
                                    min="1"
                                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium"
                                    placeholder="Ej: 30"
                                    required
                                />
                                <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                                    <span className="text-sm font-bold text-slate-400 capitalize">días</span>
                                </div>
                            </div>
                            <p className="mt-2 text-xs text-slate-400 font-medium italic">
                                Días hacia atrás para filtrar contenido antiguo.
                            </p>
                        </div>
                    </div>

                    {message && (
                        <div className={`p-4 rounded-xl flex items-center gap-3 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'
                            }`}>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                {message.type === 'success' ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                )}
                            </svg>
                            <span className="text-sm font-bold">{message.text}</span>
                        </div>
                    )}

                    <div className="pt-4">
                        <button
                            type="submit"
                            disabled={saving}
                            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-4 px-6 rounded-2xl shadow-lg shadow-blue-200 transition-all flex items-center justify-center gap-2 group"
                        >
                            {saving ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <span>Guardar Cambios</span>
                                    <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
