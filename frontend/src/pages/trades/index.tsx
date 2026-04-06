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
            <TrendingUp className="h-12 w-12 mx-auto animate-pulse" style={{ color: 'var(--brand)' }} />
            <p className="mt-4" style={{ color: 'var(--text-muted)' }}>Loading trades...</p>
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
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text)' }}>Trades</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Manage and analyze your trading history
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card p-6">
            <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Total Trades</p>
            <p className="text-2xl font-bold mt-2" style={{ color: 'var(--text)' }}>{trades.length}</p>
          </div>
          <div className="card p-6">
            <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Open Trades</p>
            <p className="text-2xl font-bold mt-2" style={{ color: 'var(--brand)' }}>
              {trades.filter((t) => !t.is_closed).length}
            </p>
          </div>
          <div className="card p-6">
            <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Winning Trades</p>
            <p className="text-2xl font-bold mt-2" style={{ color: 'var(--success)' }}>
              {trades.filter((t) => t.is_closed && (t.net_profit || 0) > 0).length}
            </p>
          </div>
          <div className="card p-6">
            <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>Losing Trades</p>
            <p className="text-2xl font-bold mt-2" style={{ color: 'var(--error)' }}>
              {trades.filter((t) => t.is_closed && (t.net_profit || 0) < 0).length}
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="card p-6 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5" style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  placeholder="Search trades..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input w-full pl-10 pr-4 py-2"
                />
              </div>
            </div>

            {/* Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="input px-4 py-2"
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
              className="input px-4 py-2"
            >
              <option value="date">Sort by Date</option>
              <option value="profit">Sort by Profit</option>
              <option value="symbol">Sort by Symbol</option>
            </select>

            {/* New Trade Button */}
            <button
              onClick={() => router.push('/trades/new')}
              className="btn btn-brand flex items-center gap-2"
            >
              <Plus className="h-5 w-5" />
              New Trade
            </button>
          </div>
        </div>

        {/* Trades Table */}
        <div className="overflow-hidden" style={{ background: 'var(--bg-card)', borderRadius: '16px', boxShadow: 'var(--shadow)' }}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead style={{ background: 'var(--bg-section)' }}>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Open Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Close Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Volume
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Profit
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'var(--border)' }}>
                {filteredTrades.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center" style={{ color: 'var(--text-muted)' }}>
                      No trades found. Create your first trade to get started!
                    </td>
                  </tr>
                ) : (
                  filteredTrades.map((trade) => (
                    <tr
                      key={trade.id}
                      className="transition"
                      style={{ borderColor: 'var(--border)' }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium" style={{ color: 'var(--text)' }}>
                          {trade.symbol}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium"
                          style={
                            trade.trade_type.toLowerCase() === 'buy'
                              ? { background: 'color-mix(in srgb, var(--success) 15%, transparent)', color: 'var(--success)' }
                              : { background: 'color-mix(in srgb, var(--error) 15%, transparent)', color: 'var(--error)' }
                          }
                        >
                          {trade.trade_type.toLowerCase() === 'buy' ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {trade.trade_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: 'var(--text)' }}>
                        {formatDate(trade.open_time)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: 'var(--text)' }}>
                        {trade.close_time ? formatDate(trade.close_time) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: 'var(--text)' }}>
                        {trade.volume}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className="font-medium"
                          style={{
                            color: (trade.net_profit || 0) >= 0 ? 'var(--success)' : 'var(--error)',
                          }}
                        >
                          {formatCurrency(trade.net_profit)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium"
                          style={
                            trade.is_closed
                              ? { background: 'var(--bg-section)', color: 'var(--text-muted)' }
                              : { background: 'color-mix(in srgb, var(--brand) 15%, transparent)', color: 'var(--brand)' }
                          }
                        >
                          {trade.is_closed ? 'Closed' : 'Open'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => router.push(`/trades/${trade.id}`)}
                            className="p-2 rounded-lg transition"
                            style={{ color: 'var(--brand)' }}
                            title="View"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => router.push(`/trades/edit/${trade.id}`)}
                            className="p-2 rounded-lg transition"
                            style={{ color: 'var(--text-muted)' }}
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(trade.id)}
                            className="p-2 rounded-lg transition"
                            style={{ color: 'var(--error)' }}
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
