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

export default function EditTrade() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
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
      return;
    }

    if (id) {
      loadTrade();
    }
  }, [user, id, router]);

  const loadTrade = async () => {
    try {
      setLoading(true);
      const trade = await apiClient.getTrade(Number(id));
      
      // Convert date strings to datetime-local format
      const openTime = trade.open_time ? new Date(trade.open_time).toISOString().slice(0, 16) : '';
      const closeTime = trade.close_time ? new Date(trade.close_time).toISOString().slice(0, 16) : '';
      
      setFormData({
        symbol: trade.symbol,
        trade_type: trade.trade_type,
        volume: trade.volume.toString(),
        open_price: trade.open_price.toString(),
        close_price: trade.close_price ? trade.close_price.toString() : '',
        open_time: openTime,
        close_time: closeTime,
        is_closed: trade.is_closed,
      });

      // Detect market type from symbol
      if (SYMBOL_SUGGESTIONS.forex.some(s => trade.symbol.includes(s.split(' ')[0]))) {
        setMarketType('forex');
      } else if (SYMBOL_SUGGESTIONS.futures.some(s => trade.symbol.includes(s.split(' ')[0]))) {
        setMarketType('futures');
      } else if (SYMBOL_SUGGESTIONS.crypto.some(s => trade.symbol.includes(s.split(' ')[0]))) {
        setMarketType('crypto');
      }
    } catch (err: any) {
      setError('Failed to load trade');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);

    try {
      const tradeData = {
        symbol: formData.symbol,
        trade_type: formData.trade_type,
        volume: parseFloat(formData.volume),
        open_price: parseFloat(formData.open_price),
        close_price: formData.close_price ? parseFloat(formData.close_price) : null,
        open_time: formData.open_time ? new Date(formData.open_time).toISOString() : undefined,
        close_time: formData.close_time ? new Date(formData.close_time).toISOString() : null,
        is_closed: formData.is_closed,
      };

      await apiClient.updateTrade(Number(id), tradeData);
      setSuccess(true);
      
      setTimeout(() => {
        router.push(`/trades/${id}`);
      }, 1500);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        const errorMessages = detail.map((e: any) => `${e.loc?.join(' → ') || 'Field'}: ${e.msg}`).join(', ');
        setError(errorMessages);
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Failed to update trade');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push(`/trades/${id}`)}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Edit Trade</h1>
              <p className="text-sm text-gray-600">Update trade details</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow">
          <div className="border-b">
            <div className="flex">
              <button
                type="button"
                onClick={() => setMarketType('forex')}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition ${
                  marketType === 'forex'
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                💱 Forex
              </button>
              <button
                type="button"
                onClick={() => setMarketType('futures')}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition ${
                  marketType === 'futures'
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                📈 Futures
              </button>
              <button
                type="button"
                onClick={() => setMarketType('crypto')}
                className={`flex-1 px-6 py-4 text-sm font-medium border-b-2 transition ${
                  marketType === 'crypto'
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                ₿ Crypto
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-6">
            {success && (
              <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Trade updated successfully! Redirecting...
              </div>
            )}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Symbol *
                </label>
                <select
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  required
                >
                  <option value="">Select a symbol</option>
                  {SYMBOL_SUGGESTIONS[marketType].map((symbol) => (
                    <option key={symbol} value={symbol}>
                      {symbol}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Direction *
                  </label>
                  <select
                    value={formData.trade_type}
                    onChange={(e) => setFormData({ ...formData, trade_type: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    required
                  >
                    <option value="buy">Buy / Long</option>
                    <option value="sell">Sell / Short</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {marketType === 'forex' ? 'Lots' : marketType === 'futures' ? 'Contracts' : 'Amount'} *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.volume}
                    onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Entry Price *
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={formData.open_price}
                    onChange={(e) => setFormData({ ...formData, open_price: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Exit Price
                  </label>
                  <input
                    type="number"
                    step="0.00001"
                    value={formData.close_price}
                    onChange={(e) => setFormData({ ...formData, close_price: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Entry Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.open_time}
                    onChange={(e) => setFormData({ ...formData, open_time: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Exit Time
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.close_time}
                    onChange={(e) => setFormData({ ...formData, close_time: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                    disabled={!formData.close_price}
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_closed}
                    onChange={(e) => setFormData({ ...formData, is_closed: e.target.checked })}
                    className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="ml-3 text-sm font-medium text-gray-700">This trade is closed</span>
                </label>
              </div>

              <div className="flex gap-4 pt-6">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition font-medium text-base"
                >
                  {saving ? 'Saving...' : '✓ Update Trade'}
                </button>
                <button
                  type="button"
                  onClick={() => router.push(`/trades/${id}`)}
                  className="flex-1 bg-gray-100 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-200 transition font-medium text-base"
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
