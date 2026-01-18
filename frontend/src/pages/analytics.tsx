import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Award,
  AlertCircle,
  Calendar,
} from 'lucide-react';

interface Analytics {
  total_trades: number;
  total_profit: number;
  win_rate: number;
  profit_factor: number;
  average_win: number;
  average_loss: number;
  largest_win: number;
  largest_loss: number;
  expectancy: number;
  sharpe_ratio: number;
}

interface Trade {
  id: number;
  symbol: string;
  trade_type: string;
  open_time: string;
  close_time: string | null;
  net_profit: number | null;
  is_closed: boolean;
}

export default function AnalyticsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [allTrades, setAllTrades] = useState<Trade[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState<'7d' | '30d' | '90d' | 'all'>('all');

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadAnalytics();
  }, [user]);

  useEffect(() => {
    // Filter trades when dateRange changes
    if (allTrades.length > 0) {
      filterTrades();
    }
  }, [dateRange, allTrades]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [analyticsData, tradesData] = await Promise.all([
        apiClient.getAnalytics(),
        apiClient.getTrades({ limit: 1000 }),
      ]);
      setAnalytics(analyticsData);
      
      // Store all closed trades
      const closedTrades = tradesData.filter((t: Trade) => t.is_closed);
      setAllTrades(closedTrades);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterTrades = () => {
    let filteredTrades = [...allTrades];
    
    // Apply date range filter
    if (dateRange !== 'all') {
      const now = new Date();
      const daysMap = { '7d': 7, '30d': 30, '90d': 90 };
      const days = daysMap[dateRange];
      const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      
      filteredTrades = filteredTrades.filter((t: Trade) => {
        const closeDate = new Date(t.close_time!);
        return closeDate >= cutoffDate;
      });
    }
    
    setTrades(filteredTrades);
  };

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '0%';
    return `${value.toFixed(2)}%`;
  };

  // Calculate metrics from filtered trades
  const calculatedMetrics = (() => {
    if (trades.length === 0) {
      return {
        total_profit: 0,
        win_rate: 0,
        profit_factor: 0,
        total_trades: 0,
        average_win: 0,
        average_loss: 0,
        largest_win: 0,
        largest_loss: 0,
      };
    }

    const total_profit = trades.reduce((sum, t) => sum + (t.net_profit || 0), 0);
    const wins = trades.filter((t) => (t.net_profit || 0) > 0);
    const losses = trades.filter((t) => (t.net_profit || 0) < 0);
    
    const total_wins_profit = wins.reduce((sum, t) => sum + (t.net_profit || 0), 0);
    const total_losses_profit = Math.abs(losses.reduce((sum, t) => sum + (t.net_profit || 0), 0));
    
    const win_rate = trades.length > 0 ? (wins.length / trades.length) * 100 : 0;
    const profit_factor = total_losses_profit > 0 ? total_wins_profit / total_losses_profit : total_wins_profit > 0 ? 999 : 0;
    const average_win = wins.length > 0 ? total_wins_profit / wins.length : 0;
    const average_loss = losses.length > 0 ? total_losses_profit / losses.length : 0;
    const largest_win = wins.length > 0 ? Math.max(...wins.map(t => t.net_profit || 0)) : 0;
    const largest_loss = losses.length > 0 ? Math.abs(Math.min(...losses.map(t => t.net_profit || 0))) : 0;

    return {
      total_profit,
      win_rate,
      profit_factor,
      total_trades: trades.length,
      average_win,
      average_loss,
      largest_win,
      largest_loss,
    };
  })();

  // Prepare chart data
  const profitOverTime = trades
    .sort((a, b) => new Date(a.close_time!).getTime() - new Date(b.close_time!).getTime())
    .map((trade, index) => ({
      index: index + 1,
      profit: trades.slice(0, index + 1).reduce((sum, t) => sum + (t.net_profit || 0), 0),
      date: new Date(trade.close_time!).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }));

  const tradesBySymbol = trades.reduce((acc: Record<string, number>, trade) => {
    const symbol = trade.symbol;
    acc[symbol] = (acc[symbol] || 0) + 1;
    return acc;
  }, {});

  const symbolData = Object.entries(tradesBySymbol)
    .map(([symbol, count]) => ({ symbol, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const winLossData = [
    {
      name: 'Wins',
      value: trades.filter((t) => (t.net_profit || 0) > 0).length,
      color: '#10b981',
    },
    {
      name: 'Losses',
      value: trades.filter((t) => (t.net_profit || 0) < 0).length,
      color: '#ef4444',
    },
  ];

  const profitByMonth = trades.reduce((acc: Record<string, number>, trade) => {
    const month = new Date(trade.close_time!).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
    });
    acc[month] = (acc[month] || 0) + (trade.net_profit || 0);
    return acc;
  }, {});

  const monthlyData = Object.entries(profitByMonth).map(([month, profit]) => ({
    month,
    profit,
  }));

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <Target className="h-12 w-12 text-blue-600 mx-auto animate-pulse" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading analytics...</p>
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Detailed performance analysis and insights
          </p>
        </div>

        {/* Date Range Filter */}
        <div className="mb-6">
          <div className="flex gap-2">
            {[
              { value: '7d', label: '7 Days' },
              { value: '30d', label: '30 Days' },
              { value: '90d', label: '90 Days' },
              { value: 'all', label: 'All Time' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setDateRange(option.value as any)}
                className={`px-4 py-2 rounded-lg transition ${
                  dateRange === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Profit</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatCurrency(calculatedMetrics.total_profit)}
                </p>
              </div>
              <div className={`p-3 rounded-full ${calculatedMetrics.total_profit >= 0 ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900'}`}>
                {calculatedMetrics.total_profit >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-600 dark:text-red-400" />
                )}
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Win Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {formatPercentage(calculatedMetrics.win_rate)}
                </p>
              </div>
              <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900">
                <Target className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Profit Factor</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {calculatedMetrics.profit_factor?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="p-3 rounded-full bg-purple-100 dark:bg-purple-900">
                <Award className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Trades</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                  {calculatedMetrics.total_trades || 0}
                </p>
              </div>
              <div className="p-3 rounded-full bg-orange-100 dark:bg-orange-900">
                <DollarSign className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Cumulative Profit Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Cumulative Profit
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={profitOverTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#fff',
                  }}
                  cursor={{ stroke: '#3b82f6', strokeWidth: 1, strokeDasharray: '3 3' }}
                />
                <Line
                  type="monotone"
                  dataKey="profit"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Win/Loss Pie Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Win/Loss Ratio
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={winLossData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={110}
                  innerRadius={70}
                  fill="#8884d8"
                  dataKey="value"
                  paddingAngle={6}
                  strokeWidth={2}
                >
                  {winLossData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#1f2937" />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                  }}
                  labelStyle={{ color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                  cursor={false}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(value) => <span style={{ color: '#9ca3af' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Monthly Profit Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Monthly Profit
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#fff',
                  }}
                  cursor={{ fill: 'transparent' }}
                />
                <Bar dataKey="profit" fill="#3b82f6" radius={[16, 16, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top Symbols Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Most Traded Symbols
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={symbolData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" />
                <YAxis dataKey="symbol" type="category" stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#fff',
                  }}
                  cursor={{ fill: 'transparent' }}
                />
                <Bar dataKey="count" fill="#10b981" radius={[0, 16, 16, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Average Win</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
              {formatCurrency(analytics?.average_win)}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Average Loss</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">
              {formatCurrency(analytics?.average_loss)}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Largest Win</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-2">
              {formatCurrency(analytics?.largest_win)}
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Largest Loss</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-2">
              {formatCurrency(analytics?.largest_loss)}
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
