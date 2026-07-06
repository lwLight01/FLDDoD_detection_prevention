import { useState } from 'react';

export default function Mitigation() {
  const [targetIp, setTargetIp] = useState('');
  const [action, setAction] = useState('RATE_LIMIT');
  
  const rules = [
    { id: 'r-001', target: '192.168.1.50', action: 'QUARANTINE', status: 'ACTIVE', ttl: '45m' },
    { id: 'r-002', target: '10.0.0.5', action: 'RATE_LIMIT', status: 'ACTIVE', ttl: '12m' },
    { id: 'r-003', target: '172.16.2.11', action: 'ISOLATE', status: 'REVOKED', ttl: '0m' },
  ];

  return (
    <div className="space-y-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">SDN Firewall Control</h1>
        <p className="text-slate-400 mt-1">Manage autonomous rules and execute manual overrides.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel">
          <h2 className="text-lg font-semibold text-white mb-4">Active SDN Rules</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400 text-sm">
                  <th className="py-3 px-4 font-medium">Rule ID</th>
                  <th className="py-3 px-4 font-medium">Target IP</th>
                  <th className="py-3 px-4 font-medium">Action</th>
                  <th className="py-3 px-4 font-medium">Status</th>
                  <th className="py-3 px-4 font-medium">TTL</th>
                  <th className="py-3 px-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r, idx) => (
                  <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors text-sm">
                    <td className="py-3 px-4 font-mono text-slate-400">{r.id}</td>
                    <td className="py-3 px-4 font-mono text-white">{r.target}</td>
                    <td className="py-3 px-4 font-medium text-slate-300">{r.action}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        r.status === 'ACTIVE' ? 'bg-primary/20 text-primary' : 'bg-slate-700 text-slate-400'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{r.ttl}</td>
                    <td className="py-3 px-4 text-right">
                      {r.status === 'ACTIVE' && (
                        <button className="text-danger hover:text-red-400 text-xs font-medium transition-colors">Revoke</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-panel h-fit">
          <h2 className="text-lg font-semibold text-white mb-4">Manual Override</h2>
          <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Target IP Address</label>
              <input 
                type="text" 
                placeholder="e.g. 192.168.1.100"
                value={targetIp}
                onChange={e => setTargetIp(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-warning focus:ring-1 focus:ring-warning"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Action</label>
              <select 
                value={action}
                onChange={e => setAction(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-warning focus:ring-1 focus:ring-warning"
              >
                <option value="RATE_LIMIT">Rate Limit (L4)</option>
                <option value="ISOLATE">Isolate (VLAN)</option>
                <option value="QUARANTINE">Quarantine (Drop All)</option>
              </select>
            </div>
            <button className="w-full mt-2 bg-warning hover:bg-yellow-600 text-white font-medium py-2 rounded-lg transition-colors flex justify-center items-center">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              Execute Override
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
