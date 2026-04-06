import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Calendar,
  Zap,
  Target,
  Activity,
  Clock,
  Search,
  Loader,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
  ArrowRight,
  ExternalLink,
  BarChart3,
  Gauge,
  Newspaper,
} from 'lucide-react';

/* ── Types ── */
interface ModelVote { name: string; vote: number; label: string; }
interface OutlookData { direction: string; strength: number; factors: string[]; }
interface PredictionData {
  signal: number;
  signal_label: string;
  confidence: number;
  votes: ModelVote[];
  regime: { state: number; label: string };
  entry_score: number;
  entry_reasons: string[];
  outlook: OutlookData;
  risk: { atr: number; stop_loss: number; take_profit: number };
  indicators: Record<string, number>;
  price_change: number;
  price_change_pct: number;
  volatility_level: string;
  events: { next_event: string | null; hours_until: number | null; shock_active: boolean };
  timestamp: string;
  symbol?: string;
  price?: number;
}
interface NewsItem {
  title: string;
  publisher: string;
  time: string;
  link: string;
  sentiment: 'positive' | 'negative' | 'neutral';
}

const INSTRUMENT_GROUPS = [
  { id: 'futures', label: 'Futures', symbols: ['NQ', 'ES', 'YM', 'CL', 'GC'] },
  { id: 'forex', label: 'Forex', symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'] },
  { id: 'crypto', label: 'Crypto', symbols: ['BTC', 'ETH', 'SOL'] },
  { id: 'stocks', label: 'Stocks', symbols: ['AAPL', 'TSLA', 'NVDA', 'MSFT'] },
];

/* ── 5-Day Outlook Card ── */
function OutlookCard({ prediction, loading }: { prediction: PredictionData | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="card flex items-center justify-center py-10">
        <Loader className="w-6 h-6 animate-spin" style={{ color: 'var(--brand)' }} />
      </div>
    );
  }
  if (!prediction?.outlook) return null;

  const { direction, strength, factors } = prediction.outlook;
  const color = direction === 'Bullish' ? 'var(--success)' : direction === 'Bearish' ? 'var(--error)' : 'var(--text-muted)';
  const bg = direction === 'Bullish' ? 'rgba(41,204,106,0.08)' : direction === 'Bearish' ? 'rgba(255,45,85,0.08)' : 'var(--bg-section)';
  const Icon = direction === 'Bullish' ? ArrowUpRight : direction === 'Bearish' ? ArrowDownRight : ArrowRight;

  return (
    <div className="card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>5-Day Outlook</span>
        </div>
        {prediction.symbol && (
          <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{prediction.symbol}</span>
        )}
      </div>

      <div className="flex items-center gap-5 mb-4">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: bg }}>
          <Icon className="w-8 h-8" style={{ color }} />
        </div>
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold" style={{ color }}>{direction}</span>
            <span className="text-lg font-semibold" style={{ color }}>{strength}%</span>
          </div>
          {prediction.price != null && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                ${prediction.price.toLocaleString()}
              </span>
              <span className="text-xs font-semibold" style={{ color: prediction.price_change >= 0 ? 'var(--success)' : 'var(--error)' }}>
                {prediction.price_change >= 0 ? '+' : ''}{prediction.price_change_pct}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Strength bar */}
      <div className="mb-4">
        <div className="w-full h-1.5 rounded-full flex" style={{ background: 'var(--border)' }}>
          <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${strength}%`, background: color }} />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-[10px]" style={{ color: 'var(--error)' }}>Bearish</span>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Neutral</span>
          <span className="text-[10px]" style={{ color: 'var(--success)' }}>Bullish</span>
        </div>
      </div>

      {factors.length > 0 && (
        <div className="space-y-1.5">
          {factors.map((f, i) => (
            <div key={i} className="flex items-start gap-2 text-xs" style={{ color: 'var(--text)' }}>
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: color }} />
              {f}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Entry Signal Card ── */
function SignalCard({ prediction, loading }: { prediction: PredictionData | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="card flex items-center justify-center py-12">
        <div className="text-center">
          <Loader className="w-7 h-7 mx-auto mb-2 animate-spin" style={{ color: 'var(--brand)' }} />
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Analyzing market data...</p>
        </div>
      </div>
    );
  }
  if (!prediction) {
    return (
      <div className="card flex items-center justify-center py-12">
        <div className="text-center">
          <Brain className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--text-muted)' }} />
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Select a symbol to analyze</p>
        </div>
      </div>
    );
  }

  const isFlat = prediction.signal === 0;
  const signalColor = prediction.signal === 1 ? 'var(--success)' : prediction.signal === -1 ? 'var(--error)' : 'var(--text-muted)';
  const signalBg = prediction.signal === 1 ? 'rgba(41,204,106,0.08)' : prediction.signal === -1 ? 'rgba(255,45,85,0.08)' : 'var(--bg-section)';
  const SignalIcon = prediction.signal === 1 ? TrendingUp : prediction.signal === -1 ? TrendingDown : Minus;
  const confidencePct = Math.round(prediction.confidence * 100);
  const circumference = 2 * Math.PI * 36;
  const strokeDashoffset = circumference * (1 - prediction.confidence);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Entry Signal</span>
        </div>
        <div className="px-2.5 py-1 rounded-full text-[10px] font-semibold" style={{ background: signalBg, color: signalColor }}>
          {prediction.regime.label}
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="relative flex-shrink-0">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="36" fill="none" stroke="var(--border)" strokeWidth="5" />
            <circle
              cx="40" cy="40" r="36" fill="none"
              stroke={signalColor} strokeWidth="5" strokeLinecap="round"
              strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
              transform="rotate(-90 40 40)"
              style={{ transition: 'stroke-dashoffset 0.8s ease' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <SignalIcon className="w-4 h-4 mb-0.5" style={{ color: signalColor }} />
            <span className="text-sm font-bold" style={{ color: signalColor }}>{confidencePct}%</span>
          </div>
        </div>

        <div className="flex-1">
          <h2 className="text-xl font-bold mb-1" style={{ color: signalColor }}>
            {isFlat ? 'No Clear Entry' : prediction.signal_label}
          </h2>
          {isFlat ? (
            <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
              Models disagree — wait for alignment
            </p>
          ) : (
            <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
              {prediction.votes.filter(v => v.vote === prediction.signal).length}/3 models agree
            </p>
          )}
          <div className="flex gap-1.5 flex-wrap">
            {prediction.votes.map((v) => (
              <div
                key={v.name}
                className="flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-semibold"
                style={{
                  background: v.vote === 1 ? 'rgba(41,204,106,0.08)' : v.vote === -1 ? 'rgba(255,45,85,0.08)' : 'var(--bg-section)',
                  color: v.vote === 1 ? 'var(--success)' : v.vote === -1 ? 'var(--error)' : 'var(--text-muted)',
                }}
              >
                {v.vote === 1 ? <TrendingUp className="w-2.5 h-2.5" /> : v.vote === -1 ? <TrendingDown className="w-2.5 h-2.5" /> : <Minus className="w-2.5 h-2.5" />}
                {v.name}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Entry Score */}
      <div className="mt-4 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Entry Score</span>
          <span className="text-xs font-bold" style={{ color: prediction.entry_score >= 4 ? 'var(--success)' : 'var(--text-muted)' }}>
            {prediction.entry_score}/9 {prediction.entry_score >= 6 ? 'Strong' : prediction.entry_score >= 4 ? 'Ready' : 'Wait'}
          </span>
        </div>
        <div className="w-full h-1.5 rounded-full" style={{ background: 'var(--border)' }}>
          <div
            className="h-1.5 rounded-full transition-all duration-500"
            style={{
              width: `${Math.min((prediction.entry_score / 9) * 100, 100)}%`,
              background: prediction.entry_score >= 6 ? 'var(--success)' : prediction.entry_score >= 4 ? 'var(--brand)' : 'var(--text-muted)',
            }}
          />
        </div>
      </div>
    </div>
  );
}

/* ── Risk & Context Panel ── */
function RiskPanel({ prediction }: { prediction: PredictionData | null }) {
  if (!prediction) return null;

  const volColor = prediction.volatility_level === 'High' ? 'var(--error)' : prediction.volatility_level === 'Low' ? 'var(--success)' : 'var(--text-muted)';
  const items = [
    {
      label: 'Regime',
      value: prediction.regime.label,
      color: prediction.regime.state === 0 ? 'var(--success)' : prediction.regime.state === 1 ? 'var(--error)' : 'var(--text-muted)',
      icon: Activity,
    },
    {
      label: 'Volatility',
      value: prediction.volatility_level,
      color: volColor,
      icon: Gauge,
    },
    {
      label: 'Events',
      value: prediction.events.next_event ? `${prediction.events.next_event}` : 'Clear',
      color: prediction.events.next_event ? 'var(--warning)' : 'var(--success)',
      icon: Calendar,
    },
    {
      label: 'Shocks',
      value: prediction.events.shock_active ? 'Active' : 'None',
      color: prediction.events.shock_active ? 'var(--error)' : 'var(--success)',
      icon: Zap,
    },
  ];

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-3">
        <Shield className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Risk Context</span>
      </div>
      <div className="space-y-2.5">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Icon className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.label}</span>
              </div>
              <span className="text-xs font-semibold" style={{ color: item.color }}>{item.value}</span>
            </div>
          );
        })}
      </div>

      {/* Risk levels */}
      <div className="mt-3 pt-3 grid grid-cols-3 gap-2" style={{ borderTop: '1px solid var(--border)' }}>
        {[
          { label: 'SL', value: prediction.risk.stop_loss.toFixed(0), color: 'var(--error)' },
          { label: 'TP', value: prediction.risk.take_profit.toFixed(0), color: 'var(--success)' },
          { label: 'ATR', value: prediction.risk.atr.toFixed(0), color: 'var(--brand)' },
        ].map((r) => (
          <div key={r.label} className="text-center py-2 rounded-xl" style={{ background: 'var(--bg-section)' }}>
            <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{r.label}</p>
            <p className="text-xs font-bold" style={{ color: r.color }}>{r.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── News Feed ── */
function NewsFeed({ symbol }: { symbol: string }) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true);
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        const res = await fetch(`/api/ai/news/${encodeURIComponent(symbol)}`, { signal: controller.signal });
        clearTimeout(timeout);
        if (res.ok) {
          const data = await res.json();
          setNews(data || []);
        }
      } catch {
        setNews([]);
      } finally {
        setLoading(false);
      }
    };
    fetchNews();
  }, [symbol]);

  const sentimentColor = (s: string) => s === 'positive' ? 'var(--success)' : s === 'negative' ? 'var(--error)' : 'var(--text-muted)';
  const sentimentBg = (s: string) => s === 'positive' ? 'rgba(41,204,106,0.08)' : s === 'negative' ? 'rgba(255,45,85,0.08)' : 'var(--bg-section)';

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Latest News</span>
        </div>
        <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{symbol}</span>
      </div>

      {loading ? (
        <div className="py-8 text-center">
          <Loader className="w-5 h-5 mx-auto animate-spin" style={{ color: 'var(--text-muted)' }} />
        </div>
      ) : news.length === 0 ? (
        <div className="py-8 text-center text-xs" style={{ color: 'var(--text-muted)' }}>No recent news</div>
      ) : (
        <div className="space-y-2">
          {news.slice(0, 6).map((item, i) => (
            <a
              key={i}
              href={item.link}
              target="_blank"
              rel="noopener noreferrer"
              className="block py-2 px-3 rounded-xl transition-all hover:opacity-80"
              style={{ background: 'var(--bg-section)' }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium leading-snug line-clamp-2" style={{ color: 'var(--text)' }}>
                    {item.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{item.publisher}</span>
                    {item.time && <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{item.time}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ background: sentimentColor(item.sentiment) }}
                  />
                  <ExternalLink className="w-3 h-3" style={{ color: 'var(--text-muted)' }} />
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Detail Panel (Expandable) ── */
function DetailPanel({ prediction }: { prediction: PredictionData | null }) {
  const [open, setOpen] = useState(false);
  if (!prediction) return null;

  return (
    <div className="card">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Technical Details</span>
        {open ? <ChevronUp className="w-4 h-4" style={{ color: 'var(--text-muted)' }} /> : <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />}
      </button>

      {open && (
        <div className="mt-4 space-y-4 animate-fade-in">
          {/* Entry reasons */}
          {prediction.entry_reasons.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>Score Breakdown</p>
              <div className="space-y-1">
                {prediction.entry_reasons.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs" style={{ color: 'var(--text)' }}>
                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--brand)' }} />
                    {r}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Indicators */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
            <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>Indicators</p>
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(prediction.indicators).map(([key, val]) => {
                let barColor = 'var(--brand)';
                let barWidth = 50;
                if (key === 'RSI 14') {
                  barWidth = Math.min(val, 100);
                  barColor = val > 70 ? 'var(--error)' : val < 30 ? 'var(--success)' : 'var(--brand)';
                } else if (key === 'BB %B') {
                  barWidth = Math.min(Math.max(val * 100, 0), 100);
                  barColor = val > 0.8 ? 'var(--error)' : val < 0.2 ? 'var(--success)' : 'var(--brand)';
                } else if (key === 'ADX') {
                  barWidth = Math.min(val, 100);
                  barColor = val > 25 ? 'var(--success)' : 'var(--text-muted)';
                }
                return (
                  <div key={key} className="py-1.5 px-2 rounded-lg" style={{ background: 'var(--bg-section)' }}>
                    <div className="flex justify-between mb-1">
                      <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{key}</span>
                      <span className="text-[10px] font-semibold" style={{ color: 'var(--text)' }}>{typeof val === 'number' ? val.toFixed(2) : val}</span>
                    </div>
                    <div className="w-full h-1 rounded-full" style={{ background: 'var(--border)' }}>
                      <div className="h-1 rounded-full transition-all" style={{ width: `${barWidth}%`, background: barColor }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 5D Outlook factors */}
          {prediction.outlook?.factors?.length > 0 && (
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
              <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>Outlook Factors</p>
              <div className="space-y-1">
                {prediction.outlook.factors.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs" style={{ color: 'var(--text)' }}>
                    <div className="w-1.5 h-1.5 rounded-full" style={{
                      background: prediction.outlook.direction === 'Bullish' ? 'var(--success)' : prediction.outlook.direction === 'Bearish' ? 'var(--error)' : 'var(--text-muted)'
                    }} />
                    {f}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Main Page ── */
export default function PredictionPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSymbol, setActiveSymbol] = useState('NQ');
  const [searchInput, setSearchInput] = useState('');
  const [instruments, setInstruments] = useState(() => {
    if (typeof window === 'undefined') return 'futures';
    return localStorage.getItem('preferred_instruments') || 'futures';
  });

  useEffect(() => {
    if (!user) { router.push('/login'); }
  }, [user, router]);

  const fetchPrediction = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 90000);
      const accessToken = localStorage.getItem('accessToken');
      const response = await fetch(`/api/ai/drl-predict/${encodeURIComponent(symbol)}`, {
        headers: accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {},
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (!response.ok) {
        const status = response.status;
        if (status === 503) setError('DRL models are loading. Try again in a moment.');
        else if (status === 400) setError(`No data available for "${symbol}". Check the symbol.`);
        else setError(`Server error (${status}). Try again.`);
        return;
      }
      const res = await response.json();
      setPrediction(res);
    } catch (err: any) {
      if (err?.name === 'AbortError') setError(`Request timed out. Server may be busy.`);
      else setError(`Failed to connect. Check your connection.`);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInstrumentChange = (id: string) => {
    setInstruments(id);
    localStorage.setItem('preferred_instruments', id);
    const group = INSTRUMENT_GROUPS.find((g) => g.id === id);
    if (group) {
      const sym = group.symbols[0];
      setActiveSymbol(sym);
      fetchPrediction(sym);
    }
  };

  const handleSymbolClick = (symbol: string) => {
    setActiveSymbol(symbol);
    setSearchInput('');
    fetchPrediction(symbol);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const sym = searchInput.trim().toUpperCase().replace('/', '');
    if (sym) {
      setActiveSymbol(sym);
      fetchPrediction(sym);
    }
  };

  useEffect(() => {
    if (user) fetchPrediction(activeSymbol);
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!user) return null;

  const currentGroup = INSTRUMENT_GROUPS.find((g) => g.id === instruments);

  return (
    <Layout>
      <div className="p-4 sm:p-6 max-w-6xl mx-auto animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ background: 'var(--brand-light)' }}>
              <Brain className="w-4.5 h-4.5" style={{ color: 'var(--brand)' }} />
            </div>
            <div>
              <h1 className="text-lg font-bold" style={{ color: 'var(--text)' }}>Prediction</h1>
              <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>DRL Ensemble + Momentum Analysis</p>
            </div>
          </div>
          <button
            onClick={() => fetchPrediction(activeSymbol)}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-1.5 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Search + Tabs */}
        <form onSubmit={handleSearch} className="mb-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search any symbol..."
                className="input pl-10 text-sm"
              />
            </div>
            <button type="submit" className="btn btn-brand text-sm" disabled={!searchInput.trim() || loading}>
              Analyze
            </button>
          </div>
        </form>

        <div className="flex gap-1.5 mb-2 flex-wrap">
          {INSTRUMENT_GROUPS.map((g) => (
            <button
              key={g.id}
              onClick={() => handleInstrumentChange(g.id)}
              className="px-3 py-1 rounded-full text-xs font-medium transition-all"
              style={{
                background: instruments === g.id ? 'var(--brand)' : 'transparent',
                color: instruments === g.id ? '#FFFFFF' : 'var(--text-muted)',
                border: instruments === g.id ? 'none' : '1px solid var(--border)',
              }}
            >
              {g.label}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5 mb-5 flex-wrap">
          {currentGroup?.symbols.map((sym) => (
            <button
              key={sym}
              onClick={() => handleSymbolClick(sym)}
              className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold transition-all"
              style={{
                background: activeSymbol === sym ? 'var(--brand-light)' : 'var(--bg-section)',
                color: activeSymbol === sym ? 'var(--brand)' : 'var(--text-muted)',
                border: activeSymbol === sym ? '1px solid var(--brand)' : '1px solid transparent',
              }}
            >
              {sym}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="card mb-4 flex items-center gap-3" style={{ borderColor: 'var(--error)' }}>
            <XCircle className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--error)' }} />
            <div>
              <p className="text-xs font-medium" style={{ color: 'var(--error)' }}>Error</p>
              <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{error}</p>
            </div>
          </div>
        )}

        {/* Main Grid: Outlook top, Signal+Risk middle, News+Detail bottom */}
        <div className="space-y-4">
          {/* Outlook (full width) */}
          <OutlookCard prediction={prediction} loading={loading} />

          {/* Signal + Risk */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <SignalCard prediction={prediction} loading={loading} />
            </div>
            <div>
              <RiskPanel prediction={prediction} />
            </div>
          </div>

          {/* News + Details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <NewsFeed symbol={activeSymbol} />
            </div>
            <div>
              <DetailPanel prediction={prediction} />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
