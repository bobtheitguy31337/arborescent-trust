import React from 'react';
import { useAuth } from '../lib/auth';
import { Feed } from '../components/Feed';

export const Home: React.FC = () => {
  const { user } = useAuth();

  return (
    <div>
      <div className="border-b border-gray-800 p-4 sticky top-0 bg-black/80 backdrop-blur-sm z-10">
        <h1 className="text-xl font-bold">Home</h1>
      </div>
      <Feed currentUserId={user?.id} />
    </div>
  );
};

