import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function FLStatus() {
  const trainingData = [
    { round: 1, accuracy: 65, loss: 1.2 },
    { round: 2, accuracy: 78, loss: 0.8 },
    { round: 3, accuracy: 85, loss: 0.5 },
    { round: 4, accuracy: 92, loss: 0.3 },
    { round: 5, accuracy: 95, loss: 0.15 },
    { round: 6, accuracy: 97.2, loss: 0.08 },
    { round: 7, accuracy: 98.4, loss: 0.05 },
  ];

  const clients = [
    { id: 'node-alpha-01', ip: '10.0.0.12', trust: 0.99, status: 'Active' },
    { id: 'node-beta-04', ip: '10.0.0.45', trust: 0.95, status: 'Active' },
    { id: 'node-gamma-09', ip: '10.0.1.8', trust: 0.42, status: 'Warning' },
    { id: 'node-delta-12', ip: '10.0.2.11', trust: 0.0, status: 'Banned' },
  ];

  return (
    <div className="space-y-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">Federated Learning Status</h1>
        <p className="text-slate-400 mt-1">Global model convergence and edge client trust metrics.</p>
      </header>

      <div className="glass-panel h-96 mb-8">
        <h2 className="text-lg font-semibold text-white mb-6">Global Training Curve (FedProx)</h2>
        <ResponsiveContainer width="100%" height="80%">
          <LineChart data={trainingData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="round" stroke="#94a3b8" />
            <YAxis yAxisId="left" stroke="#3b82f6" domain={[0, 100]} />
            <YAxis yAxisId="right" orientation="right" stroke="#ef4444" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="accuracy" name="Accuracy (%)" stroke="#3b82f6" activeDot={{ r: 8 }} strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="loss" name="Loss" stroke="#ef4444" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="glass-panel">
        <h2 className="text-lg font-semibold text-white mb-4">Edge Client Trust Registry</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 text-sm">
                <th className="py-3 px-4 font-medium">Node ID</th>
                <th className="py-3 px-4 font-medium">IP Address</th>
                <th className="py-3 px-4 font-medium">Trust Score</th>
                <th className="py-3 px-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c, idx) => (
                <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors">
                  <td className="py-3 px-4 font-mono text-sm text-slate-300">{c.id}</td>
                  <td className="py-3 px-4 font-mono text-sm text-slate-400">{c.ip}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${c.trust > 0.8 ? 'bg-success' : c.trust > 0.3 ? 'bg-warning' : 'bg-danger'}`}
                          style={{ width: `${c.trust * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium text-slate-300">{c.trust.toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      c.status === 'Active' ? 'bg-success/20 text-success' :
                      c.status === 'Banned' ? 'bg-danger/20 text-danger' :
                      'bg-warning/20 text-warning'
                    }`}>
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
