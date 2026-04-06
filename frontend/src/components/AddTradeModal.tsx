import { useState } from 'react';
import { useRouter } from 'next/router';
import { X } from 'lucide-react';

type MarketType = 'forex' | 'futures' | 'crypto';

const SYMBOL_SUGGESTIONS = {
  forex: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY', 'XAUUSD (Gold)'],
  futures: ['NQ (E-mini Nasdaq)', 'ES (E-mini S&P 500)', 'YM (E-mini Dow)', 'RTY (E-mini Russell)', 'CL (Crude Oil)', 'GC (Gold)', 'SI (Silver)', 'NG (Natural Gas)', 'ZB (T-Bond)', 'ZN (10Y Note)'],
  crypto: ['BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD', 'DOGEUSD', 'MATICUSD', 'AVAXUSD', 'LINKUSD'],
};

interface AddTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function AddTradeModal({ isOpen, onClose, onSuccess }: AddTradeModalProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [marketType, setMarketType] = useState<MarketType>('forex');
  
  const [includeJournal, setIncludeJournal] = useState(false);
  const [includeSetupPhoto, setIncludeSetupPhoto] = useState(false);
  const [includeTradePhoto, setIncludeTradePhoto] = useState(false);
  
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
  
  const [journalData, setJournalData] = useState({
    content: '',
    tags: '',
    mood: 'neutral' as 'positive' | 'neutral' | 'negative',
  });

  const resetForm = () => {
    setFormData({
      symbol: '',
      trade_type: 'buy',
      volume: '',
      open_price: '',
      close_price: '',
      open_time: '',
      close_time: '',
      is_closed: false,
    });
    setJournalData({
      content: '',
      tags: '',
      mood: 'neutral',
    });
    setIncludeJournal(false);
    setIncludeSetupPhoto(false);
    setIncludeTradePhoto(false);
    setError('');
    setSuccess(false);
    setMarketType('forex');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

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

      let accessToken = localStorage.getItem('accessToken');
      
      if (!accessToken) {
        setError('Not authenticated. Please log in again.');
        return;
      }

      let response = await fetch('https://dependable-solace-production-75f7.up.railway.app/api/trades', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(tradeData),
      });

      // If 401, try to refresh token and retry
      if (response.status === 401) {
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (refreshToken) {
          try {
            const refreshResponse = await fetch('https://dependable-solace-production-75f7.up.railway.app/api/auth/refresh', {
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

              response = await fetch('https://dependable-solace-production-75f7.up.railway.app/api/trades', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${newAccessToken}`,
                },
                body: JSON.stringify(tradeData),
              });
            } else {
              setError('Session expired. Please log in again.');
              setTimeout(() => router.push('/login'), 2000);
              return;
            }
          } catch (refreshError) {
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

      const createdTrade = await response.json();

      // Create journal entry if enabled
      if (includeJournal && journalData.content.trim()) {
        try {
          const journalPayload = {
            title: `Trade: ${formData.symbol}`,
            notes: journalData.content,
            pre_trade_analysis: '',
            post_trade_analysis: '',
            emotional_state: journalData.mood,
            mistakes: [],
            lessons_learned: [],
            screenshot_urls: [],
          };

          const journalResponse = await fetch(`https://dependable-solace-production-75f7.up.railway.app/api/journal/entries/${createdTrade.id}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
            },
            body: JSON.stringify(journalPayload),
          });

          if (!journalResponse.ok) {
          }
        } catch (journalError) {
        }
      }

      setSuccess(true);
      
      setTimeout(() => {
        handleClose();
        if (onSuccess) onSuccess();
      }, 1500);
    } catch (err: any) {
      if (err.message) {
        setError(`Error: ${err.message}`);
      } else {
        setError('Failed to create trade. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto" style={{ background: 'var(--bg-card)', boxShadow: 'var(--shadow-md)' }}>
        {/* Header */}
        <div className="sticky top-0 border-b px-6 py-4 flex items-center justify-between" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--text)' }}>Add New Trade</h2>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Record your trading activity</p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-lg transition hover:opacity-80"
          >
            <X className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        {/* Market Type Tabs */}
        <div className="border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex">
            {(['forex', 'futures', 'crypto'] as MarketType[]).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => {
                  setMarketType(type);
                  setFormData({ ...formData, symbol: '' });
                }}
                className="flex-1 px-6 py-4 text-sm font-medium border-b-2 transition"
                style={
                  marketType === type
                    ? { borderColor: 'var(--brand)', color: 'var(--brand)', background: 'var(--brand-light)' }
                    : { borderColor: 'transparent', color: 'var(--text-muted)' }
                }
              >
                {type === 'forex' ? 'Forex' : type === 'futures' ? 'Futures' : 'Crypto'}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {success && (
            <div className="mb-6 px-4 py-3 rounded-lg flex items-center" style={{ background: 'rgba(41,204,106,0.1)', color: 'var(--success)', border: '1px solid var(--success)' }}>
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Trade added successfully!
            </div>
          )}
          {error && (
            <div className="mb-6 px-4 py-3 rounded-lg" style={{ background: 'rgba(255,45,85,0.1)', color: 'var(--error)', border: '1px solid var(--error)' }}>
              {error}
            </div>
          )}

          <div className="space-y-6">
            {/* Symbol Selection */}
            <div>
              <label className="label block text-sm font-medium mb-2">
                Select Symbol *
              </label>
              <select
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
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
                <label className="label block text-sm font-medium mb-2">
                  Direction *
                </label>
                <select
                  value={formData.trade_type}
                  onChange={(e) => setFormData({ ...formData, trade_type: e.target.value })}
                  className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  required
                >
                  <option value="buy">Buy / Long</option>
                  <option value="sell">Sell / Short</option>
                </select>
              </div>

              {/* Volume */}
              <div>
                <label className="label block text-sm font-medium mb-2">
                  {marketType === 'forex' ? 'Lots' : marketType === 'futures' ? 'Contracts' : 'Amount'} *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.volume}
                  onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                  className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  placeholder={marketType === 'forex' ? '1.0' : marketType === 'futures' ? '1' : '0.1'}
                  required
                />
              </div>

              {/* Open Price */}
              <div>
                <label className="label block text-sm font-medium mb-2">
                  Entry Price *
                </label>
                <input
                  type="number"
                  step="0.00001"
                  value={formData.open_price}
                  onChange={(e) => setFormData({ ...formData, open_price: e.target.value })}
                  className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  placeholder="Entry price"
                  required
                />
              </div>

              {/* Close Price */}
              <div>
                <label className="label block text-sm font-medium mb-2">
                  Exit Price
                </label>
                <input
                  type="number"
                  step="0.00001"
                  value={formData.close_price}
                  onChange={(e) => setFormData({ ...formData, close_price: e.target.value })}
                  className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  placeholder="Leave empty if still open"
                />
              </div>

              {/* Open Time */}
              <div>
                <label className="label block text-sm font-medium mb-2">
                  Entry Time
                </label>
                <input
                  type="datetime-local"
                  value={formData.open_time}
                  onChange={(e) => setFormData({ ...formData, open_time: e.target.value })}
                  className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                />
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Leave empty for current time</p>
              </div>

              {/* Close Time */}
              <div>
                <label className="label block text-sm font-medium mb-2">
                  Exit Time
                </label>
                <input
                  type="datetime-local"
                  value={formData.close_time}
                  onChange={(e) => setFormData({ ...formData, close_time: e.target.value })}
                  className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  disabled={!formData.close_price}
                />
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Only if trade is closed</p>
              </div>
            </div>

            {/* Closed Checkbox */}
            <div className="pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_closed}
                  onChange={(e) => setFormData({ ...formData, is_closed: e.target.checked })}
                  className="w-5 h-5 rounded"
                  style={{ accentColor: 'var(--brand)' }}
                />
                <span className="ml-3 text-sm font-medium" style={{ color: 'var(--text)' }}>This trade is closed</span>
              </label>
            </div>

            {/* Journal Toggle */}
            <div className="pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeJournal}
                  onChange={(e) => setIncludeJournal(e.target.checked)}
                  className="w-5 h-5 rounded"
                  style={{ accentColor: 'var(--brand)' }}
                />
                <span className="ml-3 text-sm font-medium" style={{ color: 'var(--text)' }}>Add Journal Entry</span>
              </label>
            </div>

            {/* Journal Section */}
            {includeJournal && (
              <div className="space-y-4 p-4 rounded-lg border" style={{ background: 'var(--bg-section)', borderColor: 'var(--border)' }}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text)' }}>Journal Details</h3>
                
                {/* Photo Toggles */}
                <div className="flex gap-4 mb-4">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeSetupPhoto}
                      onChange={(e) => setIncludeSetupPhoto(e.target.checked)}
                      className="w-4 h-4 rounded"
                      style={{ accentColor: 'var(--brand)' }}
                    />
                    <span className="ml-2 text-sm" style={{ color: 'var(--text-muted)' }}>Setup Photo</span>
                  </label>
                  
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeTradePhoto}
                      onChange={(e) => setIncludeTradePhoto(e.target.checked)}
                      className="w-4 h-4 rounded"
                      style={{ accentColor: 'var(--brand)' }}
                    />
                    <span className="ml-2 text-sm" style={{ color: 'var(--text-muted)' }}>Trade Photo</span>
                  </label>
                </div>

                {/* Setup Photo Upload */}
                {includeSetupPhoto && (
                  <div>
                    <label className="label block text-sm font-medium mb-2">
                      Setup Photo (Before Trade)
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      className="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                    />
                    <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Upload your pre-trade setup/analysis</p>
                  </div>
                )}

                {/* Trade Photo Upload */}
                {includeTradePhoto && (
                  <div>
                    <label className="label block text-sm font-medium mb-2">
                      Trade Photo (Execution)
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      className="w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500"
                      style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                    />
                    <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Upload your final trade screenshot</p>
                  </div>
                )}

                {/* Journal Content */}
                <div>
                  <label className="label block text-sm font-medium mb-2">
                    Notes & Analysis
                  </label>
                  <textarea
                    value={journalData.content}
                    onChange={(e) => setJournalData({ ...journalData, content: e.target.value })}
                    rows={4}
                    placeholder="What was your thought process? Why did you take this trade? What did you learn?"
                    className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  />
                </div>

                {/* Mood */}
                <div>
                  <label className="label block text-sm font-medium mb-2">
                    Mood
                  </label>
                  <select
                    value={journalData.mood}
                    onChange={(e) => setJournalData({ ...journalData, mood: e.target.value as any })}
                    className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500"
                    style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  >
                    <option value="positive">Positive</option>
                    <option value="neutral">Neutral</option>
                    <option value="negative">Negative</option>
                  </select>
                </div>

                {/* Tags */}
                <div>
                  <label className="label block text-sm font-medium mb-2">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={journalData.tags}
                    onChange={(e) => setJournalData({ ...journalData, tags: e.target.value })}
                    placeholder="breakout, momentum, patience, etc."
                    className="input w-full px-4 py-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    style={{ background: 'var(--bg-card)', color: 'var(--text)', borderColor: 'var(--border)' }}
                  />
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4 pt-6">
              <button
                type="submit"
                disabled={loading}
                className="btn btn-brand flex-1 py-3 px-6 rounded-lg transition font-medium disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Add Trade'}
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 py-3 px-6 rounded-lg transition font-medium hover:opacity-80"
                style={{ background: 'var(--bg-section)', color: 'var(--text)' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

