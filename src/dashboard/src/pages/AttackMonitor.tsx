import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AttackMonitor() {
  // Mock data for Milestone 35
  const shapData = [
    { feature: 'TCP_SYN_Flag', importance: 0.82 },
    { feature: 'Flow_Duration', importance: 0.45 },
    { feature: 'Total_Fwd_Packets', importance: 0.31 },
    { feature: 'Bwd_Packet_Len_Max', importance: 0.22 },
    { feature: 'Fwd_Header_Len', importance: 0.15 },
  ];

  return (
    <div className="space-y-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">XAI Attack Monitor</h1>
        <p className="text-slate-400 mt-1">Explainable AI (SHAP) breakdown of the latest detected anomaly.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel h-96">
          <h2 className="text-lg font-semibold text-white mb-6">Feature Importance (SHAP Values)</h2>
          <ResponsiveContainer width="100%" height="80%">
            <BarChart data={shapData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" stroke="#94a3b8" />
              <YAxis dataKey="feature" type="category" stroke="#94a3b8" width={120} tick={{fill: '#cbd5e1', fontSize: 12}} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#fff' }}
                itemStyle={{ color: '#3b82f6' }}
              />
              <Bar dataKey="importance" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-6">
          <div className="glass-panel relative overflow-hidden">
             <div className="absolute top-0 right-0 w-24 h-24 bg-danger/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
             <h3 className="text-sm font-medium text-slate-400">Diagnosis</h3>
             <p className="text-2xl font-bold text-danger mt-1">SYN Flood Attack</p>
             <p className="text-sm text-slate-300 mt-4 leading-relaxed">
               The FT-Transformer identified anomalous behavior heavily weighted by <span className="text-primary font-bold">TCP_SYN_Flag</span> and <span className="text-primary font-bold">Flow_Duration</span>. 
             </p>
          </div>
          
          <div className="glass-panel border-l-4 border-l-warning">
             <h3 className="text-sm font-medium text-slate-400">Recommended SDN Policy</h3>
             <p className="text-white font-medium mt-2">Rate Limit TCP Traffic on Port 80</p>
             <div className="mt-4 flex space-x-3">
               <button className="flex-1 bg-primary hover:bg-blue-600 text-white py-2 rounded-lg text-sm font-medium transition-colors">Apply Policy</button>
               <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded-lg text-sm font-medium transition-colors">Dismiss</button>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
