import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  Sparkles, RefreshCw, Search, Activity, Brain,
  TrendingUp, BarChart3, AlertCircle,
} from 'lucide-react';
import PredictionCard from '@/components/ai/PredictionCard';
import ConsensusBanner from '@/components/ai/ConsensusBanner';
import IndicatorsPanel from '@/components/ai/IndicatorsPanel';
import ModelComparisonTable from '@/components/ai/ModelComparisonTable';
import FeatureImportanceChart from '@/components/ai/FeatureImportanceChart';
import ChartUploadAnalysis from '@/components/ai/ChartUploadAnalysis';
import SMCAnalysis from '@/components/ai/SMCAnalysis';

const API_URL= process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PredictionResult {
  symbol: string;
  date: string;
  prediction_for: string;
  models: Record<string, {
    direction: string;
    confidence: number;
    raw_probability: number;
  }>;
  consensus: { direction: string; agreement: string };
  indicators: Record<string, number>;
  price: { open: number; high: number; low: number; close: number; volume: number };
}

const POPULAR_SYMBOLS = [
  { label: 'EUR/USD', value: 'EURUSD=X' },
  { label: 'GBP/USD', value: 'GBPUSD=X' },
  { label: 'Gold', value: 'XAUUSD=X' },
  { label: 'BTC/USD', value: 'BTC-USD' },
  { label: 'ETH/USD', value: 'ETH-USD' },
  { label: 'S&P 500', value: '^GSPC' },
  { label: 'NASDAQ', value: '^IXIC' },
  { label: 'AAPL', value: 'AAPL' },
  { label: 'TSLA', value: 'TSLA' },
  { label: 'NQ Futures', value: 'NQ=F' },
];

export default function AIInsights() {
  const router = useRouter();
  const { user } = useAuth();
  const [symbol, setSymbol] = useState('EURUSD=X');
  const [customSymbol, setCustomSymbol] = useState('');
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [performance, setPerformance] = useState<any>(null);
  const [importance, setImportance] = useState<any>(null);
  const [aiHealth, setAiHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadAIStatus();
  }, [user, router]);

  const loadAIStatus = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const headers = { Authorization: `Bearer ${token}` };

      const [healthRes, perfRes, impRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/ai/health`, { headers }).then((r) => r.json()),
        fetch(`${API_URL}/api/ai/models/performance`, { headers }).then((r) => r.json()),
        fetch(`${API_URL}/api/ai/feature-importance`, { headers }).then((r) => r.json()),
      ]);

      if (healthRes.status === 'fulfilled') setAiHealth(healthRes.value);
      if (perfRes.status === 'fulfilled' && !perfRes.value.detail) setPerformance(perfRes.value);
      if (impRes.status === 'fulfilled' && !impRes.value.detail) setImportance(impRes.value);
    } catch (err) {
      console.error('Failed to load AI status:', err);
    }
  };

  const getPrediction = async (sym?: string) => {
    const targetSymbol = sym || symbol;
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('accessToken');
      const res = await fetch(`${API_URL}/api/ai/predict/${encodeURIComponent(targetSymbol)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Prediction failed');
      }

      const data = await res.json();
      setPrediction(data);
      setSymbol(targetSymbol);
    } catch (err: any) {
      setError(err.message || 'Failed to get prediction');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomSymbol = () => {
    if (customSymbol.trim()) {
      getPrediction(customSymbol.trim().toUpperCase());
      setCustomSymbol('');
    }
  };

  const modelsReady = aiHealth?.status === 'ready';

  return (
    <Layout>
      <div className="min-h-screen p-6 lg:p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500/20 to-cyan-500/20 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">AI Insights</h1>
              <p className="text-white/50 text-sm">ML-powered market predictions</p>
            </div>
          </div>

          {/* AI Status Badge */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm ${
            modelsReady
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${modelsReady ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            {modelsReady ? 'Models Ready' : 'Models Not Trained'}
          </div>
        </div>

        {/* Not Ready Banner */}
        {!modelsReady && (
          <div className="rounded-2xl p-6 bg-amber-500/10 border border-amber-500/20 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-amber-400 font-semibold mb-1">Models Not Trained Yet</h3>
                <p className="text-white/60 text-sm">
                  Run the training notebook to train the ML models first:
                  <code className="ml-2 px-2 py-0.5 rounded bg-white/10 text-white/80 text-xs">
                    jupyter notebook backend/ai/notebooks/model_training.ipynb
                  </code>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Symbol Selector */}
        <div className="rounded-2xl p-6 backdrop-blur-xl bg-white/[0.04] border border-white/[0.06] mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Search className="w-4 h-4 text-white/50" />
            <h3 className="text-white/80 font-medium">Select Symbol</h3>
          </div>

          {/* Quick Select */}
          <div className="flex flex-wrap gap-2 mb-4">
            {POPULAR_SYMBOLS.map((s) => (
              <button
                key={s.value}
                onClick={() => {
                  setSymbol(s.value);
                  if (modelsReady) getPrediction(s.value);
                }}
                className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                  symbol === s.value
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    : 'bg-white/[0.04] text-white/60 border border-white/[0.06] hover:bg-white/[0.08]'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* Custom Symbol Input */}
          <div className="flex gap-2">
            <input
              type="text"
              value={customSymbol}
              onChange={(e) => setCustomSymbol(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCustomSymbol()}
              placeholder="Enter custom symbol (e.g., MSFT, GBPJPY=X)..."
              className="flex-1 px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/30 text-sm"
            />
            <button
              onClick={() => getPrediction()}
              disabled={loading || !modelsReady}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500/80 to-blue-500/80 text-white font-medium text-sm hover:from-cyan-500 hover:to-blue-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Brain className="w-4 h-4" />
              )}
              Get Prediction
            </button>
          </div>
        </div>

        {/* Chart Pattern Analysis (CNN) */}
        <div className="mb-6">
          <ChartUploadAnalysis />
        </div>

        {/* SMC Short-Term Analysis */}
        <div className="mb-6">
          <SMCAnalysis symbol={symbol} />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl p-4 bg-red-500/10 border border-red-500/20 mb-6 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Prediction Results */}
        {prediction && (
          <>
            {/* Date Info */}
            <div className="text-white/40 text-sm mb-4">
              Prediction for <span className="text-white/70">{prediction.prediction_for}</span>
              {' '}based on data up to <span className="text-white/70">{prediction.date}</span>
            </div>

            {/* Model Prediction Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {Object.entries(prediction.models).map(([name, data]) => (
                <PredictionCard
                  key={name}
                  modelName={name}
                  direction={data.direction}
                  confidence={data.confidence}
                  color={
                    name === 'LSTM' ? '#2563eb' :
                    name === 'Random Forest' ? '#16a34a' : '#dc2626'
                  }
                />
              ))}
            </div>

            {/* Consensus */}
            <div className="mb-6">
              <ConsensusBanner
                direction={prediction.consensus.direction}
                agreement={prediction.consensus.agreement}
              />
            </div>

            {/* Indicators Panel */}
            <div className="mb-6">
              <IndicatorsPanel
                indicators={prediction.indicators}
                price={prediction.price}
              />
            </div>
          </>
        )}

        {/* Model Performance & Feature Importance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {performance && (
            <div className="lg:col-span-2">
              <ModelComparisonTable performance={performance} />
            </div>
          )}

          {importance?.random_forest && (
            <FeatureImportanceChart
              importance={importance.random_forest}
              title="Feature Importance — Random Forest"
              topN={12}
            />
          )}

          {importance?.xgboost && (
            <FeatureImportanceChart
              importance={importance.xgboost}
              title="Feature Importance — XGBoost"
              topN={12}
            />
          )}
        </div>
      </div>
    </Layout>
  );
}
