import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import ChatBox from '@/components/ChatBox';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Users, MessageSquare, Shield, User } from 'lucide-react';

interface ChatMessage {
  id: number;
  user_id: number;
  user_name: string;
  message: string;
  is_admin: boolean;
  created_at: string;
}

interface AdminStats {
  total_messages: number;
  total_users: number;
  admin_count: number;
}

interface UserWithMessages {
  id: number;
  full_name: string;
  email: string;
  message_count: number;
  last_message_at: string;
}

export default function AdminPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [users, setUsers] = useState<UserWithMessages[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);

  const fetchMessages = useCallback(async () => {
    if (!selectedUserId) {
      setMessages([]);
      setLoading(false);
      return;
    }
    
    try {
      const data = await apiClient.getChatMessages(selectedUserId);
      setMessages(data);
    } catch (error: any) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedUserId]);

  const fetchUsers = useCallback(async () => {
    try {
      const data = await apiClient.getUsersWithMessages();
      setUsers(data);
      // Auto-select first user if none selected
      if (!selectedUserId && data.length > 0) {
        setSelectedUserId(data[0].id);
      }
    } catch (error: any) {
      console.error('Failed to fetch users:', error);
    }
  }, [selectedUserId]);

  const fetchStats = useCallback(async () => {
    try {
      const data = await apiClient.getAdminStats();
      setStats(data);
    } catch (error: any) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    if (user.role !== 'ADMIN') {
      router.push('/dashboard');
      return;
    }

    fetchUsers();
    fetchMessages();
    fetchStats();

    // Poll for new messages every 3 seconds
    const messagesInterval = setInterval(fetchMessages, 3000);
    // Update users every 10 seconds
    const usersInterval = setInterval(fetchUsers, 10000);
    // Update stats every 30 seconds
    const statsInterval = setInterval(fetchStats, 30000);

    return () => {
      clearInterval(messagesInterval);
      clearInterval(usersInterval);
      clearInterval(statsInterval);
    };
  }, [user, router, fetchMessages, fetchUsers, fetchStats, selectedUserId]);

  const handleSendMessage = async (message: string) => {
    if (!selectedUserId) {
      alert('Please select a user conversation first');
      return;
    }
    
    try {
      await apiClient.sendChatMessage(message, selectedUserId);
      // Refresh messages immediately after sending
      await fetchMessages();
    } catch (error: any) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
      throw error;
    }
  };

  const handleDeleteMessage = async (messageId: number) => {
    try {
      await apiClient.deleteChatMessage(messageId);
      // Refresh messages after deletion
      await fetchMessages();
    } catch (error: any) {
      console.error('Failed to delete message:', error);
      alert('Failed to delete message. Please try again.');
      throw error;
    }
  };

  if (!user || user.role !== 'ADMIN') {
    return null;
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary-600" />
            Admin Panel
          </h1>
          <p className="text-gray-400">
            Manage support chat and view system statistics
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Users</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {statsLoading ? '...' : stats?.total_users || 0}
                </p>
              </div>
              <Users className="h-12 w-12 text-primary-600 opacity-50" />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Messages</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {statsLoading ? '...' : stats?.total_messages || 0}
                </p>
              </div>
              <MessageSquare className="h-12 w-12 text-green-600 opacity-50" />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Admin Users</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {statsLoading ? '...' : stats?.admin_count || 0}
                </p>
              </div>
              <Shield className="h-12 w-12 text-orange-600 opacity-50" />
            </div>
          </div>
        </div>

        {/* Support Chat */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* User List */}
          <div className="card lg:col-span-1">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
              User Conversations
            </h2>
            <div className="space-y-2 max-h-[450px] overflow-y-auto">
              {users.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                  No conversations yet
                </p>
              ) : (
                users.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => setSelectedUserId(u.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedUserId === u.id
                        ? 'bg-primary-100 dark:bg-primary-900 border-2 border-primary-500'
                        : 'bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <User className="h-4 w-4" />
                      <span className="font-semibold text-sm text-gray-900 dark:text-white truncate">
                        {u.full_name}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                      {u.email}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      {u.message_count} messages
                    </p>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className="card lg:col-span-3">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              {selectedUserId ? `Chat with ${users.find(u => u.id === selectedUserId)?.full_name}` : 'Select a user'}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {selectedUserId 
                ? 'Your responses will be marked as "Support" and visible only to this user.'
                : 'Select a user from the list to view and respond to their messages.'}
            </p>
            <div className="h-[450px]">
              {selectedUserId ? (
                <ChatBox
                  currentUserId={user.id}
                  isAdmin={true}
                  onSendMessage={handleSendMessage}
                  onDeleteMessage={handleDeleteMessage}
                  messages={messages}
                  loading={loading}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                  <div className="text-center">
                    <User className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p>Select a user to start chatting</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
          <p className="text-sm text-orange-800 dark:text-orange-200">
            <strong>Admin Privileges:</strong> You can view and respond to each user's conversation individually. Your responses are marked as "Support"
            with your name and visible only to the selected user. Messages refresh automatically every 3 seconds.
          </p>
        </div>
      </div>
    </Layout>
  );
}
