import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Plus,
  Eye,
  BarChart3,
  Calendar,
  Target,
  Zap,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
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
  volume: number;
  open_price: number;
  close_price: number | null;
  profit: number | null;
  net_profit: number | null;
  open_time: string;
  close_time: string | null;
  is_closed: boolean;
}

// Win Rate Progress Ring Component
const WinRateRing = ({ percentage }: { percentage: number }) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-28 h-28">
      <svg className="w-28 h-28 transform -rotate-90">
        <circle
          cx="56"
          cy="56"
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="8"
          fill="none"
        />
        <circle
          cx="56"
          cy="56"
          r={radius}
          stroke="url(#gradient)"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold text-white">{percentage.toFixed(1)}%</span>
      </div>
    </div>
  );
};

// Mini Calendar Component
const MiniCalendar = ({ tradingDays }: { tradingDays: Date[] }) => {
  const today = new Date();
  const currentMonth = today.getMonth();
  const currentYear = today.getFullYear();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDay = new Date(currentYear, currentMonth, 1).getDay();
  const adjustedFirstDay = firstDay === 0 ? 6 : firstDay - 1;

  const monthName = today.toLocaleString('default', { month: 'long' });
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  const isTradingDay = (day: number) => {
    return tradingDays.some(d => 
      d.getDate() === day && 
      d.getMonth() === currentMonth && 
      d.getFullYear() === currentYear
    );
  };

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-slate-200 font-medium">Trading Activity</h3>
        <span className="text-slate-500 text-sm">{monthName}</span>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center">
        {days.map(day => (
          <div key={day} className="text-xs text-slate-600 py-1">{day}</div>
        ))}
        {Array.from({ length: adjustedFirstDay }).map((_, i) => (
          <div key={`empty-${i}`} className="py-1" />
        ))}
        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          const isToday = day === today.getDate();
          const hasTraded = isTradingDay(day);
          return (
            <div
              key={day}
              className={`py-1 text-sm rounded-full transition-all ${
                isToday
                  ? 'bg-cyan-500/80 text-white font-bold'
                  : hasTraded
                  ? 'bg-white/10 text-cyan-300'
                  : 'text-slate-500 hover:bg-white/5'
              }`}
            >
              {day}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default function Dashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [tradingDays, setTradingDays] = useState<Date[]>([]);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadDashboardData();
  }, [user, router]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [analyticsRes, tradesRes] = await Promise.all([
        apiClient.getAnalytics(),
        apiClient.getTrades({ limit: 10 }),
      ]);

      setAnalytics(analyticsRes);
      setTrades(tradesRes);
      
      const days = tradesRes.map((t: Trade) => new Date(t.open_time));
      setTradingDays(days);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const userName = user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'Trader';

  if (loading) {
    return (
      <Layout>
        <div className="min-h-screen bg-[#0a0f1a] flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-cyan-500/60 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="mt-4 text-slate-500">Loading your dashboard...</p>
          </div>
        </div>
      </Layout>
    );
  }

  const winRate = analytics?.win_rate || 0;
  const totalProfit = analytics?.total_profit || 0;
  const isProfit = totalProfit >= 0;

  return (
    <Layout>
      <div className="min-h-screen bg-[#0a0f1a] p-6 lg:p-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-white mb-1">
              {getGreeting()}, <span className="text-cyan-400">{userName}</span>
            </h1>
            <p className="text-slate-500 text-sm">Ready for today's market challenges</p>
          </div>
          <div className="flex items-center gap-3 mt-4 lg:mt-0">
            <div className="relative">
              <input
                type="text"
                placeholder="Search trades..."
                className="bg-white/5 backdrop-blur-md border border-white/10 rounded-full px-5 py-2 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 w-60 text-sm"
              />
            </div>
            <button 
              onClick={() => router.push('/trades/new')}
              className="bg-gradient-to-r from-cyan-500/80 to-blue-500/80 hover:from-cyan-500 hover:to-blue-500 text-white font-medium px-5 py-2 rounded-full transition-all flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" />
              New Trade
            </button>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Stats */}
          <div className="col-span-12 lg:col-span-8 space-y-6">
            {/* P&L Card */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-slate-200 font-medium">Trading Performance</h3>
                <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-slate-300 text-sm focus:outline-none">
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="all">All Time</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* P&L Chart Area */}
                <div className="bg-white/[0.03] rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-slate-400 text-sm">Total P&L</span>
                    <span className={`flex items-center gap-1 text-sm ${isProfit ? 'text-emerald-400/80' : 'text-rose-400/80'}`}>
                      {isProfit ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      {isProfit ? '+' : ''}{((totalProfit / 10000) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className={`text-3xl font-bold mb-2 ${isProfit ? 'text-emerald-400/90' : 'text-rose-400/90'}`}>
                    {formatCurrency(totalProfit)}
                  </div>
                  <div className="text-slate-500 text-sm">
                    Goal: $10,000 • Average: {formatCurrency(analytics?.expectancy || 0)}/trade
                  </div>
                  {/* Mini Chart */}
                  <div className="h-20 mt-4 flex items-end gap-1">
                    {[40, 65, 45, 80, 55, 70, 90, 60, 75, 85].map((h, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-gradient-to-t from-cyan-500/30 to-cyan-400/10 rounded-t"
                        style={{ height: `${h}%` }}
                      />
                    ))}
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="bg-white/[0.03] rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-slate-400 text-sm">Win/Loss Stats</span>
                    <span className="text-slate-500 text-sm">Breakdown</span>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Total Trades</span>
                      <span className="text-white font-semibold text-lg">{analytics?.total_trades || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Avg Win</span>
                      <span className="text-emerald-400/80 font-medium">{formatCurrency(analytics?.average_win)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Avg Loss</span>
                      <span className="text-rose-400/80 font-medium">{formatCurrency(analytics?.average_loss)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Profit Factor</span>
                      <span className="text-cyan-400/80 font-medium">{analytics?.profit_factor?.toFixed(2) || '0.00'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Trades */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-slate-200 font-medium">Recent Trades</h3>
                <button 
                  onClick={() => router.push('/trades')}
                  className="text-cyan-400/80 hover:text-cyan-300 text-sm flex items-center gap-1"
                >
                  View All <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {trades.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                  <h4 className="text-slate-200 font-medium mb-2">No trades yet</h4>
                  <p className="text-slate-500 mb-4">Start tracking your trading journey</p>
                  <button
                    onClick={() => router.push('/trades/new')}
                    className="bg-gradient-to-r from-cyan-500/80 to-blue-500/80 hover:from-cyan-500 hover:to-blue-500 text-white font-medium px-6 py-2 rounded-full transition-all"
                  >
                    Add First Trade
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {trades.slice(0, 5).map((trade) => (
                    <div
                      key={trade.id}
                      onClick={() => router.push(`/trades/${trade.id}`)}
                      className="flex items-center justify-between p-4 bg-white/[0.03] hover:bg-white/[0.06] rounded-xl cursor-pointer transition-all group"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          trade.trade_type === 'buy' ? 'bg-emerald-500/15' : 'bg-rose-500/15'
                        }`}>
                          {trade.trade_type === 'buy' ? (
                            <TrendingUp className="w-5 h-5 text-emerald-400/80" />
                          ) : (
                            <TrendingDown className="w-5 h-5 text-rose-400/80" />
                          )}
                        </div>
                        <div>
                          <div className="text-slate-200 font-medium">{trade.symbol}</div>
                          <div className="text-slate-500 text-sm">
                            {trade.trade_type.toUpperCase()} • {trade.volume} lots
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-medium ${
                          (trade.net_profit || 0) >= 0 ? 'text-emerald-400/80' : 'text-rose-400/80'
                        }`}>
                          {formatCurrency(trade.net_profit)}
                        </div>
                        <div className="text-slate-600 text-sm">
                          {new Date(trade.open_time).toLocaleDateString()}
                        </div>
                      </div>
                      <Eye className="w-5 h-5 text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div className="col-span-12 lg:col-span-4 space-y-6">
            {/* Win Rate Card */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-slate-200 font-medium">Win Rate</h3>
                  <p className="text-slate-500 text-sm">Keep improving!</p>
                </div>
                <Target className="w-5 h-5 text-cyan-400/70" />
              </div>
              <div className="flex items-center justify-center py-4">
                <WinRateRing percentage={winRate} />
              </div>
              <div className="text-center text-slate-500 text-sm">
                Goal is 55% • {winRate >= 55 ? '🎯 Target reached!' : `${(55 - winRate).toFixed(1)}% to go`}
              </div>
            </div>

            {/* Calendar */}
            <MiniCalendar tradingDays={tradingDays} />

            {/* Quick Actions */}
            <div className="glass-card p-5">
              <h3 className="text-slate-200 font-medium mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => router.push('/trades/new')}
                  className="flex flex-col items-center gap-2 p-4 bg-cyan-500/10 hover:bg-cyan-500/15 rounded-xl transition-all group"
                >
                  <Plus className="w-5 h-5 text-cyan-400/80" />
                  <span className="text-slate-300 text-sm">New Trade</span>
                </button>
                <button
                  onClick={() => router.push('/journal/new')}
                  className="flex flex-col items-center gap-2 p-4 bg-violet-500/10 hover:bg-violet-500/15 rounded-xl transition-all group"
                >
                  <Zap className="w-5 h-5 text-violet-400/80" />
                  <span className="text-slate-300 text-sm">Journal</span>
                </button>
                <button
                  onClick={() => router.push('/analytics')}
                  className="flex flex-col items-center gap-2 p-4 bg-blue-500/10 hover:bg-blue-500/15 rounded-xl transition-all group"
                >
                  <BarChart3 className="w-5 h-5 text-blue-400/80" />
                  <span className="text-slate-300 text-sm">Analytics</span>
                </button>
                <button
                  onClick={() => router.push('/calendar')}
                  className="flex flex-col items-center gap-2 p-4 bg-emerald-500/10 hover:bg-emerald-500/15 rounded-xl transition-all group"
                >
                  <Calendar className="w-5 h-5 text-emerald-400/80" />
                  <span className="text-slate-300 text-sm">Calendar</span>
                </button>
              </div>
            </div>

            {/* Performance Tip */}
            <div className="glass-card p-5 border-l-2 border-cyan-500/50">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-cyan-500/15 rounded-full flex items-center justify-center flex-shrink-0">
                  <Zap className="w-4 h-4 text-cyan-400/80" />
                </div>
                <div>
                  <h4 className="text-slate-200 font-medium mb-1">Trading Tip</h4>
                  <p className="text-slate-500 text-sm">
                    {analytics?.profit_factor && analytics.profit_factor < 1.5
                      ? "Focus on your risk management. Consider reducing position sizes on losing streaks."
                      : winRate < 50
                      ? "Review your entry criteria. Quality setups lead to better win rates."
                      : "Great job! Keep journaling your trades to maintain consistency."
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 1rem;
        }
      `}</style>
    </Layout>
  );
}
