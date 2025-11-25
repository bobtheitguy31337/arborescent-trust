import React from 'react';
import { Sprout, Leaf, TreeDeciduous, Shield } from 'lucide-react';

interface TrustBadgeProps {
  status: string;
  isCoreMember: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({ status, isCoreMember, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  if (isCoreMember) {
    return (
      <span className="inline-flex items-center gap-1 bg-purple-600 text-white px-2 py-0.5 rounded-full text-xs font-medium">
        <Shield className={sizeClasses[size]} />
        Core
      </span>
    );
  }

  // Trust level badges based on account age/health (simplified for now)
  const badge = {
    active: { icon: TreeDeciduous, color: 'bg-green-600', label: 'Tree' },
    flagged: { icon: Leaf, color: 'bg-yellow-600', label: 'Branch' },
    suspended: { icon: Sprout, color: 'bg-gray-600', label: 'Suspended' },
    banned: { icon: Sprout, color: 'bg-red-600', label: 'Banned' },
  }[status] || { icon: Sprout, color: 'bg-green-600', label: 'Seedling' };

  const Icon = badge.icon;

  return (
    <span className={`inline-flex items-center gap-1 ${badge.color} text-white px-2 py-0.5 rounded-full text-xs font-medium`}>
      <Icon className={sizeClasses[size]} />
      {badge.label}
    </span>
  );
};

