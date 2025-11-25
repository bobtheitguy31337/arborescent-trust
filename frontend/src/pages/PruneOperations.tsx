import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import type { PruneOperation, PruneResponse } from '../types';
import { Scissors, AlertTriangle, CheckCircle, History, Search } from 'lucide-react';
import { format } from 'date-fns';

export default function PruneOperations() {
  const [history, setHistory] = useState<PruneOperation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Prune form state
  const [userId, setUserId] = useState('');
  const [reason, setReason] = useState('');
  const [dryRun, setDryRun] = useState(true);
  const [previewData, setPreviewData] = useState<PruneResponse | null>(null);
  const [pruning, setPruning] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getPruneHistory();
      setHistory(data);
    } catch (err: any) {
      setError('Failed to load prune history');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setPreviewData(null);

    try {
      setPruning(true);
      const result = await apiClient.pruneUser({
        root_user_id: userId,
        reason,
        dry_run: true,
      });
      setPreviewData(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to preview prune operation');
    } finally {
      setPruning(false);
    }
  };

  const handleExecute = async () => {
    if (!confirm(`Are you sure you want to prune ${previewData?.affected_count} users? This action cannot be undone.`)) {
      return;
    }

    setError('');

    try {
      setPruning(true);
      const result = await apiClient.pruneUser({
        root_user_id: userId,
        reason,
        dry_run: false,
      });
      
      alert(`Successfully pruned ${result.affected_count} users`);
      setPreviewData(null);
      setUserId('');
      setReason('');
      await loadHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute prune operation');
    } finally {
      setPruning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Warning banner */}
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mr-3 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
              Surgical Pruning
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              Pruning removes an entire branch (user and all descendants). Always preview before executing.
              All operations are logged and can be audited.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Prune form */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Scissors className="h-5 w-5 mr-2 text-red-600" />
          New Prune Operation
        </h3>

        <form onSubmit={handlePreview} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Root User ID
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="User ID to prune (root of branch)"
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Reason for Pruning
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Describe why this branch is being pruned (e.g., coordinated bot network, spam)"
              className="input min-h-[100px]"
              required
            />
          </div>

          <button
            type="submit"
            disabled={pruning}
            className="btn btn-secondary flex items-center"
          >
            {pruning ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            ) : (
              <Search className="mr-2 h-5 w-5" />
            )}
            Preview Affected Users
          </button>
        </form>
      </div>

      {/* Preview results */}
      {previewData && (
        <div className="card border-2 border-yellow-400 dark:border-yellow-600">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 text-yellow-600" />
              Preview: {previewData.affected_count} Users Will Be Affected
            </h3>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4 max-h-96 overflow-y-auto">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Affected Users:
            </p>
            <ul className="space-y-2">
              {previewData.affected_users?.slice(0, 50).map((user: any) => (
                <li key={user.id} className="text-sm text-gray-600 dark:text-gray-400">
                  • {user.username} ({user.email}) - Created: {new Date(user.created_at).toLocaleDateString()}
                </li>
              ))}
              {previewData.affected_users && previewData.affected_users.length > 50 && (
                <li className="text-sm text-gray-500 dark:text-gray-500 italic">
                  ... and {previewData.affected_users.length - 50} more users
                </li>
              )}
            </ul>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleExecute}
              disabled={pruning}
              className="btn btn-danger flex items-center"
            >
              {pruning ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              ) : (
                <Scissors className="mr-2 h-5 w-5" />
              )}
              Execute Prune ({previewData.affected_count} users)
            </button>
            <button
              onClick={() => setPreviewData(null)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* History */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <History className="h-5 w-5 mr-2" />
            Prune History
          </h3>
          <button onClick={loadHistory} className="btn btn-secondary text-sm">
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : history.length === 0 ? (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            No prune operations recorded
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Root User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Affected
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {history.map((op) => (
                  <tr key={op.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {format(new Date(op.created_at), 'MMM d, yyyy HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {op.root_user_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {op.affected_user_count} users
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400 max-w-xs truncate">
                      {op.reason}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          op.status === 'completed'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : op.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                        }`}
                      >
                        {op.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

