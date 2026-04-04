import { useState } from 'react';
import {
  Activity, TrendingUp, TrendingDown, MinusCircle,
  RefreshCw, AlertTriangle, ChevronDown, ChevronUp,
  Zap, Shield, BarChart3,
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SMCResult {
  symbol: string;
  interval: string;
  version: string;
  prediction: string;
  raw_prediction: string;
  confidence: number;
  confidence_threshold: number;
  above_threshold: boolean;
  probabilities: { bearish: number; bullish: number };
  models: {
    random_forest: { prediction: string; probabilities: { bearish: number; bullish: number } };
    xgboost: { prediction: string; probabilities: { bearish: number; bullish: number } };
  };
  smc_setup: { detected: boolean; direction?: string; confidence?: number };
  pattern_counts: Record<string, number>;
  bars_analyzed: number;
  features_used: number;
  description: string;
}

interface SMCAnalysisProps {
  symbol: string;
}

export default function SMCAnalysis({ symbol }: SMCAnalysisProps) {
  const [result, setResult] = useState<SMCResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [interval, setInterval] = useState('1h');

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('accessToken');
      const res = await fetch(
        `${API_URL}/api/ai/smc-analysis/${encodeURIComponent(symbol)}?interval=${interval}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getPredictionColor = (pred: string) => {
    if (pred === 'bullish') return 'text-emerald-400';
    if (pred === 'bearish') return 'text-red-400';
    return 'text-yellow-400';
  };

  const getPredictionBg = (pred: string) => {
    if (pred === 'bullish') return 'bg-emerald-500/10 border-emerald-500/30';
    if (pred === 'bearish') return 'bg-red-500/10 border-red-500/30';
    return 'bg-yellow-500/10 border-yellow-500/30';
  };

  const getPredictionIcon = (pred: string) => {
    if (pred === 'bullish') return <TrendingUp className="w-6 h-6 text-emerald-400" />;
    if (pred === 'bearish') return <TrendingDown className="w-6 h-6 text-red-400" />;
    return <MinusCircle className="w-6 h-6 text-yellow-400" />;
  };

  const getPredictionLabel = (pred: string) => {
    if (pred === 'bullish') return 'BULLISH';
    if (pred === 'bearish') return 'BEARISH';
    return 'NO SIGNAL';
  };

  return (
    <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Zap className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-sm">SMC Short-Term Analysis</h3>
            <p className="text-white/40 text-xs">Hourly prediction • SMC + Technical Indicator fusion</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            className="bg-white/[0.06] text-white/70 text-xs rounded-lg px-2 py-1.5 border border-white/[0.08] outline-none"
          >
            <option value="1h">1 Hour</option>
            <option value="4h">4 Hour</option>
            <option value="1d">Daily</option>
          </select>
          <button
            onClick={analyze}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/20 text-purple-300 text-xs font-medium hover:bg-purple-500/30 transition disabled:opacity-50"
          >
            {loading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Activity className="w-3.5 h-3.5" />
            )}
            Analyze
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 mx-4 mt-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="p-4 space-y-4">
          {/* Main prediction */}
          <div className={`rounded-xl p-4 border ${getPredictionBg(result.prediction)}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                {getPredictionIcon(result.prediction)}
                <div>
                  <span className={`text-lg font-bold ${getPredictionColor(result.prediction)}`}>
                    {getPredictionLabel(result.prediction)}
                  </span>
                  <span className="text-white/30 text-xs ml-2">
                    {result.symbol} • {result.interval}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-white/80 text-sm font-semibold">
                  {(result.confidence * 100).toFixed(1)}%
                </div>
                <div className="text-white/40 text-xs">confidence</div>
              </div>
            </div>

            {/* Confidence bar */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-white/40 mb-1">
                <span>Bearish</span>
                <span>Bullish</span>
              </div>
              <div className="h-3 bg-white/[0.06] rounded-full overflow-hidden relative">
                <div
                  className="h-full bg-gradient-to-r from-red-500 to-red-400 absolute left-0"
                  style={{ width: `${result.probabilities.bearish * 100}%` }}
                />
                <div
                  className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 absolute right-0"
                  style={{ width: `${result.probabilities.bullish * 100}%` }}
                />
                {/* Threshold markers */}
                <div
                  className="absolute top-0 h-full w-px bg-white/40"
                  style={{ left: `${(1 - result.confidence_threshold) * 100}%` }}
                  title={`Threshold: ${(result.confidence_threshold * 100).toFixed(0)}%`}
                />
                <div
                  className="absolute top-0 h-full w-px bg-white/40"
                  style={{ left: `${result.confidence_threshold * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className="text-red-400">{(result.probabilities.bearish * 100).toFixed(1)}%</span>
                <span className="text-white/30 text-[10px]">
                  threshold: {(result.confidence_threshold * 100).toFixed(0)}%
                </span>
                <span className="text-emerald-400">{(result.probabilities.bullish * 100).toFixed(1)}%</span>
              </div>
            </div>

            <p className="text-white/50 text-xs">{result.description}</p>
          </div>

          {/* Model agreement row */}
          <div className="grid grid-cols-2 gap-3">
            {(['random_forest', 'xgboost'] as const).map((model) => {
              const m = result.models[model];
              return (
                <div key={model} className="rounded-lg bg-white/[0.04] border border-white/[0.06] p-3">
                  <div className="text-white/40 text-[10px] uppercase tracking-wider mb-1">
                    {model === 'random_forest' ? 'Random Forest' : 'XGBoost'}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-semibold ${getPredictionColor(m.prediction)}`}>
                      {m.prediction.toUpperCase()}
                    </span>
                    <span className="text-white/50 text-xs">
                      {(Math.max(m.probabilities.bearish, m.probabilities.bullish) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* SMC Setup info */}
          {result.smc_setup.detected && (
            <div className="rounded-lg bg-white/[0.04] border border-white/[0.06] p-3 flex items-center gap-3">
              <Shield className="w-4 h-4 text-blue-400" />
              <div>
                <span className="text-white/70 text-xs">SMC Setup: </span>
                <span className={`text-xs font-semibold ${
                  result.smc_setup.direction === 'bullish' ? 'text-emerald-400' : 'text-red-400'
                }`}>
                  {result.smc_setup.direction?.toUpperCase()}
                </span>
                <span className="text-white/40 text-xs ml-2">
                  ({((result.smc_setup.confidence || 0) * 100).toFixed(0)}% confidence)
                </span>
              </div>
            </div>
          )}

          {/* Expandable details */}
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-center gap-1 text-white/30 text-xs hover:text-white/50 transition py-1"
          >
            {expanded ? 'Hide' : 'Show'} details
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {expanded && (
            <div className="space-y-3 pt-1">
              {/* Stats */}
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Features', value: result.features_used, icon: BarChart3 },
                  { label: 'Bars', value: result.bars_analyzed, icon: Activity },
                  { label: 'Version', value: result.version.toUpperCase(), icon: Zap },
                ].map(({ label, value, icon: Icon }) => (
                  <div key={label} className="rounded-lg bg-white/[0.03] p-2 text-center">
                    <Icon className="w-3 h-3 text-white/30 mx-auto mb-1" />
                    <div className="text-white/70 text-xs font-semibold">{value}</div>
                    <div className="text-white/30 text-[10px]">{label}</div>
                  </div>
                ))}
              </div>

              {/* Pattern counts */}
              {result.pattern_counts && Object.keys(result.pattern_counts).length > 0 && (
                <div className="rounded-lg bg-white/[0.03] p-3">
                  <div className="text-white/40 text-[10px] uppercase tracking-wider mb-2">
                    Detected SMC Patterns
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                    {Object.entries(result.pattern_counts)
                      .filter(([, v]) => (v as number) > 0)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .slice(0, 10)
                      .map(([k, v]) => (
                        <div key={k} className="flex justify-between text-xs">
                          <span className="text-white/50 truncate">{k.replace(/_/g, ' ')}</span>
                          <span className="text-white/70 font-mono ml-2">{v as number}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !error && !loading && (
        <div className="p-6 text-center">
          <Activity className="w-8 h-8 text-white/20 mx-auto mb-2" />
          <p className="text-white/30 text-xs">
            Click Analyze to get a short-term prediction for {symbol}
          </p>
          <p className="text-white/20 text-[10px] mt-1">
            Uses 88 features: SMC patterns + technical indicators + temporal lags
          </p>
        </div>
      )}
    </div>
  );
}
