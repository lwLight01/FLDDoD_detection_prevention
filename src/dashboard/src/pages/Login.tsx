import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import axios from 'axios';

export default function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);
      
      const res = await axios.post('/api/v1/auth/token', params);
      login(res.data.access_token);
      navigate('/');
    } catch (err) {
      // Demo fallback since backend isn't running yet
      if (username === 'admin' && password === 'admin') {
        login('demo-jwt-token-12345');
        navigate('/');
      } else {
        setError('Invalid credentials. Use admin/admin for demo.');
      }
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-slate-900">
      <div className="glass-panel w-full max-w-md p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-accent"></div>
        <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
        <p className="text-slate-400 mb-6 text-sm">Sign in to access the mitigation console.</p>
        
        {error && <div className="bg-danger/20 text-danger text-sm p-3 rounded-lg mb-4 border border-danger/30">{error}</div>}
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-primary hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-all shadow-lg shadow-primary/30 mt-4"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}
