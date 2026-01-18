import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  Plus,
  Search,
  Filter,
  Download,
  Eye,
  Edit,
  Trash2,
  TrendingUp,
  TrendingDown,
  Calendar,
  DollarSign,
} from 'lucide-react';

interface Trade {
  id: number;
  symbol: string;
  trade_type: string;
  volume: number;
  open_price: number;
  close_price: number | null;
  profit: number | null;
  net_profit: number | null;
  open_time: string;
  close_time: string | null;
  is_closed: boolean;
  commission: number;
  swap: number;
  notes: string | null;
  tags: string | null;
}

export default function TradesPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filteredTrades, setFilteredTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'buy' | 'sell' | 'open' | 'closed'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'profit' | 'symbol'>('date');

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadTrades();
  }, [user]);

  useEffect(() => {
    filterAndSortTrades();
  }, [trades, searchTerm, filterType, sortBy]);

  const loadTrades = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTrades({ limit: 1000 });
      setTrades(data);
    } catch (error) {
      console.error('Failed to load trades:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortTrades = () => {
    let filtered = [...trades];

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(
        (trade) =>
          trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
          trade.notes?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply filters
    if (filterType === 'buy') {
      filtered = filtered.filter((t) => t.trade_type.toLowerCase() === 'buy');
    } else if (filterType === 'sell') {
      filtered = filtered.filter((t) => t.trade_type.toLowerCase() === 'sell');
    } else if (filterType === 'open') {
      filtered = filtered.filter((t) => !t.is_closed);
    } else if (filterType === 'closed') {
      filtered = filtered.filter((t) => t.is_closed);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.open_time).getTime() - new Date(a.open_time).getTime();
      } else if (sortBy === 'profit') {
        return (b.net_profit || 0) - (a.net_profit || 0);
      } else if (sortBy === 'symbol') {
        return a.symbol.localeCompare(b.symbol);
      }
      return 0;
    });

    setFilteredTrades(filtered);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this trade?')) return;

    try {
      await apiClient.deleteTrade(id);
      setTrades(trades.filter((t) => t.id !== id));
    } catch (error) {
      console.error('Failed to delete trade:', error);
      alert('Failed to delete trade');
    }
  };

  const formatCurrency = (value: number | null) => {
    if (value === null) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <TrendingUp className="h-12 w-12 text-blue-600 mx-auto animate-pulse" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading trades...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Trades</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage and analyze your trading history
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Trades</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{trades.length}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Open Trades</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-2">
              {trades.filter((t) => !t.is_closed).length}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Winning Trades</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
              {trades.filter((t) => t.is_closed && (t.net_profit || 0) > 0).length}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Losing Trades</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">
              {trades.filter((t) => t.is_closed && (t.net_profit || 0) < 0).length}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search trades..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Trades</option>
              <option value="buy">Buy Only</option>
              <option value="sell">Sell Only</option>
              <option value="open">Open Trades</option>
              <option value="closed">Closed Trades</option>
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="date">Sort by Date</option>
              <option value="profit">Sort by Profit</option>
              <option value="symbol">Sort by Symbol</option>
            </select>

            {/* New Trade Button */}
            <button
              onClick={() => router.push('/trades/new')}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Plus className="h-5 w-5" />
              New Trade
            </button>
          </div>
        </div>

        {/* Trades Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Open Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Close Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Volume
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Profit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-gray-700">
                {filteredTrades.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                      No trades found. Create your first trade to get started!
                    </td>
                  </tr>
                ) : (
                  filteredTrades.map((trade) => (
                    <tr
                      key={trade.id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {trade.symbol}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            trade.trade_type.toLowerCase() === 'buy'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                          }`}
                        >
                          {trade.trade_type.toLowerCase() === 'buy' ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {trade.trade_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatDate(trade.open_time)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {trade.close_time ? formatDate(trade.close_time) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {trade.volume}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`font-medium ${
                            (trade.net_profit || 0) >= 0
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}
                        >
                          {formatCurrency(trade.net_profit)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            trade.is_closed
                              ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                          }`}
                        >
                          {trade.is_closed ? 'Closed' : 'Open'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => router.push(`/trades/${trade.id}`)}
                            className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
                            title="View"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => router.push(`/trades/edit/${trade.id}`)}
                            className="p-2 text-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition"
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(trade.id)}
                            className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
}
