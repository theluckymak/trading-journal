import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { ArrowLeft } from 'lucide-react';

export default function NewTrade() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    symbol: '',
    trade_type: 'BUY',
    volume: '',
    open_price: '',
    close_price: '',
    stop_loss: '',
    take_profit: '',
    open_time: '',
    close_time: '',
    commission: '0',
    swap: '0',
    is_closed: false,
  });

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Convert string values to numbers
      const tradeData = {
        symbol: formData.symbol,
        trade_type: formData.trade_type,
        volume: parseFloat(formData.volume),
        open_price: parseFloat(formData.open_price),
        close_price: formData.close_price ? parseFloat(formData.close_price) : null,
        stop_loss: formData.stop_loss ? parseFloat(formData.stop_loss) : null,
        take_profit: formData.take_profit ? parseFloat(formData.take_profit) : null,
        open_time: new Date(formData.open_time).toISOString(),
        close_time: formData.close_time ? new Date(formData.close_time).toISOString() : null,
        commission: parseFloat(formData.commission),
        swap: parseFloat(formData.swap),
        is_closed: formData.is_closed,
      };

      await apiClient.createTrade(tradeData);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create trade');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Add New Trade</h1>
              <p className="text-sm text-gray-600">Manually log a trade to your journal</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow">
          <form onSubmit={handleSubmit} className="p-6">
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Symbol */}
              <div>
                <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-1">
                  Symbol *
                </label>
                <input
                  id="symbol"
                  name="symbol"
                  type="text"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="EURUSD"
                  value={formData.symbol}
                  onChange={handleChange}
                />
              </div>

              {/* Trade Type */}
              <div>
                <label htmlFor="trade_type" className="block text-sm font-medium text-gray-700 mb-1">
                  Type *
                </label>
                <select
                  id="trade_type"
                  name="trade_type"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.trade_type}
                  onChange={handleChange}
                >
                  <option value="BUY">Buy</option>
                  <option value="SELL">Sell</option>
                </select>
              </div>

              {/* Volume */}
              <div>
                <label htmlFor="volume" className="block text-sm font-medium text-gray-700 mb-1">
                  Volume (Lots) *
                </label>
                <input
                  id="volume"
                  name="volume"
                  type="number"
                  step="0.01"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.01"
                  value={formData.volume}
                  onChange={handleChange}
                />
              </div>

              {/* Open Price */}
              <div>
                <label htmlFor="open_price" className="block text-sm font-medium text-gray-700 mb-1">
                  Entry Price *
                </label>
                <input
                  id="open_price"
                  name="open_price"
                  type="number"
                  step="0.00001"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1.10500"
                  value={formData.open_price}
                  onChange={handleChange}
                />
              </div>

              {/* Close Price */}
              <div>
                <label htmlFor="close_price" className="block text-sm font-medium text-gray-700 mb-1">
                  Exit Price
                </label>
                <input
                  id="close_price"
                  name="close_price"
                  type="number"
                  step="0.00001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1.10600"
                  value={formData.close_price}
                  onChange={handleChange}
                />
              </div>

              {/* Stop Loss */}
              <div>
                <label htmlFor="stop_loss" className="block text-sm font-medium text-gray-700 mb-1">
                  Stop Loss
                </label>
                <input
                  id="stop_loss"
                  name="stop_loss"
                  type="number"
                  step="0.00001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1.10400"
                  value={formData.stop_loss}
                  onChange={handleChange}
                />
              </div>

              {/* Take Profit */}
              <div>
                <label htmlFor="take_profit" className="block text-sm font-medium text-gray-700 mb-1">
                  Take Profit
                </label>
                <input
                  id="take_profit"
                  name="take_profit"
                  type="number"
                  step="0.00001"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1.10700"
                  value={formData.take_profit}
                  onChange={handleChange}
                />
              </div>

              {/* Open Time */}
              <div>
                <label htmlFor="open_time" className="block text-sm font-medium text-gray-700 mb-1">
                  Entry Time *
                </label>
                <input
                  id="open_time"
                  name="open_time"
                  type="datetime-local"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.open_time}
                  onChange={handleChange}
                />
              </div>

              {/* Close Time */}
              <div>
                <label htmlFor="close_time" className="block text-sm font-medium text-gray-700 mb-1">
                  Exit Time
                </label>
                <input
                  id="close_time"
                  name="close_time"
                  type="datetime-local"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.close_time}
                  onChange={handleChange}
                />
              </div>

              {/* Commission */}
              <div>
                <label htmlFor="commission" className="block text-sm font-medium text-gray-700 mb-1">
                  Commission
                </label>
                <input
                  id="commission"
                  name="commission"
                  type="number"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                  value={formData.commission}
                  onChange={handleChange}
                />
              </div>

              {/* Swap */}
              <div>
                <label htmlFor="swap" className="block text-sm font-medium text-gray-700 mb-1">
                  Swap
                </label>
                <input
                  id="swap"
                  name="swap"
                  type="number"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="0.00"
                  value={formData.swap}
                  onChange={handleChange}
                />
              </div>

              {/* Is Closed */}
              <div className="md:col-span-2">
                <label className="flex items-center">
                  <input
                    id="is_closed"
                    name="is_closed"
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    checked={formData.is_closed}
                    onChange={handleChange}
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    This trade is closed
                  </span>
                </label>
              </div>
            </div>

            <div className="mt-8 flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Adding Trade...' : 'Add Trade'}
              </button>
              <button
                type="button"
                onClick={() => router.push('/dashboard')}
                className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        {/* Info */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Manual Trade Entry</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Enter your trade details manually from your broker's trading history</li>
            <li>• You can add journal notes and analysis after creating the trade</li>
            <li>• Profit/loss will be calculated automatically based on entry and exit prices</li>
            <li>• Leave exit price empty for open trades</li>
          </ul>
        </div>
      </main>
    </div>
  );
}
