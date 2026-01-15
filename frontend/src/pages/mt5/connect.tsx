import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { ArrowLeft, Plus, Trash2, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

interface MT5Account {
  id: number;
  account_number: string;
  account_name: string | null;
  broker_name: string;
  server_name: string;
  is_active: boolean;
  is_connected: boolean;
  last_sync_at: string | null;
  last_connection_error: string | null;
  account_balance: string | null;
}

export default function ConnectMT5() {
  const router = useRouter();
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<MT5Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [syncing, setSyncing] = useState<number | null>(null);
  
  const [formData, setFormData] = useState({
    account_number: '',
    account_name: '',
    broker_name: '',
    server_name: '',
    password: '',
  });
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadAccounts();
  }, [user, router]);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const accounts = await apiClient.getMT5Accounts();
      setAccounts(accounts);
    } catch (error) {
      console.error('Failed to load MT5 accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);

    try {
      console.log('Submitting MT5 account:', { ...formData, password: '***' });
      await apiClient.addMT5Account(formData);
      setFormData({
        account_number: '',
        account_name: '',
        broker_name: '',
        server_name: '',
        password: '',
      });
      setShowForm(false);
      await loadAccounts();
    } catch (err: any) {
      console.error('Failed to add MT5 account:', err);
      console.error('Error response:', err.response);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to add MT5 account. Please check your credentials.';
      setFormError(errorMsg);
    } finally {
      setFormLoading(false);
    }
  };

  const handleSync = async (accountId: number) => {
    try {
      setSyncing(accountId);
      await apiClient.syncMT5Account(accountId);
      await loadAccounts();
      alert('Trades synchronized successfully!');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to sync trades';
      alert(errorMsg);
    } finally {
      setSyncing(null);
    }
  };

  const handleDelete = async (accountId: number) => {
    if (!confirm('Are you sure you want to remove this MT5 account?')) return;

    try {
      await apiClient.deleteMT5Account(accountId);
      await loadAccounts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete account');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading MT5 accounts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="p-2 hover:bg-gray-100 rounded-lg transition"
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">MT5 Accounts</h1>
                <p className="text-sm text-gray-600">Connect and manage your MetaTrader 5 accounts</p>
              </div>
            </div>
            {!showForm && (
              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                <Plus className="h-4 w-4" />
                Add Account
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Add Account Form */}
        {showForm && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Add MT5 Account</h2>
              <button
                onClick={() => {
                  setShowForm(false);
                  setFormError('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6">
              {formError && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="account_number" className="block text-sm font-medium text-gray-700 mb-1">
                    Account Number *
                  </label>
                  <input
                    id="account_number"
                    name="account_number"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="12345678"
                    value={formData.account_number}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="account_name" className="block text-sm font-medium text-gray-700 mb-1">
                    Account Name (Optional)
                  </label>
                  <input
                    id="account_name"
                    name="account_name"
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="My Main Account"
                    value={formData.account_name}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="broker_name" className="block text-sm font-medium text-gray-700 mb-1">
                    Broker Name *
                  </label>
                  <input
                    id="broker_name"
                    name="broker_name"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="IC Markets"
                    value={formData.broker_name}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="server_name" className="block text-sm font-medium text-gray-700 mb-1">
                    Server Name *
                  </label>
                  <input
                    id="server_name"
                    name="server_name"
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="ICMarkets-Demo"
                    value={formData.server_name}
                    onChange={handleChange}
                  />
                </div>

                <div className="md:col-span-2">
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password *
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Your MT5 password"
                    value={formData.password}
                    onChange={handleChange}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Your password is encrypted and stored securely
                  </p>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  type="submit"
                  disabled={formLoading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {formLoading ? 'Connecting...' : 'Connect Account'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setFormError('');
                  }}
                  className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Accounts List */}
        {accounts.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Plus className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No MT5 accounts connected</h3>
              <p className="text-gray-600 mb-6">
                Connect your MetaTrader 5 account to automatically sync your trades and analyze your performance
              </p>
              {!showForm && (
                <button
                  onClick={() => setShowForm(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Connect Your First Account
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {accounts.map((account) => (
              <div key={account.id} className="bg-white rounded-lg shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {account.account_name || `Account ${account.account_number}`}
                        </h3>
                        <div
                          className={`flex items-center gap-1 px-2 py-1 text-xs rounded-full ${
                            account.is_connected
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {account.is_connected ? (
                            <>
                              <CheckCircle className="h-3 w-3" />
                              Connected
                            </>
                          ) : (
                            <>
                              <XCircle className="h-3 w-3" />
                              Disconnected
                            </>
                          )}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">Account Number</p>
                          <p className="font-medium text-gray-900">{account.account_number}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Broker</p>
                          <p className="font-medium text-gray-900">{account.broker_name}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Server</p>
                          <p className="font-medium text-gray-900">{account.server_name}</p>
                        </div>
                        {account.account_balance && (
                          <div>
                            <p className="text-gray-500">Balance</p>
                            <p className="font-medium text-gray-900">
                              ${parseFloat(account.account_balance).toFixed(2)}
                            </p>
                          </div>
                        )}
                      </div>

                      {account.last_sync_at && (
                        <p className="text-xs text-gray-500 mt-3">
                          Last synced: {new Date(account.last_sync_at).toLocaleString()}
                        </p>
                      )}

                      {account.last_connection_error && (
                        <div className="mt-3 bg-red-50 border border-red-200 rounded p-3">
                          <p className="text-xs text-red-700">
                            <strong>Connection Error:</strong> {account.last_connection_error}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => handleSync(account.id)}
                        disabled={syncing === account.id}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition disabled:opacity-50"
                        title="Sync trades"
                      >
                        <RefreshCw className={`h-5 w-5 ${syncing === account.id ? 'animate-spin' : ''}`} />
                      </button>
                      <button
                        onClick={() => handleDelete(account.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                        title="Remove account"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">About MT5 Integration</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Your MT5 credentials are encrypted and stored securely</li>
            <li>• Trades are automatically synchronized when you click the sync button</li>
            <li>• You can connect multiple MT5 accounts</li>
            <li>• Historical trades will be imported on first sync</li>
            <li>• Make sure MetaTrader 5 terminal is running for connection to work</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
