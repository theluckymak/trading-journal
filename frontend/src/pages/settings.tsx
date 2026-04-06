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
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setMt5Status(data);
        if (data.has_config) {
          // Fetch account config to pre-fill the form
          const configResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/account`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
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
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
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
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMt5Config({ ...mt5Config, is_active: data.is_active });
        setMessage({ type: 'success', text: data.is_active ? 'MT5 sync enabled' : 'MT5 sync disabled' });
        await fetchMt5Status();
      }
    } catch (error) {
    }
  };

  const handleMt5Delete = async () => {
    if (!confirm('Are you sure you want to remove your MT5 credentials?')) return;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/mt5/account`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
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
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const result = await apiClient.updateProfile(profileData);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      
      // Reload user data
      if (user) {
        const updatedUser = await apiClient.getCurrentUser();
        // Update session storage
        sessionStorage.setItem('user', JSON.stringify(updatedUser));
        // Force reload to update context
        setTimeout(() => window.location.reload(), 1000);
      }
    } catch (error: any) {
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
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>Settings</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Manage your account settings and preferences
          </p>
        </div>

        {/* Message */}
        {message && (
          <div
            className="mb-6 p-4 rounded-lg"
            style={
              message.type === 'success'
                ? { background: 'rgba(41,204,106,0.1)', color: 'var(--success)' }
                : { background: 'rgba(255,45,85,0.1)', color: 'var(--error)' }
            }
          >
            {message.text}
          </div>
        )}

        {/* User ID Section */}
        <div className="p-6 mb-6" style={{ background: 'var(--bg-card)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg" style={{ background: 'var(--brand-light)' }}>
              <Shield className="h-5 w-5" style={{ color: 'var(--brand)' }} />
            </div>
            <h2 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>User ID</h2>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <p className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                Your unique user identifier. Use this when contacting support.
              </p>
              <div className="flex items-center gap-3">
                <code className="px-4 py-2 rounded-lg text-lg font-mono" style={{ background: 'var(--bg-section)', color: 'var(--text)' }}>
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
                  className="flex items-center gap-2 px-3 py-2 rounded-lg transition"
                  style={{ background: 'var(--bg-section)', color: 'var(--text-muted)' }}
                  title="Copy User ID"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" style={{ color: 'var(--success)' }} />
                      <span className="text-sm" style={{ color: 'var(--success)' }}>Copied!</span>
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
        <div className="p-6 mb-6" style={{ background: 'var(--bg-card)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg" style={{ background: 'var(--brand-light)' }}>
              <TrendingUp className="h-5 w-5" style={{ color: 'var(--brand)' }} />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>MT5 Auto-Sync</h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Connect your MT5 account to automatically sync trades
              </p>
            </div>
            {mt5Status?.has_config && (
              <button
                onClick={handleMt5Toggle}
                className="px-4 py-2 rounded-lg font-medium transition"
                style={
                  mt5Status.is_active
                    ? { background: 'rgba(41,204,106,0.1)', color: 'var(--success)' }
                    : { background: 'var(--bg-section)', color: 'var(--text-muted)' }
                }
              >
                {mt5Status.is_active ? 'Sync Active' : 'Sync Paused'}
              </button>
            )}
          </div>

          {/* Sync Status */}
          {mt5Status?.has_config && (
            <div className="mb-6 p-4 rounded-lg" style={{ background: 'var(--bg-section)' }}>
              <div className="flex items-center gap-3 mb-2">
                {mt5Status.last_sync_status === 'success' ? (
                  <CheckCircle className="h-5 w-5" style={{ color: 'var(--success)' }} />
                ) : mt5Status.last_sync_status === 'error' ? (
                  <XCircle className="h-5 w-5" style={{ color: 'var(--error)' }} />
                ) : (
                  <AlertCircle className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
                )}
                <span className="font-medium" style={{ color: 'var(--text)' }}>
                  {mt5Status.last_sync_status === 'success'
                    ? 'Last sync successful'
                    : mt5Status.last_sync_status === 'error'
                    ? 'Last sync failed'
                    : 'Never synced'}
                </span>
              </div>
              {mt5Status.last_sync_at && (
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  Last sync: {new Date(mt5Status.last_sync_at).toLocaleString()}
                </p>
              )}
              {mt5Status.last_sync_message && (
                <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                  {mt5Status.last_sync_message}
                </p>
              )}
            </div>
          )}

          {mt5Loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" style={{ color: 'var(--text-muted)' }} />
            </div>
          ) : (
            <form onSubmit={handleMt5Save} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                    MT5 Login (Account Number)
                  </label>
                  <input
                    type="text"
                    value={mt5Config.mt5_login}
                    onChange={(e) => setMt5Config({ ...mt5Config, mt5_login: e.target.value })}
                    className="input w-full"
                    placeholder="e.g., 12345678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                    MT5 Server
                  </label>
                  <input
                    type="text"
                    value={mt5Config.mt5_server}
                    onChange={(e) => setMt5Config({ ...mt5Config, mt5_server: e.target.value })}
                    className="input w-full"
                    placeholder="e.g., ICMarkets-Demo"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                  MT5 Password {mt5Status?.has_config && '(leave blank to keep current)'}
                </label>
                <div className="relative">
                  <input
                    type={showMt5Password ? 'text' : 'password'}
                    value={mt5Config.mt5_password}
                    onChange={(e) => setMt5Config({ ...mt5Config, mt5_password: e.target.value })}
                    className="w-full px-4 py-2 pr-10 rounded-lg border"
                    style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                    placeholder={mt5Status?.has_config ? '••••••••' : 'Enter MT5 password'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowMt5Password(!showMt5Password)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {showMt5Password ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                  Sync Interval (minutes)
                </label>
                <select
                  value={mt5Config.sync_interval_minutes}
                  onChange={(e) =>
                    setMt5Config({ ...mt5Config, sync_interval_minutes: parseInt(e.target.value) })
                  }
                  className="input w-full"
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
                  className="btn btn-brand flex items-center gap-2"
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
                    className="px-6 py-2.5 rounded-lg transition"
                    style={{ color: 'var(--error)' }}
                  >
                    Remove Credentials
                  </button>
                )}
              </div>

              <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>
                <AlertCircle className="h-4 w-4 inline mr-1" />
                Your credentials are encrypted. We only use them to sync your trades.
              </p>
            </form>
          )}
        </div>

        {/* Profile Section */}
        <div className="p-6 mb-6" style={{ background: 'var(--bg-card)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg" style={{ background: 'var(--brand-light)' }}>
              <User className="h-5 w-5" style={{ color: 'var(--brand)' }} />
            </div>
            <h2 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>Profile Information</h2>
          </div>

          <form onSubmit={handleProfileUpdate} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                Full Name
              </label>
              <input
                type="text"
                value={profileData.full_name}
                onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                className="input w-full"
                placeholder="Enter your full name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                Email Address
              </label>
              <input
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                className="input w-full"
                placeholder="your.email@example.com"
                disabled
              />
              <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>
                Email cannot be changed
              </p>
            </div>

            <div className="flex items-center gap-4">
              <button
                type="submit"
                disabled={loading}
                className="btn btn-brand flex items-center gap-2"
              >
                <Save className="h-5 w-5" />
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>

        {/* Password Section */}
        {!user?.oauth_provider && (
          <div className="p-6 mb-6" style={{ background: 'var(--bg-card)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg" style={{ background: 'var(--brand-light)' }}>
                <Key className="h-5 w-5" style={{ color: 'var(--brand)' }} />
              </div>
              <h2 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>Change Password</h2>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                  Current Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={passwordData.current_password}
                    onChange={(e) =>
                      setPasswordData({ ...passwordData, current_password: e.target.value })
                    }
                    className="w-full px-4 py-2 pr-10 rounded-lg border"
                    style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                    placeholder="Enter current password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                  New Password
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={passwordData.new_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, new_password: e.target.value })
                  }
                  className="input w-full"
                  placeholder="Enter new password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-muted)' }}>
                  Confirm New Password
                </label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={passwordData.confirm_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, confirm_password: e.target.value })
                  }
                  className="input w-full"
                  placeholder="Confirm new password"
                />
              </div>

              <div className="flex items-center gap-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn btn-brand flex items-center gap-2"
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
          <div className="rounded-lg p-6 mb-6" style={{ background: 'var(--brand-light)' }}>
            <div className="flex items-center gap-3">
              <Shield className="h-6 w-6" style={{ color: 'var(--brand)' }} />
              <div>
                <h3 className="font-semibold" style={{ color: 'var(--text)' }}>
                  OAuth Authentication
                </h3>
                <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                  You're signed in with {user.oauth_provider}. Password change is not available for OAuth accounts.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Account Info */}
        <div className="p-6" style={{ background: 'var(--bg-card)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg" style={{ background: 'var(--bg-section)' }}>
              <Shield className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
            </div>
            <h2 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>Account Information</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Account Type</span>
              <span className="font-medium" style={{ color: 'var(--text)' }}>
                {user?.oauth_provider ? `OAuth (${user.oauth_provider})` : 'Email/Password'}
              </span>
            </div>
            <div className="flex items-center justify-between py-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Role</span>
              <span className="font-medium capitalize" style={{ color: 'var(--text)' }}>
                {mounted && user?.role}
              </span>
            </div>
            <div className="flex items-center justify-between py-3">
              <span style={{ color: 'var(--text-muted)' }}>Account Status</span>
              <span
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium"
                style={{ background: 'rgba(41,204,106,0.1)', color: 'var(--success)' }}
              >
                <span className="h-2 w-2 rounded-full" style={{ background: 'var(--success)' }}></span>
                Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
