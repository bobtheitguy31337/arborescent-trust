import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { UserPlus, TreePine } from 'lucide-react';
import { apiClient } from '../lib/api';

export default function Register() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [inviteToken, setInviteToken] = useState('');
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const validateToken = async (token: string) => {
    if (!token) {
      setTokenValid(null);
      return;
    }

    try {
      const result = await apiClient.validateInvite(token);
      setTokenValid(result.valid);
      if (!result.valid) {
        setError(result.reason || 'Invalid invite token');
      } else {
        setError('');
      }
    } catch (err) {
      setTokenValid(false);
      setError('Failed to validate invite token');
    }
  };

  const handleTokenBlur = () => {
    validateToken(inviteToken);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      await register({
        email,
        username,
        password,
        invite_token: inviteToken,
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to register. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        <div className="flex items-center justify-center mb-8">
          <TreePine className="h-12 w-12 text-primary-600 mr-3" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Arborescent Trust
          </h1>
        </div>

        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
          Create Account
        </h2>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="inviteToken" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Invite Token *
            </label>
            <input
              id="inviteToken"
              type="text"
              value={inviteToken}
              onChange={(e) => setInviteToken(e.target.value)}
              onBlur={handleTokenBlur}
              className={`input ${
                tokenValid === true
                  ? 'border-green-500'
                  : tokenValid === false
                  ? 'border-red-500'
                  : ''
              }`}
              required
              placeholder="Enter your invite code"
            />
            {tokenValid === true && (
              <p className="mt-1 text-sm text-green-600 dark:text-green-400">✓ Valid invite token</p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input"
              required
              placeholder="johndoe"
              minLength={3}
              maxLength={50}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
              placeholder="••••••••"
              minLength={8}
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input"
              required
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading || tokenValid !== true}
            className="w-full btn btn-primary flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <>
                <UserPlus className="mr-2 h-5 w-5" />
                Create Account
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

