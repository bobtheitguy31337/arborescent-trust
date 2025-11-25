import React, { useState, useEffect } from 'react';
import { Loader } from 'lucide-react';
import { apiClient } from '../lib/api';
import { TrustBadge } from '../components/TrustBadge';
import type { Notification } from '../types';

export const Notifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const data = await apiClient.getNotifications();
      setNotifications(data.notifications);
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Failed to load notifications', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id: string) => {
    try {
      await apiClient.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (error) {
      console.error('Failed to mark notification as read', error);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiClient.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / 1000 / 60 / 60);
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'just now';
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div>
      <div className="border-b border-gray-800 p-4 sticky top-0 bg-black/80 backdrop-blur-sm z-10">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">
            Notifications {unreadCount > 0 && <span className="text-primary">({unreadCount})</span>}
          </h1>
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} className="text-sm text-primary hover:underline">
              Mark all as read
            </button>
          )}
        </div>
      </div>

      <div>
        {notifications.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-xl mb-2">No notifications yet</p>
            <p>When someone interacts with you, you'll see it here</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              onClick={() => !notification.read && handleMarkRead(notification.id)}
              className={`border-b border-gray-800 p-4 cursor-pointer transition-colors ${
                notification.read ? 'bg-transparent' : 'bg-primary/5 hover:bg-primary/10'
              }`}
            >
              <div className="flex gap-3">
                {notification.actor && (
                  <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center font-bold flex-shrink-0">
                    {notification.actor.display_name?.[0] || notification.actor.username[0].toUpperCase()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  {notification.actor && (
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold">
                        {notification.actor.display_name || notification.actor.username}
                      </span>
                      <TrustBadge
                        status={notification.actor.status}
                        isCoreMember={notification.actor.is_core_member}
                        size="sm"
                      />
                    </div>
                  )}
                  <p className="text-gray-300">{notification.message}</p>
                  <p className="text-sm text-gray-500 mt-1">{formatDate(notification.created_at)}</p>
                </div>
                {!notification.read && (
                  <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-2" />
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

