import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { ArrowLeft, Calendar, TrendingUp, TrendingDown, DollarSign, Activity, Trash2, Edit, AlertCircle } from 'lucide-react';

// Cache bust: 2026-01-20-v2

interface Trade {
  id: number;
  symbol: string;
  trade_type: string;
  volume: number;
  open_price: number;
  close_price: number | null;
  open_time: string;
  close_time: string | null;
  profit: number | null;
  net_profit: number | null;
  commission: number;
  swap: number;
  is_closed: boolean;
  created_at: string;
}

interface JournalEntry {
  id: number;
  title: string | null;
  notes: string | null;
  pre_trade_analysis: string | null;
  post_trade_analysis: string | null;
  emotional_state: string | null;
  mistakes: string | null;
  lessons_learned: string | null;
  screenshot_urls: string | null;
  trade_id: number | null;
  created_at: string;
  updated_at: string;
}

export default function TradeDetail() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  const [trade, setTrade] = useState<Trade | null>(null);
  const [journal, setJournal] = useState<JournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [editingJournal, setEditingJournal] = useState(false);
  const [journalData, setJournalData] = useState({
    content: '',
    tags: '',
    mood: 'neutral' as 'positive' | 'neutral' | 'negative',
  });

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    if (id) {
      fetchTrade();
    }
  }, [user, id, router]);

  const fetchTrade = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTrade(Number(id));
      setTrade(data);
      await fetchJournal();
    } catch (err: any) {
      setError('Failed to load trade');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchJournal = async () => {
    try {
      const response = await fetch(`https://dependable-solace-production-75f7.up.railway.app/api/journal/entries/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });
      
      if (response.ok) {
        const entry = await response.json();
        setJournal(entry);
        setJournalData({
          content: entry.notes || '',
          tags: entry.mistakes || '',
          mood: entry.emotional_state || 'neutral',
        });
      }
    } catch (err) {
      console.error('Failed to load journal:', err);
    }
  };

  const saveJournal = async () => {
    try {
      const payload = {
        title: `Trade: ${trade?.symbol}`,
        notes: journalData.content,
        pre_trade_analysis: '',
        post_trade_analysis: '',
        emotional_state: journalData.mood,
        mistakes: journalData.tags || '',
        lessons_learned: '',
        screenshot_urls: [],
      };

      const url = `https://dependable-solace-production-75f7.up.railway.app/api/journal/entries/${id}`;
      const method = 'POST';

      console.log('Saving journal:', { url, payload, tradeId: id });

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify(payload),
      });

      console.log('Response status:', response.status);

      if (response.ok) {
        await fetchJournal();
        setEditingJournal(false);
        alert('Journal saved successfully!');
      } else {
        const errorData = await response.json();
        console.error('Save error:', errorData);
        const errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : errorData.detail?.msg || errorData.message || JSON.stringify(errorData.detail) || 'Unknown error';
        alert(`Failed to save journal: ${errorMessage}\n\nIf this trade was created by another user, you cannot add a journal to it.`);
      }
    } catch (err: any) {
      console.error('Error saving journal:', err);
      const errorMessage = err.message || 'Network error occurred';
      alert(`Failed to save journal: ${errorMessage}`);
    }
  };

  const formatCurrency = (value: number | null) => {
    if (value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleDelete = async () => {
    if (!id) return;
    
    try {
      setDeleting(true);
      await apiClient.deleteTrade(Number(id));
      router.push('/dashboard?deleted=true');
    } catch (err: any) {
      setError('Failed to delete trade');
      console.error(err);
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !trade) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Trade Not Found</h2>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const isProfitable = trade.net_profit !== null && trade.net_profit >= 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-300" />
            </button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Trade Details</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">#{trade.id}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(`/trades/edit/${trade.id}`)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
              >
                <Edit className="h-4 w-4" />
                Edit
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 dark:bg-red-900 rounded-full">
                <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Delete Trade</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Are you sure you want to delete this trade? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2 disabled:opacity-50"
              >
                {deleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Compact Trade Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white">{trade.symbol}</h2>
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  trade.trade_type === 'buy'
                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                    : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                }`}
              >
                {trade.trade_type.toUpperCase()}
              </span>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  trade.is_closed
                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                    : 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                }`}
              >
                {trade.is_closed ? 'Closed' : 'Open'}
              </span>
            </div>
            <div className="text-right">
              <p
                className={`text-4xl font-bold ${
                  isProfitable ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}
              >
                {formatCurrency(trade.net_profit)}
              </p>
            </div>
          </div>
        </div>

        {/* Journal Section */}
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Activity className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" />
              Trade Journal
            </h3>
            {journal && !editingJournal && (
              <button
                onClick={() => setEditingJournal(true)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Edit
              </button>
            )}
          </div>

          {!journal && !editingJournal ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400 mb-4">No journal entry for this trade yet</p>
              <button
                onClick={() => setEditingJournal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                Add Journal Entry
              </button>
            </div>
          ) : editingJournal ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Notes & Analysis
                </label>
                <textarea
                  value={journalData.content}
                  onChange={(e) => setJournalData({ ...journalData, content: e.target.value })}
                  rows={6}
                  placeholder="What was your thought process? Why did you take this trade? What did you learn?"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mood
                </label>
                <select
                  value={journalData.mood}
                  onChange={(e) => setJournalData({ ...journalData, mood: e.target.value as any })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="positive">😊 Positive</option>
                  <option value="neutral">😐 Neutral</option>
                  <option value="negative">😟 Negative</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={journalData.tags}
                  onChange={(e) => setJournalData({ ...journalData, tags: e.target.value })}
                  placeholder="breakout, momentum, patience, etc."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  📸 Setup Photo URL (optional)
                </label>
                <input
                  type="text"
                  placeholder="https://example.com/setup-screenshot.png"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  📸 Trade Photo URL (optional)
                </label>
                <input
                  type="text"
                  placeholder="https://example.com/trade-screenshot.png"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={saveJournal}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                >
                  Save Journal
                </button>
                <button
                  onClick={() => {
                    setEditingJournal(false);
                    if (journal) {
                      setJournalData({
                        content: journal.notes || '',
                        tags: journal.mistakes || '',
                        mood: (journal.emotional_state as 'positive' | 'neutral' | 'negative') || 'neutral',
                      });
                    }
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{journal?.notes}</p>
              </div>

              {journal?.mistakes && (
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Mistakes:</p>
                  <div className="text-gray-800 dark:text-gray-200">
                    {journal.mistakes}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Mood:</span>
                <span className="font-medium">
                  {journal?.emotional_state === 'positive' && '😊 Positive'}
                  {journal?.emotional_state === 'neutral' && '😐 Neutral'}
                  {journal?.emotional_state === 'negative' && '😟 Negative'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Trade Details Grid */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Entry Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-green-600 dark:text-green-400" />
                Entry
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Price</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">{trade.open_price.toFixed(5)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Time</p>
                  <p className="text-base text-gray-900 dark:text-gray-200">{formatDate(trade.open_time)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Volume</p>
                  <p className="text-base text-gray-900 dark:text-gray-200">{trade.volume}</p>
                </div>
              </div>
            </div>

            {/* Exit Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <TrendingDown className="h-5 w-5 mr-2 text-red-600 dark:text-red-400" />
                Exit
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Price</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {trade.close_price ? trade.close_price.toFixed(5) : 'Open'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Time</p>
                  <p className="text-base text-gray-900 dark:text-gray-200">
                    {trade.close_time ? formatDate(trade.close_time) : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Gross P/L</p>
                  <p
                    className={`text-base font-semibold ${
                      trade.profit && trade.profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {formatCurrency(trade.profit)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Calendar className="h-5 w-5 mr-2 text-gray-600 dark:text-gray-400" />
            Metadata
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Created</span>
              <span className="text-gray-900 dark:text-gray-200">{formatDate(trade.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Trade ID</span>
              <span className="text-gray-900 dark:text-gray-200">#{trade.id}</span>
            </div>
          </div>
        </div>

        {/* Financial Details */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <DollarSign className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
            Financial Breakdown
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Gross Profit/Loss</span>
              <span className="font-semibold dark:text-gray-200">{formatCurrency(trade.profit)}</span>
            </div>
            <div className="flex justify-between py-2 border-b dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Commission</span>
              <span className="font-semibold text-red-600 dark:text-red-400">{formatCurrency(trade.commission)}</span>
            </div>
            <div className="flex justify-between py-2 border-b dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Swap</span>
              <span className="font-semibold text-red-600 dark:text-red-400">{formatCurrency(trade.swap)}</span>
            </div>
            <div className="flex justify-between py-3 bg-gray-50 dark:bg-gray-900 px-3 rounded-lg">
              <span className="text-gray-900 dark:text-white font-semibold">Net Profit/Loss</span>
              <span
                className={`text-lg font-bold ${
                  isProfitable ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                }`}
              >
                {formatCurrency(trade.net_profit)}
              </span>
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <Calendar className="h-5 w-5 mr-2 text-gray-600 dark:text-gray-400" />
            Metadata
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Created</span>
              <span className="text-gray-900 dark:text-gray-200">{formatDate(trade.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Trade ID</span>
              <span className="text-gray-900 dark:text-gray-200">#{trade.id}</span>
            </div>
          </div>
        </div>

        {/* Journal Section */}
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Activity className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" />
              Trade Journal
            </h3>
            {journal && !editingJournal && (
              <button
                onClick={() => setEditingJournal(true)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                Edit
              </button>
            )}
          </div>

          {!journal && !editingJournal ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400 mb-4">No journal entry for this trade yet</p>
              <button
                onClick={() => setEditingJournal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                Add Journal Entry
              </button>
            </div>
          ) : editingJournal ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Notes & Analysis
                </label>
                <textarea
                  value={journalData.content}
                  onChange={(e) => setJournalData({ ...journalData, content: e.target.value })}
                  rows={6}
                  placeholder="What was your thought process? Why did you take this trade? What did you learn?"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mood
                </label>
                <select
                  value={journalData.mood}
                  onChange={(e) => setJournalData({ ...journalData, mood: e.target.value as any })}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="positive">😊 Positive</option>
                  <option value="neutral">😐 Neutral</option>
                  <option value="negative">😟 Negative</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={journalData.tags}
                  onChange={(e) => setJournalData({ ...journalData, tags: e.target.value })}
                  placeholder="breakout, momentum, patience, etc."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  📸 Setup Photo URL (optional)
                </label>
                <input
                  type="text"
                  placeholder="https://example.com/setup-screenshot.png"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  📸 Trade Photo URL (optional)
                </label>
                <input
                  type="text"
                  placeholder="https://example.com/trade-screenshot.png"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={saveJournal}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                >
                  Save Journal
                </button>
                <button
                  onClick={() => {
                    setEditingJournal(false);
                    if (journal) {
                      setJournalData({
                        content: journal.notes || '',
                        tags: journal.mistakes || '',
                        mood: (journal.emotional_state as 'positive' | 'neutral' | 'negative') || 'neutral',
                      });
                    }
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{journal?.notes}</p>
              </div>

              {journal?.mistakes && (
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Tags:</p>
                  <div className="flex flex-wrap gap-2">
                    {journal.mistakes.split(',').map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-sm rounded-full"
                      >
                        {tag.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {journal?.mistakes && (
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Mistakes:</p>
                  <div className="text-gray-800 dark:text-gray-200">
                    {journal.mistakes}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Mood:</span>
                <span className="font-medium">
                  {journal?.emotional_state === 'positive' && '😊 Positive'}
                  {journal?.emotional_state === 'neutral' && '😐 Neutral'}
                  {journal?.emotional_state === 'negative' && '😟 Negative'}
                </span>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
