import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  User,
  Mail,
  Shield,
  Bell,
  Palette,
  Save,
  Key,
  Eye,
  EyeOff,
  Copy,
  Check,
  RefreshCw,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showMt5Password, setShowMt5Password] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // MT5 Settings State
  const [mt5Loading, setMt5Loading] = useState(true);
  const [mt5Saving, setMt5Saving] = useState(false);
  const [mt5Config, setMt5Config] = useState<{
    mt5_login: string;
    mt5_password: string;
    mt5_server: string;
    is_active: boolean;
    sync_interval_minutes: number;
  }>({
    mt5_login: '',
    mt5_password: '',
    mt5_server: '',
    is_active: true,
    sync_interval_minutes: 5,
  });
  const [mt5Status, setMt5Status] = useState<{
    has_config: boolean;
    is_active: boolean;
    last_sync_at: string | null;
    last_sync_status: string | null;
    last_sync_message: string | null;
  } | null>(null);
  
  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    setProfileData({
      full_name: user.full_name || '',
      email: user.email || '',
    });
  }, [user]);

  // Fetch MT5 status on mount
  useEffect(() => {
    if (user) {
      fetchMt5Status();
    }
  }, [user]);

  const fetchMt5Status = async () => {
    try {
      setMt5Loading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/status`, {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setMt5Status(data);
        if (data.has_config) {
          // Fetch account config to pre-fill the form
          const configResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/account`, {
            headers: {
              'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
            },
          });
          if (configResponse.ok) {
            const configData = await configResponse.json();
            setMt5Config({
              mt5_login: configData.mt5_login || '',
              mt5_password: '', // Don't fetch password for security
              mt5_server: configData.mt5_server || '',
              is_active: configData.is_active ?? true,
              sync_interval_minutes: configData.sync_interval_minutes || 5,
            });
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch MT5 status:', error);
    } finally {
      setMt5Loading(false);
    }
  };

  const handleMt5Save = async (e: React.FormEvent) => {
    e.preventDefault();
    setMt5Saving(true);
    setMessage(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/account`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
        body: JSON.stringify(mt5Config),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'MT5 credentials saved successfully!' });
        // Clear password after save
        setMt5Config({ ...mt5Config, mt5_password: '' });
        // Refresh status
        await fetchMt5Status();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to save MT5 credentials' });
      }
    } catch (error) {
      console.error('Failed to save MT5 credentials:', error);
      setMessage({ type: 'error', text: 'Failed to save MT5 credentials' });
    } finally {
      setMt5Saving(false);
    }
  };

  const handleMt5Toggle = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/account/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMt5Config({ ...mt5Config, is_active: data.is_active });
        setMessage({ type: 'success', text: data.is_active ? 'MT5 sync enabled' : 'MT5 sync disabled' });
        await fetchMt5Status();
      }
    } catch (error) {
      console.error('Failed to toggle MT5 sync:', error);
    }
  };

  const handleMt5Delete = async () => {
    if (!confirm('Are you sure you want to remove your MT5 credentials?')) return;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/account`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        setMt5Config({
          mt5_login: '',
          mt5_password: '',
          mt5_server: '',
          is_active: true,
          sync_interval_minutes: 5,
        });
        setMt5Status(null);
        setMessage({ type: 'success', text: 'MT5 credentials removed' });
      }
    } catch (error) {
      console.error('Failed to remove MT5 credentials:', error);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      console.log('Updating profile with data:', profileData);
      const result = await apiClient.updateProfile(profileData);
      console.log('Profile update successful:', result);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      
      // Reload user data
      if (user) {
        const updatedUser = await apiClient.getCurrentUser();
        console.log('Updated user data:', updatedUser);
        // Update session storage
        sessionStorage.setItem('user', JSON.stringify(updatedUser));
        // Force reload to update context
        setTimeout(() => window.location.reload(), 1000);
      }
    } catch (error: any) {
      console.error('Failed to update profile:', error);
      console.error('Error details:', JSON.stringify(error, null, 2));
      
      // Handle fetch API error structure
      let errorMessage = 'Failed to update profile';
      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail;
        errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      setMessage({ 
        type: 'error', 
        text: errorMessage
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }

    if (passwordData.new_password.length < 8) {
      setMessage({ type: 'error', text: 'Password must be at least 8 characters' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      // API call to change password would go here
      // await apiClient.changePassword(passwordData);
      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      console.error('Failed to change password:', error);
      setMessage({ type: 'error', text: 'Failed to change password' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="p-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Message */}
        {message && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
            }`}
          >
            {message.text}
          </div>
        )}

        {/* User ID Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded-lg">
              <Shield className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">User ID</h2>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                Your unique user identifier. Use this when contacting support.
              </p>
              <div className="flex items-center gap-3">
                <code className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-lg font-mono text-gray-900 dark:text-white">
                  UID: {user?.id || '---'}
                </code>
                <button
                  onClick={() => {
                    if (user?.id) {
                      navigator.clipboard.writeText(String(user.id));
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }
                  }}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition text-gray-600 dark:text-gray-300"
                  title="Copy User ID"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-green-500">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      <span className="text-sm">Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* MT5 Auto-Sync Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">MT5 Auto-Sync</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Connect your MT5 account to automatically sync trades
              </p>
            </div>
            {mt5Status?.has_config && (
              <button
                onClick={handleMt5Toggle}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  mt5Status.is_active
                    ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {mt5Status.is_active ? 'Sync Active' : 'Sync Paused'}
              </button>
            )}
          </div>

          {/* Sync Status */}
          {mt5Status?.has_config && (
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                {mt5Status.last_sync_status === 'success' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : mt5Status.last_sync_status === 'error' ? (
                  <XCircle className="h-5 w-5 text-red-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                )}
                <span className="font-medium text-gray-900 dark:text-white">
                  {mt5Status.last_sync_status === 'success'
                    ? 'Last sync successful'
                    : mt5Status.last_sync_status === 'error'
                    ? 'Last sync failed'
                    : 'Never synced'}
                </span>
              </div>
              {mt5Status.last_sync_at && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Last sync: {new Date(mt5Status.last_sync_at).toLocaleString()}
                </p>
              )}
              {mt5Status.last_sync_message && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {mt5Status.last_sync_message}
                </p>
              )}
            </div>
          )}

          {mt5Loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : (
            <form onSubmit={handleMt5Save} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    MT5 Login (Account Number)
                  </label>
                  <input
                    type="text"
                    value={mt5Config.mt5_login}
                    onChange={(e) => setMt5Config({ ...mt5Config, mt5_login: e.target.value })}
                    className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                    placeholder="e.g., 12345678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    MT5 Server
                  </label>
                  <input
                    type="text"
                    value={mt5Config.mt5_server}
                    onChange={(e) => setMt5Config({ ...mt5Config, mt5_server: e.target.value })}
                    className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                    placeholder="e.g., ICMarkets-Demo"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  MT5 Password {mt5Status?.has_config && '(leave blank to keep current)'}
                </label>
                <div className="relative">
                  <input
                    type={showMt5Password ? 'text' : 'password'}
                    value={mt5Config.mt5_password}
                    onChange={(e) => setMt5Config({ ...mt5Config, mt5_password: e.target.value })}
                    className="w-full px-4 py-2 pr-10 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                    placeholder={mt5Status?.has_config ? '••••••••' : 'Enter MT5 password'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowMt5Password(!showMt5Password)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showMt5Password ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Sync Interval (minutes)
                </label>
                <select
                  value={mt5Config.sync_interval_minutes}
                  onChange={(e) =>
                    setMt5Config({ ...mt5Config, sync_interval_minutes: parseInt(e.target.value) })
                  }
                  className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                >
                  <option value={1}>Every 1 minute</option>
                  <option value={5}>Every 5 minutes</option>
                  <option value={15}>Every 15 minutes</option>
                  <option value={30}>Every 30 minutes</option>
                  <option value={60}>Every hour</option>
                </select>
              </div>

              <div className="flex items-center gap-4 pt-4">
                <button
                  type="submit"
                  disabled={mt5Saving || !mt5Config.mt5_login || !mt5Config.mt5_server}
                  className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {mt5Saving ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Save className="h-5 w-5" />
                  )}
                  {mt5Saving ? 'Saving...' : mt5Status?.has_config ? 'Update Credentials' : 'Save Credentials'}
                </button>

                {mt5Status?.has_config && (
                  <button
                    type="button"
                    onClick={handleMt5Delete}
                    className="px-6 py-2.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                  >
                    Remove Credentials
                  </button>
                )}
              </div>

              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                <AlertCircle className="h-4 w-4 inline mr-1" />
                Your credentials are encrypted. We only use them to sync your trades.
              </p>
            </form>
          )}
        </div>

        {/* Profile Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <User className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Profile Information</h2>
          </div>

          <form onSubmit={handleProfileUpdate} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Full Name
              </label>
              <input
                type="text"
                value={profileData.full_name}
                onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your full name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="your.email@example.com"
                disabled
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Email cannot be changed
              </p>
            </div>

            <div className="flex items-center gap-4">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <Save className="h-5 w-5" />
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>

        {/* Password Section */}
        {!user?.oauth_provider && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <Key className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Change Password</h2>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Current Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={passwordData.current_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, current_password: e.target.value })
                    }
                    className="w-full px-4 py-2 pr-10 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter current password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  New Password
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={passwordData.new_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, new_password: e.target.value })
                  }
                  className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter new password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Confirm New Password
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={passwordData.confirm_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, confirm_password: e.target.value })
                  }
                  className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  placeholder="Confirm new password"
                />
              </div>

              <div className="flex items-center gap-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <Key className="h-5 w-5" />
                  {loading ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* OAuth Info */}
        {user?.oauth_provider && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 mb-6">
            <div className="flex items-center gap-3">
              <Shield className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  OAuth Authentication
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  You're signed in with {user.oauth_provider}. Password change is not available for OAuth accounts.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Account Info */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <Shield className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Account Information</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Account Type</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {user?.oauth_provider ? `OAuth (${user.oauth_provider})` : 'Email/Password'}
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Role</span>
              <span className="font-medium text-gray-900 dark:text-white capitalize">
                {mounted && user?.role}
              </span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span className="text-gray-600 dark:text-gray-400">Account Status</span>
              <span className="inline-flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 rounded-full text-sm font-medium">
                <span className="h-2 w-2 bg-green-600 rounded-full"></span>
                Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
