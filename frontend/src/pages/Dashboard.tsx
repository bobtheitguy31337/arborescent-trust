import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';
import type { AdminStats } from '../types';
import { Users, UserCheck, UserX, Flag, TrendingUp, Calendar } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await apiClient.getAdminStats();
      setStats(data);
    } catch (err: any) {
      setError('Failed to load dashboard statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
        {error}
      </div>
    );
  }

  if (!stats) return null;

  const statCards = [
    {
      name: 'Total Users',
      value: stats.total_users.toLocaleString(),
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      name: 'Active Users',
      value: stats.active_users.toLocaleString(),
      icon: UserCheck,
      color: 'bg-green-500',
    },
    {
      name: 'Flagged Users',
      value: stats.flagged_users.toLocaleString(),
      icon: Flag,
      color: 'bg-yellow-500',
    },
    {
      name: 'Banned Users',
      value: stats.banned_users.toLocaleString(),
      icon: UserX,
      color: 'bg-red-500',
    },
  ];

  const inviteStats = [
    {
      name: 'Total Invites Issued',
      value: stats.total_invites_issued.toLocaleString(),
    },
    {
      name: 'Invites Used',
      value: stats.total_invites_used.toLocaleString(),
    },
    {
      name: 'Usage Rate',
      value: stats.total_invites_issued > 0
        ? `${((stats.total_invites_used / stats.total_invites_issued) * 100).toFixed(1)}%`
        : '0%',
    },
  ];

  const recentActivity = [
    {
      name: 'Registrations (24h)',
      value: stats.recent_registrations_24h.toLocaleString(),
      icon: Calendar,
    },
    {
      name: 'Registrations (7d)',
      value: stats.recent_registrations_7d.toLocaleString(),
      icon: Calendar,
    },
    {
      name: 'Avg Health Score',
      value: stats.avg_health_score.toFixed(1),
      icon: TrendingUp,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome message */}
      <div className="card bg-gradient-to-r from-primary-500 to-primary-600 text-white">
        <h2 className="text-2xl font-bold mb-2">Welcome to the Admin Dashboard</h2>
        <p className="text-primary-100">
          Monitor user activity, manage invite trees, and maintain system health.
        </p>
      </div>

      {/* User statistics */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          User Statistics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((stat) => (
            <div key={stat.name} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
                    {stat.value}
                  </p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Invite statistics */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Invite System
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {inviteStats.map((stat) => (
            <div key={stat.name} className="card">
              <p className="text-sm text-gray-600 dark:text-gray-400">{stat.name}</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {stat.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent activity */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent Activity
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recentActivity.map((stat) => (
            <div key={stat.name} className="card">
              <div className="flex items-center">
                <stat.icon className="h-5 w-5 text-primary-600 mr-3" />
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                    {stat.value}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System health */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          System Health
        </h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600 dark:text-gray-400">Average Health Score</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {stats.avg_health_score.toFixed(1)}/100
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${stats.avg_health_score}%` }}
              />
            </div>
          </div>

          {stats.flagged_users > 0 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
              <div className="flex items-center">
                <Flag className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>{stats.flagged_users}</strong> users are flagged for review.{' '}
                  <a href="/dashboard/users?status=flagged" className="underline font-medium">
                    Review now
                  </a>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

