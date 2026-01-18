import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

interface Trade {
  id: number;
  symbol: string;
  trade_type: string;
  open_time: string;
  close_time: string | null;
  net_profit: number | null;
  profit: number | null;
  is_closed: boolean;
}

interface DayData {
  date: Date;
  profit: number;
  trades: number;
  rr: number;
  winRate: number;
  wins: number;
  losses: number;
}

interface WeekData {
  weekNum: number;
  profit: number;
  daysTraded: number;
  winRate: number;
  totalTrades: number;
}

export default function CalendarPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadTrades();
  }, [user]);

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

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const getTradesForDate = (date: Date) => {
    return trades.filter((trade) => {
      const tradeDate = new Date(trade.close_time || trade.open_time);
      return (
        tradeDate.getDate() === date.getDate() &&
        tradeDate.getMonth() === date.getMonth() &&
        tradeDate.getFullYear() === date.getFullYear()
      );
    });
  };

  const getDayData = (date: Date): DayData | null => {
    const dayTrades = getTradesForDate(date);
    if (dayTrades.length === 0) return null;

    const profit = dayTrades.reduce((sum, t) => sum + (t.net_profit || 0), 0);
    const wins = dayTrades.filter(t => (t.net_profit || 0) > 0);
    const losses = dayTrades.filter(t => (t.net_profit || 0) < 0);
    
    // Calculate R:R (simplified as profit/risk ratio)
    const avgProfit = profit / dayTrades.length;
    const rr = avgProfit / 100; // Simplified R value
    const winRate = dayTrades.length > 0 ? (wins.length / dayTrades.length) * 100 : 0;

    return {
      date,
      profit,
      trades: dayTrades.length,
      rr,
      winRate,
      wins: wins.length,
      losses: losses.length,
    };
  };

  const getWeekData = (weekStart: Date): WeekData => {
    let weekProfit = 0;
    let daysTraded = 0;
    let totalWins = 0;
    let totalTrades = 0;

    for (let i = 0; i < 7; i++) {
      const day = new Date(weekStart);
      day.setDate(weekStart.getDate() + i);
      
      if (day.getMonth() === currentDate.getMonth()) {
        const dayData = getDayData(day);
        if (dayData) {
          weekProfit += dayData.profit;
          daysTraded++;
          totalWins += dayData.wins;
          totalTrades += dayData.trades;
        }
      }
    }

    const winRate = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;

    return {
      weekNum: Math.ceil((weekStart.getDate() + getDaysInMonth(currentDate).startingDayOfWeek) / 7),
      profit: weekProfit,
      daysTraded,
      winRate,
      totalTrades
    };
  };

  const previousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
  };

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentDate);
  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  // Create weeks array with days and calculate weekly stats
  const weeks: Array<{ days: (number | null)[]; weekData: WeekData }> = [];
  let currentWeek: (number | null)[] = [];
  let weekNum = 1;

  // Add empty cells for days before month starts
  for (let i = 0; i < startingDayOfWeek; i++) {
    currentWeek.push(null);
  }

  // Add actual days
  for (let day = 1; day <= daysInMonth; day++) {
    currentWeek.push(day);
    
    // When we hit Saturday (index 6) or last day of month
    if (currentWeek.length === 7 || day === daysInMonth) {
      // Fill remaining days with null if needed
      while (currentWeek.length < 7) {
        currentWeek.push(null);
      }
      
      // Calculate week start date (first actual day in the week)
      const firstDay = currentWeek.find(d => d !== null);
      const weekStartDate = firstDay ? new Date(year, month, firstDay) : new Date(year, month, 1);
      
      weeks.push({
        days: [...currentWeek],
        weekData: getWeekData(weekStartDate)
      });
      
      currentWeek = [];
      weekNum++;
    }
  }

  // Calculate monthly statistics
  const monthlyStats = (() => {
    const monthTrades = trades.filter(trade => {
      const tradeDate = new Date(trade.close_time || trade.open_time);
      return tradeDate.getMonth() === currentDate.getMonth() && 
             tradeDate.getFullYear() === currentDate.getFullYear();
    });
    
    const totalProfit = monthTrades.reduce((sum, t) => sum + (t.net_profit || 0), 0);
    const wins = monthTrades.filter(t => (t.net_profit || 0) > 0);
    const losses = monthTrades.filter(t => (t.net_profit || 0) < 0);
    const winRate = monthTrades.length > 0 ? (wins.length / monthTrades.length) * 100 : 0;
    
    const totalWinProfit = wins.reduce((sum, t) => sum + (t.net_profit || 0), 0);
    const totalLossProfit = Math.abs(losses.reduce((sum, t) => sum + (t.net_profit || 0), 0));
    const profitFactor = totalLossProfit > 0 ? totalWinProfit / totalLossProfit : totalWinProfit > 0 ? 999 : 0;
    
    const avgWin = wins.length > 0 ? totalWinProfit / wins.length : 0;
    const avgLoss = losses.length > 0 ? totalLossProfit / losses.length : 0;
    const expectancy = monthTrades.length > 0 ? totalProfit / monthTrades.length : 0;
    
    return {
      totalProfit,
      totalTrades: monthTrades.length,
      winRate,
      profitFactor,
      expectancy,
      avgWin,
      avgLoss,
      wins: wins.length,
      losses: losses.length
    };
  })();

  const selectedDateTrades = selectedDate ? getTradesForDate(selectedDate) : [];
  const selectedDayData = selectedDate ? getDayData(selectedDate) : null;

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <CalendarIcon className="h-12 w-12 text-blue-600 mx-auto animate-pulse" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading calendar...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Trading Calendar</h1>
          <p className="text-gray-600 dark:text-gray-400">View your trading activity over time</p>
        </div>

        {/* Monthly Performance Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">P&L</div>
            <div className={`text-lg font-bold ${monthlyStats.totalProfit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              ${monthlyStats.totalProfit.toFixed(0)}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Trades</div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">{monthlyStats.totalTrades}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Win Rate</div>
            <div className={`text-lg font-bold ${monthlyStats.winRate >= 50 ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}`}>
              {monthlyStats.winRate.toFixed(1)}%
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Profit Factor</div>
            <div className="text-lg font-bold text-purple-600 dark:text-purple-400">{monthlyStats.profitFactor.toFixed(2)}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Expectancy</div>
            <div className={`text-lg font-bold ${monthlyStats.expectancy >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              ${monthlyStats.expectancy.toFixed(0)}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Win</div>
            <div className="text-lg font-bold text-green-600 dark:text-green-400">${monthlyStats.avgWin.toFixed(0)}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Loss</div>
            <div className="text-lg font-bold text-red-600 dark:text-red-400">${monthlyStats.avgLoss.toFixed(0)}</div>
          </div>
        </div>

        {/* Calendar and Details */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Calendar */}
          <div className="lg:col-span-3 bg-white dark:bg-gray-800 rounded-lg shadow p-4 md:p-6 overflow-x-auto">
            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={previousMonth}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                <ChevronLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{monthName}</h2>
              <button
                onClick={nextMonth}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                <ChevronRight className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            {/* Calendar Grid with Weekly Stats */}
            <div className="min-w-[700px]">
              {/* Day Headers */}
              <div className="grid grid-cols-8 gap-2 mb-2">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                  <div
                    key={day}
                    className="text-center text-sm font-semibold text-gray-600 dark:text-gray-400 py-2"
                  >
                    {day}
                  </div>
                ))}
                <div className="text-center text-sm font-semibold text-gray-600 dark:text-gray-400 py-2">
                  Weekly
                </div>
              </div>

              {/* Weeks */}
              {weeks.map((week, weekIdx) => (
                <div key={weekIdx} className="grid grid-cols-8 gap-2 mb-2">
                  {/* Days of the week */}
                  {week.days.map((day, dayIdx) => {
                    if (day === null) {
                      return <div key={`empty-${dayIdx}`} className="aspect-square" />;
                    }

                    const date = new Date(year, month, day);
                    const dayData = getDayData(date);
                    const hasActivity = dayData !== null;
                    const isToday =
                      date.getDate() === new Date().getDate() &&
                      date.getMonth() === new Date().getMonth() &&
                      date.getFullYear() === new Date().getFullYear();

                    return (
                      <button
                        key={day}
                        onClick={() => hasActivity && setSelectedDate(date)}
                        disabled={!dayData}
                        className={`relative aspect-square p-2 rounded-lg border-2 transition overflow-hidden ${
                          hasActivity
                            ? dayData.profit >= 0
                              ? 'border-green-600 dark:border-green-500 bg-green-600/10 dark:bg-green-900/30 hover:bg-green-600/20 dark:hover:bg-green-900/40 cursor-pointer'
                              : 'border-red-600 dark:border-red-500 bg-red-600/10 dark:bg-red-900/30 hover:bg-red-600/20 dark:hover:bg-red-900/40 cursor-pointer'
                            : 'border-gray-300 dark:border-gray-700 bg-gray-800/20 cursor-default'
                        } ${isToday ? 'ring-2 ring-blue-500' : ''}`}
                      >
                        <div className="absolute top-1 left-1.5 text-[8px] xs:text-[9px] sm:text-[10px] md:text-xs font-medium text-gray-400 dark:text-gray-500">
                          {day}
                        </div>
                        {dayData && (
                          <>
                            <div className="absolute inset-x-0 top-[30%] flex items-center justify-center">
                              <div
                                className={`text-xs xs:text-sm sm:text-base md:text-lg lg:text-xl xl:text-2xl font-semibold leading-none ${
                                  dayData.profit >= 0
                                    ? 'text-green-600 dark:text-green-400'
                                    : 'text-red-600 dark:text-red-400'
                                }`}
                              >
                                {dayData.profit >= 0 ? '$' : '-$'}{Math.abs(dayData.profit).toFixed(0)}
                              </div>
                            </div>
                            <div className="absolute bottom-0.5 left-1 right-1 flex flex-col space-y-0">
                              <div className="text-[7px] xs:text-[8px] sm:text-[9px] md:text-[10px] lg:text-xs text-gray-700 dark:text-gray-300 truncate">
                                {dayData.trades} {dayData.trades === 1 ? 'trade' : 'trades'}
                              </div>
                              <div className="text-[7px] xs:text-[8px] sm:text-[9px] md:text-[10px] lg:text-xs text-blue-600 dark:text-blue-400">
                                {dayData.rr >= 0 ? '+' : ''}{dayData.rr.toFixed(1)}R
                              </div>
                            </div>
                          </>
                        )}
                      </button>
                    );
                  })}

                  {/* Weekly Summary */}
                  <div className="aspect-square bg-gray-700 dark:bg-gray-900 rounded-lg p-2 border-2 border-gray-600 dark:border-gray-700 overflow-hidden">
                    <div className="flex flex-col items-center justify-center h-full space-y-1">
                      <div className="text-[8px] xs:text-[9px] sm:text-[10px] md:text-xs text-gray-400 mb-1">Week {week.weekData.weekNum}</div>
                      <div
                        className={`text-xs xs:text-sm sm:text-base md:text-lg lg:text-xl xl:text-2xl font-semibold leading-none ${
                          week.weekData.profit >= 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }`}
                      >
                        {week.weekData.profit >= 0 ? '$' : '-$'}
                        {Math.abs(week.weekData.profit).toFixed(0)}
                      </div>
                      <div className="text-[7px] xs:text-[8px] sm:text-[9px] md:text-[10px] lg:text-xs text-blue-400 mt-1">
                        {week.weekData.daysTraded} day{week.weekData.daysTraded !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Selected Date Details - Sidebar */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {selectedDate
                ? selectedDate.toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                  })
                : 'Select a date'}
            </h3>

            {selectedDate && selectedDateTrades.length > 0 ? (
              <div className="space-y-4">
                {/* Summary */}
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Profit</div>
                  <div
                    className={`text-2xl font-bold ${
                      selectedDayData && selectedDayData.profit >= 0
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(selectedDayData?.profit || 0)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    {selectedDateTrades.length} trade{selectedDateTrades.length !== 1 ? 's' : ''}
                  </div>
                </div>

                {/* Trade List */}
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {selectedDateTrades.map((trade) => (
                    <button
                      key={trade.id}
                      onClick={() => router.push(`/trades/${trade.id}`)}
                      className="w-full text-left p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {trade.symbol}
                        </span>
                        <span
                          className={`flex items-center gap-1 text-sm ${
                            trade.trade_type.toLowerCase() === 'buy'
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}
                        >
                          {trade.trade_type.toLowerCase() === 'buy' ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                          {trade.trade_type}
                        </span>
                      </div>
                      <div
                        className={`text-sm font-medium ${
                          (trade.net_profit || 0) >= 0
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        }`}
                      >
                        {new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: 'USD',
                        }).format(trade.net_profit || 0)}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : selectedDate ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No trades on this date
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                Click on a date to view trades
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
