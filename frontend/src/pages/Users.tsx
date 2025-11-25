import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import type { User } from '../types';
import { Search, Filter, Flag, Shield, Ban, Eye, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  useEffect(() => {
    loadUsers();
  }, [page, statusFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params: any = { page, page_size: 20 };
      if (statusFilter !== 'all') {
        params.status = statusFilter;
      }
      if (searchTerm) {
        params.search = searchTerm;
      }

      const data = await apiClient.getAllUsers(params);
      setUsers(data.users);
      setTotalPages(Math.ceil(data.total / data.page_size));
    } catch (err: any) {
      setError('Failed to load users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadUsers();
  };

  const handleFlagUser = async (userId: string, reason: string) => {
    try {
      await apiClient.flagUser(userId, reason);
      await loadUsers();
    } catch (err) {
      alert('Failed to flag user');
    }
  };

  const handleUnflagUser = async (userId: string) => {
    try {
      await apiClient.unflagUser(userId);
      await loadUsers();
    } catch (err) {
      alert('Failed to unflag user');
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      flagged: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      suspended: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      banned: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return styles[status as keyof typeof styles] || styles.active;
  };

  return (
    <div className="space-y-6">
      {/* Search and filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by username or email..."
                className="input pl-10"
              />
            </div>
          </form>

          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="input"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="flagged">Flagged</option>
              <option value="suspended">Suspended</option>
              <option value="banned">Banned</option>
            </select>

            <button
              onClick={loadUsers}
              className="btn btn-secondary"
            >
              <Filter className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Users table */}
      <div className="card overflow-hidden p-0">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : users.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <AlertCircle className="h-12 w-12 mb-4" />
            <p>No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Invites
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {user.username}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {user.email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(user.status)}`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-900 dark:text-white">
                        {user.role === 'admin' || user.role === 'superadmin' ? (
                          <Shield className="h-4 w-4 text-primary-600 mr-1" />
                        ) : null}
                        {user.role}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {user.invites_used} / {user.invite_quota}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {format(new Date(user.created_at), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => window.open(`/dashboard/tree?user=${user.id}`, '_blank')}
                          className="text-primary-600 hover:text-primary-900 dark:text-primary-400"
                          title="View tree"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        {user.status === 'flagged' ? (
                          <button
                            onClick={() => handleUnflagUser(user.id)}
                            className="text-green-600 hover:text-green-900 dark:text-green-400"
                            title="Unflag user"
                          >
                            <Flag className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => {
                              const reason = prompt('Reason for flagging:');
                              if (reason) handleFlagUser(user.id, reason);
                            }}
                            className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400"
                            title="Flag user"
                          >
                            <Flag className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && users.length > 0 && (
          <div className="bg-gray-50 dark:bg-gray-800 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              Page {page} of {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

