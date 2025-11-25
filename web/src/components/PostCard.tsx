import React, { useState } from 'react';
import { Heart, Repeat2, MessageCircle, MoreHorizontal, Trash2 } from 'lucide-react';
import { apiClient } from '../lib/api';
import { TrustBadge } from './TrustBadge';
import type { Post } from '../types';

interface PostCardProps {
  post: Post;
  onPostDeleted?: () => void;
  onReply?: (post: Post) => void;
  currentUserId?: string;
}

export const PostCard: React.FC<PostCardProps> = ({ post, onPostDeleted, onReply, currentUserId }) => {
  const [liked, setLiked] = useState(post.is_liked);
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [reposted, setReposted] = useState(post.is_reposted);
  const [repostCount, setRepostCount] = useState(post.repost_count);
  const [showMenu, setShowMenu] = useState(false);

  const handleLike = async () => {
    try {
      if (liked) {
        await apiClient.unlikePost(post.id);
        setLiked(false);
        setLikeCount((c) => c - 1);
      } else {
        await apiClient.likePost(post.id);
        setLiked(true);
        setLikeCount((c) => c + 1);
      }
    } catch (error) {
      console.error('Failed to like/unlike post', error);
    }
  };

  const handleRepost = async () => {
    try {
      if (!reposted) {
        await apiClient.repost(post.id);
        setReposted(true);
        setRepostCount((c) => c + 1);
      }
    } catch (error) {
      console.error('Failed to repost', error);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this post?')) return;
    try {
      await apiClient.deletePost(post.id);
      onPostDeleted?.();
    } catch (error) {
      console.error('Failed to delete post', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / 1000 / 60 / 60);
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'just now';
    if (hours < 24) return `${hours}h`;
    if (days < 7) return `${days}d`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const isOwnPost = currentUserId === post.user_id;

  // If it's a repost with original content
  const originalPost = post.repost_of;

  return (
    <div className="border-b border-gray-800 p-4 hover:bg-gray-900/30 transition-colors">
      {post.is_repost && originalPost && (
        <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
          <Repeat2 className="w-4 h-4" />
          <span>{post.author.username} reposted</span>
        </div>
      )}

      <div className="flex gap-3">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center text-xl font-bold">
            {(originalPost || post).author.display_name?.[0] || (originalPost || post).author.username[0].toUpperCase()}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold hover:underline cursor-pointer">
              {(originalPost || post).author.display_name || (originalPost || post).author.username}
            </span>
            <TrustBadge
              status={(originalPost || post).author.status}
              isCoreMember={(originalPost || post).author.is_core_member}
              size="sm"
            />
            <span className="text-gray-500">@{(originalPost || post).author.username}</span>
            <span className="text-gray-500">·</span>
            <span className="text-gray-500">{formatDate((originalPost || post).created_at)}</span>
            
            {isOwnPost && (
              <div className="ml-auto relative">
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="text-gray-500 hover:text-primary p-1 rounded-full hover:bg-primary/10"
                >
                  <MoreHorizontal className="w-5 h-5" />
                </button>
                {showMenu && (
                  <div className="absolute right-0 mt-1 bg-black border border-gray-700 rounded-lg shadow-xl py-2 z-10">
                    <button
                      onClick={handleDelete}
                      className="flex items-center gap-2 px-4 py-2 hover:bg-gray-900 w-full text-left text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="text-white mb-3 whitespace-pre-wrap break-words">
            {(originalPost || post).content}
          </div>

          {(originalPost || post).media.length > 0 && (
            <div className={`grid gap-2 mb-3 rounded-2xl overflow-hidden ${(originalPost || post).media.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
              {(originalPost || post).media.map((m) => (
                <div key={m.id} className="bg-gray-900">
                  {m.media_type === 'video' ? (
                    <video
                      src={apiClient.getMediaUrl(m.file_path)}
                      className="w-full max-h-96 object-cover"
                      controls
                    />
                  ) : (
                    <img
                      src={apiClient.getMediaUrl(m.file_path)}
                      alt={m.alt_text || ''}
                      className="w-full max-h-96 object-cover"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between max-w-md mt-3">
            <button
              onClick={() => onReply?.(originalPost || post)}
              className="flex items-center gap-2 text-gray-500 hover:text-primary group"
            >
              <div className="p-2 rounded-full group-hover:bg-primary/10 transition-colors">
                <MessageCircle className="w-5 h-5" />
              </div>
              <span className="text-sm">{(originalPost || post).reply_count || 0}</span>
            </button>

            <button
              onClick={handleRepost}
              className={`flex items-center gap-2 group ${
                reposted ? 'text-green-500' : 'text-gray-500 hover:text-green-500'
              }`}
            >
              <div className="p-2 rounded-full group-hover:bg-green-500/10 transition-colors">
                <Repeat2 className="w-5 h-5" />
              </div>
              <span className="text-sm">{repostCount || 0}</span>
            </button>

            <button
              onClick={handleLike}
              className={`flex items-center gap-2 group ${
                liked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
              }`}
            >
              <div className="p-2 rounded-full group-hover:bg-red-500/10 transition-colors">
                <Heart className={`w-5 h-5 ${liked ? 'fill-current' : ''}`} />
              </div>
              <span className="text-sm">{likeCount || 0}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

