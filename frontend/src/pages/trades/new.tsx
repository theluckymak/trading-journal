import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { ArrowLeft } from 'lucide-react';

type MarketType = 'forex' | 'futures' | 'crypto';

const SYMBOL_SUGGESTIONS = {
  forex: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY', 'XAUUSD (Gold)'],
  futures: ['NQ (E-mini Nasdaq)', 'ES (E-mini S&P 500)', 'YM (E-mini Dow)', 'RTY (E-mini Russell)', 'CL (Crude Oil)', 'GC (Gold)', 'SI (Silver)', 'NG (Natural Gas)', 'ZB (T-Bond)', 'ZN (10Y Note)'],
  crypto: ['BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD', 'DOGEUSD', 'MATICUSD', 'AVAXUSD', 'LINKUSD'],
};

export default function NewTrade() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [marketType, setMarketType] = useState<MarketType>('forex');
  
  const [formData, setFormData] = useState({
    symbol: '',
    trade_type: 'buy',
    volume: '',
    open_price: '',
    close_price: '',
    open_time: '',
    close_time: '',
    is_closed: false,
  });

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      const tradeData = {
        symbol: formData.symbol,
        trade_type: formData.trade_type,
        volume: parseFloat(formData.volume),
        open_price: parseFloat(formData.open_price),
        close_price: formData.close_price ? parseFloat(formData.close_price) : null,
        open_time: formData.open_time ? new Date(formData.open_time).toISOString() : new Date().toISOString(),
        close_time: formData.close_time ? new Date(formData.close_time).toISOString() : null,
        is_closed: formData.is_closed,
        commission: 0.0,
        swap: 0.0,
        stop_loss: null,
        take_profit: null,
        profit: null,
      };

      console.log('Submitting trade data:', tradeData);
      
      // Get access token from localStorage
      let accessToken = localStorage.getItem('accessToken');
      console.log('[DEBUG] Access token from localStorage:', accessToken ? `${accessToken.substring(0, 50)}...` : 'NULL');
      
      if (!accessToken) {
        setError('Not authenticated. Please log in again.');
        return;
      }

      // Use native fetch API instead of axios due to network issues
      let response = await fetch('http://localhost:8000/api/trades', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(tradeData),
      });

      console.log('[DEBUG] Response status:', response.status);
      console.log('[DEBUG] Response ok:', response.ok);

      // If 401, try to refresh token and retry
      if (response.status === 401) {
        console.log('[DEBUG] Token expired, attempting refresh...');
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (refreshToken) {
          try {
            const refreshResponse = await fetch('http://localhost:8000/api/auth/refresh', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json();
              const newAccessToken = refreshData.access_token;
              localStorage.setItem('accessToken', newAccessToken);
              console.log('[DEBUG] Token refreshed successfully, retrying request...');

              // Retry the trade creation with new token
              response = await fetch('http://localhost:8000/api/trades', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${newAccessToken}`,
                },
                body: JSON.stringify(tradeData),
              });
              console.log('[DEBUG] Retry response status:', response.status);
            } else {
              console.error('[DEBUG] Token refresh failed');
              setError('Session expired. Please log in again.');
              setTimeout(() => router.push('/login'), 2000);
              return;
            }
          } catch (refreshError) {
            console.error('[DEBUG] Token refresh error:', refreshError);
            setError('Session expired. Please log in again.');
            setTimeout(() => router.push('/login'), 2000);
            return;
          }
        } else {
          setError('Session expired. Please log in again.');
          setTimeout(() => router.push('/login'), 2000);
          return;
        }
      }

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        
        const detail = errorData.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((e: any) => `${e.loc?.join(' → ') || 'Field'}: ${e.msg}`).join(', ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError(`Failed to create trade: ${response.status}`);
        }
        return;
      }

      const result = await response.json();
      console.log('Trade created successfully:', result);
      setSuccess(true);
      
      // Show success message then redirect
      setTimeout(() => {
        router.push('/dashboard');
      }, 1500);
    } catch (err: any) {
      console.error('Trade creation error:', err);
      
      if (err.message) {
        setError(`Error: ${err.message}`);
      } else {
        setError('Failed to create trade. Please check the console for details.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Add New Trade</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">Record your trading activity</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {/* Market Type Tabs */}
          <div className="border-b dark:border-gray-700">
            <div className="flex">
              <button
                type="button"
                onClick={() => {
                  setMarketType('forex');
                  setFormData({ ...formData, symbol: '' });
                }}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition ${
                  marketType === 'forex'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                💱 Forex
              </button>
              <button
                type="button"
                onClick={() => {
                  setMarketType('futures');
                  setFormData({ ...formData, symbol: '' });
                }}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition ${
                  marketType === 'futures'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                📈 Futures
              </button>
              <button
                type="button"
                onClick={() => {
                  setMarketType('crypto');
                  setFormData({ ...formData, symbol: '' });
                }}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition ${
                  marketType === 'crypto'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                ₿ Crypto
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-6">
            {success && (
              <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Trade added successfully! Redirecting...
              </div>
            )}
            {error && (
              <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div className="space-y-6">
              {/* Symbol Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Select Symbol *
                </label>
                <select
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  required
                >
                  <option value="">Choose a symbol...</option>
                  {SYMBOL_SUGGESTIONS[marketType].map((symbol) => (
                    <option key={symbol} value={symbol.split(' ')[0]}>
                      {symbol}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Trade Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Direction *
                  </label>
                  <select
                    value={formData.trade_type}
                    onChange={(e) => setFormData({ ...formData, trade_type: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    required
                  >
                    <option value="buy">Buy / Long</option>
                    <option value="sell">Sell / Short</option>
                  </select>
                </div>

                {/* Volume */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {marketType === 'forex' ? 'Lots' : marketType === 'futures' ? 'Contracts' : 'Amount'} *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.volume}
                    onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    placeholder={marketType === 'forex' ? '1.0' : marketType === 'futures' ? '1' : '0.1'}
                    required
                  />
                </div>

                {/* Open Price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Entry Price *
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={formData.open_price}
                    onChange={(e) => setFormData({ ...formData, open_price: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    placeholder="Entry price"
                    required
                  />
                </div>

                {/* Close Price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Exit Price
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={formData.close_price}
                    onChange={(e) => setFormData({ ...formData, close_price: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    placeholder="Leave empty if still open"
                  />
                </div>

                {/* Open Time */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Entry Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.open_time}
                    onChange={(e) => setFormData({ ...formData, open_time: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Leave empty for current time</p>
                </div>

                {/* Close Time */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Exit Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.close_time}
                    onChange={(e) => setFormData({ ...formData, close_time: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    disabled={!formData.close_price}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Only if trade is closed</p>
                </div>
              </div>

              {/* Closed Checkbox */}
              <div className="pt-4 border-t dark:border-gray-700">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_closed}
                    onChange={(e) => setFormData({ ...formData, is_closed: e.target.checked })}
                    className="w-5 h-5 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700 dark:text-gray-300">This trade is closed</span>
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition font-medium text-base"
                >
                  {loading ? 'Saving...' : '✓ Add Trade'}
                </button>
                <button
                  type="button"
                  onClick={() => router.push('/dashboard')}
                  className="flex-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 py-3 px-6 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition font-medium text-base"
                >
                  Cancel
                </button>
              </div>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
