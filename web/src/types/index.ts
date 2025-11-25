export interface User {
  id: string;
  username: string;
  email?: string;
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  banner_url?: string;
  location?: string;
  website?: string;
  follower_count: number;
  following_count: number;
  post_count: number;
  status: string;
  is_core_member: boolean;
  is_admin?: boolean;
  role?: string;
  invite_quota?: number;
  invites_used?: number;
  invites_available?: number;
  is_following?: boolean;
  is_followed_by?: boolean;
  created_at: string;
}

export interface MediaAttachment {
  id: string;
  media_type: 'image' | 'video' | 'gif';
  mime_type: string;
  file_path: string;
  width?: number;
  height?: number;
  duration?: number;
  thumbnail_path?: string;
  alt_text?: string;
}

export interface Post {
  id: string;
  user_id: string;
  content: string;
  visibility: string;
  is_reply: boolean;
  reply_to_id?: string;
  reply_to_user_id?: string;
  is_repost: boolean;
  repost_of_id?: string;
  repost_of?: Post;
  like_count: number;
  repost_count: number;
  reply_count: number;
  view_count: number;
  is_liked: boolean;
  is_reposted: boolean;
  created_at: string;
  updated_at?: string;
  author: User;
  media: MediaAttachment[];
}

export interface Feed {
  posts: Post[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface Notification {
  id: string;
  user_id: string;
  actor_id?: string;
  notification_type: string;
  post_id?: string;
  message?: string;
  extra_data?: any;
  read: boolean;
  read_at?: string;
  created_at: string;
  actor?: User;
}

export interface NotificationList {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface AuthResponse {
  user_id: string;
  username: string;
  email: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  invite_token: string;
}

