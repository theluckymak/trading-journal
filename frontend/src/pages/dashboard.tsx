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
  Brain,
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

const WinRateRing = ({ percentage }: { percentage: number }) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-28 h-28">
      <svg className="w-28 h-28 transform -rotate-90">
        <circle cx="56" cy="56" r={radius} stroke="var(--border)" strokeWidth="8" fill="none" />
        <circle
          cx="56" cy="56" r={radius} stroke="var(--brand)" strokeWidth="8" fill="none"
          strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold" style={{ color: 'var(--text)' }}>{percentage.toFixed(1)}%</span>
      </div>
    </div>
  );
};

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
    return tradingDays.some(d => d.getDate() === day && d.getMonth() === currentMonth && d.getFullYear() === currentYear);
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium" style={{ color: 'var(--text)' }}>Trading Activity</h3>
        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{monthName}</span>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center">
        {days.map(day => (
          <div key={day} className="text-xs py-1" style={{ color: 'var(--text-muted)' }}>{day}</div>
        ))}
        {Array.from({ length: adjustedFirstDay }).map((_, i) => <div key={`e-${i}`} className="py-1" />)}
        {Array.from({ length: daysInMonth }).map((_, i) => {
          const day = i + 1;
          const isToday = day === today.getDate();
          const hasTraded = isTradingDay(day);
          return (
            <div
              key={day}
              className="py-1 text-sm rounded-full transition-all"
              style={{
                background: isToday ? 'var(--brand)' : hasTraded ? 'var(--brand-light)' : 'transparent',
                color: isToday ? '#fff' : hasTraded ? 'var(--brand)' : 'var(--text-muted)',
                fontWeight: isToday ? 700 : 400,
              }}
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
    if (!user) { router.push('/login'); return; }
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
      setTradingDays(tradesRes.map((t: Trade) => new Date(t.open_time)));
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
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
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-3 rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--brand)' }} />
            <p className="mt-4 text-sm" style={{ color: 'var(--text-muted)' }}>Loading dashboard...</p>
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
      <div className="min-h-screen p-6 lg:p-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold mb-1" style={{ color: 'var(--text)' }}>
              {getGreeting()}, <span style={{ color: 'var(--brand)' }}>{userName}</span>
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Ready for today's market challenges</p>
          </div>
          <div className="flex items-center gap-3 mt-4 lg:mt-0">
            <input
              type="text"
              placeholder="Search trades..."
              className="input w-60 text-sm"
              style={{ borderRadius: '19px' }}
            />
            <button onClick={() => router.push('/trades/new')} className="btn btn-brand flex items-center gap-2">
              <Plus className="w-4 h-4" /> New Trade
            </button>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          {/* Left */}
          <div className="col-span-12 lg:col-span-8 space-y-5">
            {/* P&L Card */}
            <div className="card">
              <div className="flex items-center justify-between mb-5">
                <h3 className="font-medium" style={{ color: 'var(--text)' }}>Trading Performance</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-2xl" style={{ background: 'var(--bg-section)' }}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Total P&L</span>
                    <span className="flex items-center gap-1 text-sm" style={{ color: isProfit ? 'var(--success)' : 'var(--error)' }}>
                      {isProfit ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                      {isProfit ? '+' : ''}{((totalProfit / 10000) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-3xl font-bold mb-2" style={{ color: isProfit ? 'var(--success)' : 'var(--error)' }}>
                    {formatCurrency(totalProfit)}
                  </div>
                  <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Avg: {formatCurrency(analytics?.expectancy || 0)}/trade
                  </div>
                  <div className="h-16 mt-4 flex items-end gap-1">
                    {[40, 65, 45, 80, 55, 70, 90, 60, 75, 85].map((h, i) => (
                      <div key={i} className="flex-1 rounded-t" style={{ height: `${h}%`, background: 'var(--brand-light)' }}>
                        <div className="w-full rounded-t" style={{ height: '60%', background: 'var(--brand)', opacity: 0.4, marginTop: '40%' }} />
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-5 rounded-2xl" style={{ background: 'var(--bg-section)' }}>
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Win/Loss Stats</span>
                  <div className="space-y-4 mt-4">
                    {[
                      { label: 'Total Trades', value: String(analytics?.total_trades || 0), color: 'var(--text)' },
                      { label: 'Avg Win', value: formatCurrency(analytics?.average_win), color: 'var(--success)' },
                      { label: 'Avg Loss', value: formatCurrency(analytics?.average_loss), color: 'var(--error)' },
                      { label: 'Profit Factor', value: analytics?.profit_factor?.toFixed(2) || '0.00', color: 'var(--brand)' },
                    ].map((s) => (
                      <div key={s.label} className="flex justify-between items-center">
                        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{s.label}</span>
                        <span className="font-semibold" style={{ color: s.color }}>{s.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Trades */}
            <div className="card">
              <div className="flex items-center justify-between mb-5">
                <h3 className="font-medium" style={{ color: 'var(--text)' }}>Recent Trades</h3>
                <button onClick={() => router.push('/trades')} className="text-sm flex items-center gap-1" style={{ color: 'var(--brand)' }}>
                  View All <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              {trades.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
                  <h4 className="font-medium mb-2" style={{ color: 'var(--text)' }}>No trades yet</h4>
                  <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>Start tracking your trading journey</p>
                  <button onClick={() => router.push('/trades/new')} className="btn btn-brand">Add First Trade</button>
                </div>
              ) : (
                <div className="space-y-2">
                  {trades.slice(0, 5).map((trade) => (
                    <div
                      key={trade.id}
                      onClick={() => router.push(`/trades/${trade.id}`)}
                      className="flex items-center justify-between p-4 rounded-2xl cursor-pointer transition-all group"
                      style={{ background: 'var(--bg-section)' }}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full flex items-center justify-center"
                          style={{ background: trade.trade_type === 'buy' ? 'rgba(41,204,106,0.1)' : 'rgba(255,45,85,0.1)' }}>
                          {trade.trade_type === 'buy'
                            ? <TrendingUp className="w-5 h-5" style={{ color: 'var(--success)' }} />
                            : <TrendingDown className="w-5 h-5" style={{ color: 'var(--error)' }} />
                          }
                        </div>
                        <div>
                          <div className="font-medium" style={{ color: 'var(--text)' }}>{trade.symbol}</div>
                          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            {trade.trade_type.toUpperCase()} · {trade.volume} lots
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium" style={{ color: (trade.net_profit || 0) >= 0 ? 'var(--success)' : 'var(--error)' }}>
                          {formatCurrency(trade.net_profit)}
                        </div>
                        <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
                          {new Date(trade.open_time).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right */}
          <div className="col-span-12 lg:col-span-4 space-y-5">
            {/* Win Rate */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-medium" style={{ color: 'var(--text)' }}>Win Rate</h3>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Keep improving!</p>
                </div>
                <Target className="w-5 h-5" style={{ color: 'var(--brand)' }} />
              </div>
              <div className="flex items-center justify-center py-4">
                <WinRateRing percentage={winRate} />
              </div>
              <div className="text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                Goal is 55% · {winRate >= 55 ? 'Target reached!' : `${(55 - winRate).toFixed(1)}% to go`}
              </div>
            </div>

            <MiniCalendar tradingDays={tradingDays} />

            {/* Quick Actions */}
            <div className="card">
              <h3 className="font-medium mb-4" style={{ color: 'var(--text)' }}>Quick Actions</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'New Trade', icon: Plus, href: '/trades/new' },
                  { label: 'Journal', icon: Zap, href: '/journal/new' },
                  { label: 'Analytics', icon: BarChart3, href: '/analytics' },
                  { label: 'Calendar', icon: Calendar, href: '/calendar' },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.label}
                      onClick={() => router.push(item.href)}
                      className="flex flex-col items-center gap-2 p-4 rounded-2xl transition-all"
                      style={{ background: 'var(--brand-light)' }}
                    >
                      <Icon className="w-5 h-5" style={{ color: 'var(--brand)' }} />
                      <span className="text-sm" style={{ color: 'var(--text)' }}>{item.label}</span>
                    </button>
                  );
                })}
                <button
                  onClick={() => router.push('/prediction')}
                  className="flex flex-col items-center gap-2 p-4 rounded-2xl transition-all col-span-2"
                  style={{ background: 'var(--brand-light)' }}
                >
                  <Brain className="w-5 h-5" style={{ color: 'var(--brand)' }} />
                  <span className="text-sm" style={{ color: 'var(--text)' }}>AI Prediction</span>
                </button>
              </div>
            </div>

            {/* Tip */}
            <div className="card" style={{ borderLeft: '3px solid var(--brand)' }}>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--brand-light)' }}>
                  <Zap className="w-4 h-4" style={{ color: 'var(--brand)' }} />
                </div>
                <div>
                  <h4 className="font-medium mb-1" style={{ color: 'var(--text)' }}>Trading Tip</h4>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    {analytics?.profit_factor && analytics.profit_factor < 1.5
                      ? "Focus on risk management. Consider reducing position sizes on losing streaks."
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
    </Layout>
  );
}
