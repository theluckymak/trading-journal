import { useState, useCallback, useRef } from 'react';
import { Upload, ImageIcon, X, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ChartAnalysisResult {
  prediction: string;
  confidence: number;
  probabilities: Record<string, number>;
  model: string;
  description: string;
}

export default function ChartUploadAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<ChartAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith('image/')) {
      setError('Please upload an image file (PNG or JPG)');
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragActive(false), []);

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('accessToken');
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_URL}/api/ai/chart-analysis`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Analysis failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze chart');
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const predictionIcon = (pred: string) => {
    if (pred === 'bullish') return <TrendingUp className="w-6 h-6 text-emerald-400" />;
    if (pred === 'bearish') return <TrendingDown className="w-6 h-6 text-red-400" />;
    return <Minus className="w-6 h-6 text-gray-400" />;
  };

  const predictionColor = (pred: string) => {
    if (pred === 'bullish') return 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30';
    if (pred === 'bearish') return 'from-red-500/20 to-red-500/5 border-red-500/30';
    return 'from-gray-500/20 to-gray-500/5 border-gray-500/30';
  };

  return (
    <div className="rounded-2xl p-6 backdrop-blur-xl bg-white/[0.04] border border-white/[0.06]">
      <div className="flex items-center gap-2 mb-4">
        <ImageIcon className="w-4 h-4 text-purple-400" />
        <h3 className="text-white/80 font-medium">Chart Pattern Analysis (CNN)</h3>
        <span className="ml-auto text-xs text-white/30">Upload a candlestick chart image</span>
      </div>

      {/* Drop Zone */}
      {!preview ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`relative cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all ${
            dragActive
              ? 'border-cyan-400/60 bg-cyan-500/10'
              : 'border-white/10 hover:border-white/20 hover:bg-white/[0.02]'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <Upload className="w-8 h-8 text-white/30 mx-auto mb-3" />
          <p className="text-white/50 text-sm">
            Drag & drop a chart image, or <span className="text-cyan-400">click to browse</span>
          </p>
          <p className="text-white/30 text-xs mt-1">
            PNG or JPG — works best with 1H/4H candlestick charts
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Preview */}
          <div className="relative rounded-xl overflow-hidden border border-white/10">
            <img src={preview} alt="Chart preview" className="w-full max-h-64 object-contain bg-[#131722]" />
            <button
              onClick={clear}
              className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 hover:bg-black/80 transition-colors"
            >
              <X className="w-4 h-4 text-white/70" />
            </button>
          </div>

          {/* Analyze Button */}
          {!result && (
            <button
              onClick={analyze}
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500/80 to-cyan-500/80 text-white font-medium text-sm hover:from-purple-500 hover:to-cyan-500 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing patterns...
                </>
              ) : (
                <>
                  <ImageIcon className="w-4 h-4" />
                  Analyze Chart Pattern
                </>
              )}
            </button>
          )}

          {/* Result */}
          {result && (
            <div className={`rounded-xl p-5 bg-gradient-to-br border ${predictionColor(result.prediction)}`}>
              <div className="flex items-center gap-3 mb-3">
                {predictionIcon(result.prediction)}
                <div>
                  <div className="text-white font-bold text-lg capitalize">{result.prediction}</div>
                  <div className="text-white/50 text-xs">{result.description}</div>
                </div>
                <div className="ml-auto text-right">
                  <div className="text-white font-bold text-xl">{(result.confidence * 100).toFixed(1)}%</div>
                  <div className="text-white/40 text-xs">confidence</div>
                </div>
              </div>

              {/* Probability Bars */}
              <div className="space-y-2 mt-4">
                {Object.entries(result.probabilities).map(([cls, prob]) => (
                  <div key={cls} className="flex items-center gap-2">
                    <span className="text-white/50 text-xs w-16 capitalize">{cls}</span>
                    <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          cls === 'bullish' ? 'bg-emerald-400' :
                          cls === 'bearish' ? 'bg-red-400' : 'bg-gray-400'
                        }`}
                        style={{ width: `${prob * 100}%` }}
                      />
                    </div>
                    <span className="text-white/60 text-xs w-12 text-right">{(prob * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>

              {/* Model Info */}
              <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-between">
                <span className="text-white/30 text-xs">{result.model}</span>
                <button
                  onClick={clear}
                  className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  Upload another chart
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-3 rounded-lg p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
