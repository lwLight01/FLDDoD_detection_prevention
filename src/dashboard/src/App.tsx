import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Home from './pages/Home';
import AttackMonitor from './pages/AttackMonitor';
import FLStatus from './pages/FLStatus';
import Mitigation from './pages/Mitigation';
import { useAuth } from './hooks/useAuth';

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {isAuthenticated ? (
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="monitor" element={<AttackMonitor />} />
          <Route path="fl-status" element={<FLStatus />} />
          <Route path="mitigation" element={<Mitigation />} />
        </Route>
      ) : (
        <Route path="*" element={<Navigate to="/login" replace />} />
      )}
    </Routes>
  );
}

export default App;
