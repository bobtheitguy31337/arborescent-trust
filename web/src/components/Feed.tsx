import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Loader } from 'lucide-react';
import { apiClient } from '../lib/api';
import { PostCard } from './PostCard';
import { PostComposer } from './PostComposer';
import type { Post } from '../types';

interface FeedProps {
  currentUserId?: string;
}

export const Feed: React.FC<FeedProps> = ({ currentUserId }) => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [replyingTo, setReplyingTo] = useState<Post | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const lastPostRef = useRef<HTMLDivElement>(null);

  const loadPosts = async (pageNum: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      
      const feed = await apiClient.getFeed(pageNum);
      
      if (append) {
        setPosts((prev) => [...prev, ...feed.posts]);
      } else {
        setPosts(feed.posts);
      }
      
      setHasMore(feed.has_more);
      setPage(pageNum);
    } catch (error) {
      console.error('Failed to load feed', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    loadPosts(1);
  }, []);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const target = entries[0];
      if (target.isIntersecting && hasMore && !loadingMore) {
        loadPosts(page + 1, true);
      }
    },
    [hasMore, loadingMore, page]
  );

  useEffect(() => {
    const option = {
      root: null,
      rootMargin: '20px',
      threshold: 1.0,
    };
    
    observerRef.current = new IntersectionObserver(handleObserver, option);
    
    if (lastPostRef.current) {
      observerRef.current.observe(lastPostRef.current);
    }
    
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [handleObserver]);

  const handlePostCreated = () => {
    loadPosts(1);
    setReplyingTo(null);
  };

  const handlePostDeleted = () => {
    loadPosts(1);
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
      <PostComposer onPostCreated={handlePostCreated} />

      {replyingTo && (
        <div className="border-b border-gray-800 bg-gray-900/50">
          <div className="p-4">
            <div className="text-sm text-gray-500 mb-2">
              Replying to @{replyingTo.author.username}
            </div>
            <PostComposer
              replyToId={replyingTo.id}
              onPostCreated={handlePostCreated}
              placeholder="Post your reply"
            />
            <button
              onClick={() => setReplyingTo(null)}
              className="text-sm text-gray-500 hover:text-white mt-2"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div>
        {posts.map((post, index) => (
          <div
            key={post.id}
            ref={index === posts.length - 1 ? lastPostRef : null}
          >
            <PostCard
              post={post}
              onPostDeleted={handlePostDeleted}
              onReply={setReplyingTo}
              currentUserId={currentUserId}
            />
          </div>
        ))}
      </div>

      {loadingMore && (
        <div className="flex items-center justify-center py-8">
          <Loader className="w-6 h-6 animate-spin text-primary" />
        </div>
      )}

      {!hasMore && posts.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          You've reached the end
        </div>
      )}

      {!loading && posts.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-xl mb-2">No posts yet</p>
          <p>Follow some users to see their posts here</p>
        </div>
      )}
    </div>
  );
};

