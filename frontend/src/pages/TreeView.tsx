import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiClient } from '../lib/api';
import type { TreeNode, User } from '../types';
import TreeVisualization from '../components/TreeVisualization';
import { Search, Network, Info } from 'lucide-react';

export default function TreeView() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [treeData, setTreeData] = useState<TreeNode | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState(searchParams.get('user') || '');
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);

  useEffect(() => {
    const userParam = searchParams.get('user');
    if (userParam) {
      setSearchInput(userParam);
      loadTree(userParam);
    }
  }, [searchParams]);

  const loadTree = async (identifier: string) => {
    try {
      setLoading(true);
      setError('');
      
      // Backend now accepts UUID, username, or email directly
      const [tree, user] = await Promise.all([
        apiClient.getUserTree(identifier),
        apiClient.getUser(identifier),
      ]);
      setTreeData(tree);
      setSelectedUser(user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tree data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput) {
      loadTree(searchInput);
    }
  };

  const handleNodeClick = (node: TreeNode) => {
    setSelectedNode(node);
  };

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              User ID, Username, or Email
            </label>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="e.g., admin or admin@example.com"
              className="input"
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Enter a username, email, or user ID to view their invite tree
            </p>
          </div>
          <div className="flex items-end">
            <button type="submit" className="btn btn-primary flex items-center">
              <Search className="mr-2 h-5 w-5" />
              Load Tree
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      )}

      {!loading && selectedUser && treeData && (
        <>
          {/* User info */}
          <div className="card">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {selectedUser.username}
                </h3>
                <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  <p>Email: {selectedUser.email}</p>
                  <p>Status: <span className="font-medium">{selectedUser.status}</span></p>
                  <p>Invites: {selectedUser.invites_used} / {selectedUser.invite_quota}</p>
                  <p>Role: {selectedUser.role}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-primary-600">
                <Network className="h-8 w-8" />
              </div>
            </div>
          </div>

          {/* Tree visualization */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Invite Tree
              </h3>
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Info className="h-4 w-4" />
                <span>Click nodes to view details</span>
              </div>
            </div>
            <TreeVisualization data={treeData} onNodeClick={handleNodeClick} />
          </div>

          {/* Selected node details */}
          {selectedNode && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Node Details: {selectedNode.username}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Email</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {selectedNode.email}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {selectedNode.status}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Depth</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {selectedNode.depth}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Health Score</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {selectedNode.health_score !== null
                      ? `${selectedNode.health_score.toFixed(1)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Children</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {selectedNode.children.length}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Created</p>
                  <p className="text-base font-medium text-gray-900 dark:text-white">
                    {new Date(selectedNode.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => setSearchParams({ user: selectedNode.id })}
                  className="btn btn-primary"
                >
                  Load This User's Tree
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !treeData && (
        <div className="card text-center py-12">
          <Network className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">
            Enter a user ID to visualize their invite tree
          </p>
        </div>
      )}
    </div>
  );
}

