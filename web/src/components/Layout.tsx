import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Home, Bell, User, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../lib/auth';
import { TrustBadge } from './TrustBadge';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto max-w-7xl flex">
        {/* Sidebar */}
        <div className="w-64 border-r border-gray-800 h-screen sticky top-0 flex flex-col">
          <div className="p-4">
            <h1 className="text-2xl font-bold text-primary mb-8">Arborescent</h1>
            
            <nav className="space-y-2">
              <Link
                to="/"
                className="flex items-center gap-4 text-xl p-3 rounded-full hover:bg-gray-900 transition-colors"
              >
                <Home className="w-7 h-7" />
                <span>Home</span>
              </Link>
              
              <Link
                to="/notifications"
                className="flex items-center gap-4 text-xl p-3 rounded-full hover:bg-gray-900 transition-colors"
              >
                <Bell className="w-7 h-7" />
                <span>Notifications</span>
              </Link>
              
              <Link
                to={`/profile/${user.username}`}
                className="flex items-center gap-4 text-xl p-3 rounded-full hover:bg-gray-900 transition-colors"
              >
                <User className="w-7 h-7" />
                <span>Profile</span>
              </Link>

              {user.is_admin && (
                <a
                  href="/admin"
                  className="flex items-center gap-4 text-xl p-3 rounded-full hover:bg-gray-900 transition-colors text-purple-400"
                >
                  <Shield className="w-7 h-7" />
                  <span>Admin</span>
                </a>
              )}
            </nav>
          </div>

          <div className="mt-auto p-4 border-t border-gray-800">
            <div className="flex items-center gap-3 p-3 rounded-full hover:bg-gray-900 cursor-pointer transition-colors">
              <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center font-bold">
                {user.display_name?.[0] || user.username[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-bold truncate flex items-center gap-2">
                  {user.display_name || user.username}
                  <TrustBadge status={user.status} isCoreMember={user.is_core_member} size="sm" />
                </div>
                <div className="text-gray-500 text-sm truncate">@{user.username}</div>
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-red-500 p-2 rounded-full hover:bg-red-500/10 transition-colors"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 border-r border-gray-800 max-w-2xl">
          {children}
        </div>

        {/* Right sidebar - Trending/Suggestions */}
        <div className="w-80 p-4 hidden xl:block">
          <div className="bg-gray-900 rounded-2xl p-4 mb-4">
            <h2 className="text-xl font-bold mb-4">About Arborescent</h2>
            <p className="text-gray-400 text-sm mb-3">
              An invite-only social network with built-in trust and accountability.
            </p>
            <p className="text-gray-400 text-sm">
              Your trust level is based on your network health. Bad actors affect their entire invite tree.
            </p>
          </div>

          <div className="bg-gray-900 rounded-2xl p-4">
            <h2 className="text-xl font-bold mb-4">Your Invites</h2>
            <div className="space-y-3">
              <div className="text-gray-400 text-sm">
                <span className="text-white font-bold text-lg">{user.invites_available || 0}</span> invites remaining
              </div>
              <Link to="/invites" className="btn-primary block text-center text-sm">
                Manage Invites
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

