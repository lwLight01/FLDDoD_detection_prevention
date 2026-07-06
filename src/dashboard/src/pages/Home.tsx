import { useEffect, useState } from 'react';

export default function Home() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [wsStatus, setWsStatus] = useState('Connecting...');

  useEffect(() => {
    // Attempt WebSocket connection for Milestone 34
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use localhost:8000 for local dev if vite proxy is bypassed, or just standard proxy route
    const wsUrl = import.meta.env.DEV ? 'ws://localhost:8000/ws/alerts' : `${protocol}//${window.location.host}/ws/alerts`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => setWsStatus('Connected');
    ws.onclose = () => setWsStatus('Disconnected');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setAlerts(prev => [data, ...prev].slice(0, 10)); // Keep last 10
    };

    return () => ws.close();
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">System Overview</h1>
          <p className="text-slate-400 mt-1">Real-time status of the DDoS detection network.</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="relative flex h-3 w-3">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${wsStatus === 'Connected' ? 'bg-success' : 'bg-warning'}`}></span>
            <span className={`relative inline-flex rounded-full h-3 w-3 ${wsStatus === 'Connected' ? 'bg-success' : 'bg-warning'}`}></span>
          </span>
          <span className="text-sm text-slate-300">Live Stream: {wsStatus}</span>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel">
          <h3 className="text-slate-400 text-sm font-medium">Active Nodes</h3>
          <p className="text-4xl font-bold text-white mt-2">12</p>
          <p className="text-xs text-success mt-2">↑ 2 from last round</p>
        </div>
        <div className="glass-panel">
          <h3 className="text-slate-400 text-sm font-medium">Global Model Accuracy</h3>
          <p className="text-4xl font-bold text-primary mt-2">98.4%</p>
          <p className="text-xs text-success mt-2">Converged (FedAvg)</p>
        </div>
        <div className="glass-panel">
          <h3 className="text-slate-400 text-sm font-medium">Threats Blocked (24h)</h3>
          <p className="text-4xl font-bold text-danger mt-2">1,204</p>
          <p className="text-xs text-slate-400 mt-2">Across all SDN edges</p>
        </div>
      </div>

      <div className="glass-panel mt-8">
        <h2 className="text-xl font-bold text-white mb-4">Recent Alerts Feed</h2>
        {alerts.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            No active threats detected. Listening for alerts...
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert, idx) => (
              <div key={idx} className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 flex justify-between items-center">
                <div>
                  <span className={`px-2 py-1 rounded text-xs font-bold mr-3 ${
                    alert.severity === 'CRITICAL' ? 'bg-danger/20 text-danger' : 
                    alert.severity === 'HIGH' ? 'bg-warning/20 text-warning' : 
                    'bg-primary/20 text-primary'
                  }`}>
                    {alert.severity}
                  </span>
                  <span className="text-sm text-slate-300">Alert ID: {alert.alert_id}</span>
                </div>
                <div className="text-sm">
                  {alert.mitigation_triggered ? (
                    <span className="text-success font-medium">⚡ Mitigation Deployed</span>
                  ) : (
                    <span className="text-slate-500">Logging only</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
