import React, { useState, useRef } from 'react';
import { Image, X, Loader } from 'lucide-react';
import { apiClient } from '../lib/api';
import type { MediaAttachment } from '../types';

interface PostComposerProps {
  onPostCreated?: () => void;
  replyToId?: string;
  placeholder?: string;
}

export const PostComposer: React.FC<PostComposerProps> = ({
  onPostCreated,
  replyToId,
  placeholder = "What's happening?",
}) => {
  const [content, setContent] = useState('');
  const [media, setMedia] = useState<MediaAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [posting, setPosting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || media.length >= 4) return;

    setUploading(true);
    try {
      for (let i = 0; i < Math.min(files.length, 4 - media.length); i++) {
        const file = files[i];
        const uploaded = await apiClient.uploadMedia(file);
        setMedia((prev) => [...prev, uploaded]);
      }
    } catch (error) {
      console.error('Failed to upload media', error);
      alert('Failed to upload media');
    } finally {
      setUploading(false);
    }
  };

  const removeMedia = (id: string) => {
    setMedia((prev) => prev.filter((m) => m.id !== id));
  };

  const handlePost = async () => {
    if (!content.trim() && media.length === 0) return;

    setPosting(true);
    try {
      await apiClient.createPost(
        content,
        media.map((m) => m.id),
        replyToId
      );
      setContent('');
      setMedia([]);
      onPostCreated?.();
    } catch (error) {
      console.error('Failed to create post', error);
      alert('Failed to create post');
    } finally {
      setPosting(false);
    }
  };

  const remainingChars = 280 - content.length;
  const isOverLimit = remainingChars < 0;
  const canPost = (content.trim() || media.length > 0) && !isOverLimit && !posting;

  return (
    <div className="border-b border-gray-800 p-4">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent text-white text-xl resize-none focus:outline-none mb-3"
        rows={3}
        maxLength={300}
      />

      {media.length > 0 && (
        <div className={`grid gap-2 mb-3 ${media.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
          {media.map((m) => (
            <div key={m.id} className="relative rounded-2xl overflow-hidden bg-gray-900">
              {m.media_type === 'video' ? (
                <video
                  src={apiClient.getMediaUrl(m.file_path)}
                  className="w-full h-64 object-cover"
                  controls
                />
              ) : (
                <img
                  src={apiClient.getMediaUrl(m.file_path)}
                  alt={m.alt_text || ''}
                  className="w-full h-64 object-cover"
                />
              )}
              <button
                onClick={() => removeMedia(m.id)}
                className="absolute top-2 right-2 bg-black/70 hover:bg-black/90 rounded-full p-1.5 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || media.length >= 4}
            className="text-primary hover:bg-primary/10 p-2 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? <Loader className="w-5 h-5 animate-spin" /> : <Image className="w-5 h-5" />}
          </button>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-sm ${isOverLimit ? 'text-red-500' : 'text-gray-500'}`}>
            {remainingChars}
          </span>
          <button
            onClick={handlePost}
            disabled={!canPost}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {posting ? 'Posting...' : replyToId ? 'Reply' : 'Post'}
          </button>
        </div>
      </div>
    </div>
  );
};

