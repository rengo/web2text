import React, { useEffect, useState, useRef } from 'react';
import { API_URL } from '../api';

interface LogEntry {
    message: string;
    level: 'info' | 'warning' | 'error' | 'success';
    extra: any;
    timestamp: string;
}

const LogViewer: React.FC = () => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const endRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const apiUrl = API_URL;
        const wsUrl = apiUrl.replace('http', 'ws') + '/ws/logs';
        let isCleaningUp = false;

        console.log('Connecting to WebSocket:', wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            if (isCleaningUp) return;
            console.log('Connected to WebSocket');
            setIsConnected(true);
            addLog({ message: 'Connected to log stream...', level: 'info', extra: {}, timestamp: new Date().toISOString() });
        };

        ws.onmessage = (event) => {
            if (isCleaningUp) return;
            try {
                const data = JSON.parse(event.data);
                const payload = typeof data === 'string' ? JSON.parse(data) : data;

                addLog({
                    message: payload.message,
                    level: payload.level,
                    extra: payload.extra,
                    timestamp: new Date().toISOString()
                });
            } catch (e) {
                console.error('Failed to parse log message:', event.data, e);
            }
        };

        ws.onclose = () => {
            if (isCleaningUp) return;
            console.log('Disconnected from WebSocket');
            setIsConnected(false);
            addLog({ message: 'Disconnected from log stream.', level: 'error', extra: {}, timestamp: new Date().toISOString() });
        };

        ws.onerror = (error) => {
            if (isCleaningUp) return;
            console.error('WebSocket error:', error);
        };

        return () => {
            isCleaningUp = true;
            ws.close();
        };
    }, []);

    const addLog = (log: LogEntry) => {
        setLogs(prev => {
            const newLogs = [...prev, log];
            if (newLogs.length > 200) {
                return newLogs.slice(newLogs.length - 200);
            }
            return newLogs;
        });
    };

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'error': return 'text-red-400';
            case 'warning': return 'text-yellow-400';
            case 'success': return 'text-green-400';
            default: return 'text-gray-300';
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)] bg-[#1e1e1e] rounded-xl overflow-hidden border border-gray-700 shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 bg-[#252526] border-b border-black/20">
                <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                    <span className="text-gray-400 font-mono text-xs font-bold uppercase tracking-wider">
                        {isConnected ? 'LIVE CONNECTION' : 'DISCONNECTED'}
                    </span>
                </div>
                <button
                    onClick={() => setLogs([])}
                    className="text-xs text-gray-500 hover:text-white transition-colors uppercase font-bold"
                >
                    Clear Console
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1 custom-scrollbar">
                {logs.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600">
                        <p>Waiting for events...</p>
                    </div>
                )}

                {logs.map((log, i) => (
                    <div key={i} className="flex gap-3 hover:bg-white/5 p-0.5 rounded px-2 transition-colors">
                        <span className="text-gray-600 shrink-0 text-[10px] py-0.5 select-none w-20">
                            {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <div className="flex-1 break-all">
                            <span className={`${getLevelColor(log.level)} font-medium mr-2`}>
                                [{log.level.toUpperCase()}]
                            </span>
                            <span className="text-gray-300">
                                {log.message}
                            </span>
                            {log.extra && Object.keys(log.extra).length > 0 && (
                                <span className="ml-2 text-gray-500 text-xs">
                                    {JSON.stringify(log.extra)}
                                </span>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={endRef} />
            </div>
        </div>
    );
};

export default LogViewer;
