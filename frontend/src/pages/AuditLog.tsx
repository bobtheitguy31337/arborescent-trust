import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import type { AuditLogEntry } from '../types';
import { FileText, Filter, Download } from 'lucide-react';
import { format } from 'date-fns';

export default function AuditLog() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Filters
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadLogs();
  }, [page, eventTypeFilter, userIdFilter]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const params: any = { page, page_size: 50 };
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      if (userIdFilter) params.user_id = userIdFilter;

      const data = await apiClient.getAuditLog(params);
      setLogs(data.logs);
      setTotalPages(Math.ceil(data.total / 50));
    } catch (err: any) {
      setError('Failed to load audit logs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleRow = (id: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const getEventTypeBadge = (eventType: string) => {
    const colors: Record<string, string> = {
      token_created: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      token_used: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      token_expired: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
      token_revoked: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      user_pruned: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      quota_adjusted: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      user_flagged: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      user_unflagged: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
    };
    return colors[eventType] || colors.token_created;
  };

  const eventTypes = [
    'token_created',
    'token_used',
    'token_expired',
    'token_revoked',
    'user_pruned',
    'quota_adjusted',
    'user_flagged',
    'user_unflagged',
  ];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Event Type
            </label>
            <select
              value={eventTypeFilter}
              onChange={(e) => {
                setEventTypeFilter(e.target.value);
                setPage(1);
              }}
              className="input"
            >
              <option value="">All Events</option>
              {eventTypes.map((type) => (
                <option key={type} value={type}>
                  {type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              User ID
            </label>
            <input
              type="text"
              value={userIdFilter}
              onChange={(e) => setUserIdFilter(e.target.value)}
              placeholder="Filter by user ID"
              className="input"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setEventTypeFilter('');
                setUserIdFilter('');
                setPage(1);
              }}
              className="btn btn-secondary w-full"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Audit log table */}
      <div className="card overflow-hidden p-0">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Audit Log
            </h3>
            <button className="btn btn-secondary text-sm flex items-center">
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <FileText className="h-12 w-12 mb-4" />
            <p>No audit logs found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Event Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Actor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Target
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {logs.map((log) => (
                  <React.Fragment key={log.id}>
                    <tr
                      className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                      onClick={() => toggleRow(log.id)}
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {format(new Date(log.created_at), 'MMM d, yyyy HH:mm:ss')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getEventTypeBadge(log.event_type)}`}>
                          {log.event_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {log.actor_user_id ? log.actor_user_id.substring(0, 8) + '...' : 'System'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {log.target_user_id ? log.target_user_id.substring(0, 8) + '...' : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {log.ip_address || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-primary-600 dark:text-primary-400">
                        {expandedRows.has(log.id) ? 'Hide' : 'Show'}
                      </td>
                    </tr>
                    {expandedRows.has(log.id) && (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 bg-gray-50 dark:bg-gray-900">
                          <div className="text-sm">
                            <p className="font-medium text-gray-900 dark:text-white mb-2">Event Data:</p>
                            <pre className="bg-white dark:bg-gray-800 p-4 rounded-lg overflow-auto text-xs">
                              {JSON.stringify(log.event_data, null, 2)}
                            </pre>
                            {log.user_agent && (
                              <div className="mt-2">
                                <p className="font-medium text-gray-900 dark:text-white">User Agent:</p>
                                <p className="text-gray-600 dark:text-gray-400 text-xs mt-1">
                                  {log.user_agent}
                                </p>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && logs.length > 0 && (
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

