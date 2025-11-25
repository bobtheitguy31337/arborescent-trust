// API Types for Arborescent Trust

export interface User {
  id: string;
  email: string;
  username: string;
  is_core_member: boolean;
  invite_quota: number;
  invites_used: number;
  invited_by_user_id: string | null;
  status: 'active' | 'suspended' | 'banned' | 'flagged';
  role: 'user' | 'admin' | 'superadmin';
  created_at: string;
  last_login_at: string | null;
  registration_ip: string | null;
}

export interface InviteToken {
  id: string;
  token: string;
  created_by_user_id: string;
  used_by_user_id: string | null;
  is_used: boolean;
  expires_at: string;
  is_revoked: boolean;
  created_at: string;
  used_at: string | null;
}

export interface HealthScore {
  id: number;
  user_id: string;
  subtree_size: number;
  subtree_active_count: number;
  subtree_flagged_count: number;
  subtree_banned_count: number;
  direct_invitee_health: number;
  subtree_health: number;
  overall_health: number;
  max_depth_below: number;
  maturity_level: 'branch' | 'supporting_trunk' | 'core';
  calculated_at: string;
}

export interface AuditLogEntry {
  id: number;
  event_type: string;
  actor_user_id: string | null;
  target_user_id: string | null;
  invite_token_id: string | null;
  event_data: Record<string, any>;
  created_at: string;
  ip_address: string | null;
  user_agent: string | null;
}

export interface PruneOperation {
  id: string;
  root_user_id: string;
  affected_user_count: number;
  reason: string;
  executed_by_user_id: string;
  status: 'pending' | 'completed' | 'rolled_back';
  created_at: string;
  executed_at: string | null;
  affected_users: any[];
}

export interface TreeNode {
  id: string;
  username: string;
  email: string;
  status: string;
  created_at: string;
  depth: number;
  health_score: number | null;
  children: TreeNode[];
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  flagged_users: number;
  banned_users: number;
  suspended_users: number;
  deleted_users: number;
  total_invites_issued: number;
  total_invites_used: number;
  avg_health_score: number;
  low_health_users: number;
  recent_registrations_24h: number;
  recent_registrations_7d: number;
}

// API Request/Response Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  invite_token: string;
  fingerprint?: string;
}

export interface AuthResponse {
  user_id: string;
  username: string;
  email: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CreateInvitesRequest {
  count: number;
  note?: string;
}

export interface PruneRequest {
  root_user_id: string;
  reason: string;
  dry_run: boolean;
}

export interface PruneResponse {
  dry_run: boolean;
  operation_id?: string;
  affected_count: number;
  affected_users?: any[];
  status?: string;
}

