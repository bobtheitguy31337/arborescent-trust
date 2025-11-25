import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, RequireAuth, RequireAdmin } from './lib/auth';
import Login from './pages/Login';
import Register from './pages/Register';
import DashboardLayout from './components/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import TreeView from './pages/TreeView';
import PruneOperations from './pages/PruneOperations';
import AuditLog from './pages/AuditLog';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected admin routes */}
          <Route
            path="/dashboard"
            element={
              <RequireAdmin>
                <DashboardLayout />
              </RequireAdmin>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="users" element={<Users />} />
            <Route path="tree" element={<TreeView />} />
            <Route path="prune" element={<PruneOperations />} />
            <Route path="audit" element={<AuditLog />} />
          </Route>

          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* 404 */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
