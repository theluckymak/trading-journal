import { ArrowUp, ArrowDown } from 'lucide-react';

interface PredictionCardProps {
  modelName: string;
  direction: string;
  confidence: number;
  color: string;
}

export default function PredictionCard({ modelName, direction, confidence, color }: PredictionCardProps) {
  const isUp = direction === 'UP';
  const confidencePct = (confidence * 100).toFixed(1);

  return (
    <div className={`rounded-2xl p-6 backdrop-blur-xl border transition-all hover:scale-[1.02] ${
      isUp
        ? 'bg-emerald-500/10 border-emerald-500/20'
        : 'bg-red-500/10 border-red-500/20'
    }`}>
      <div className="text-sm text-white/60 mb-2 font-medium">{modelName}</div>
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
          isUp ? 'bg-emerald-500/20' : 'bg-red-500/20'
        }`}>
          {isUp ? (
            <ArrowUp className="w-5 h-5 text-emerald-400" />
          ) : (
            <ArrowDown className="w-5 h-5 text-red-400" />
          )}
        </div>
        <span className={`text-2xl font-bold ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
          {direction}
        </span>
      </div>
      <div className="text-white/80 text-sm">
        Confidence: <span className="font-semibold text-white">{confidencePct}%</span>
      </div>
    </div>
  );
}
