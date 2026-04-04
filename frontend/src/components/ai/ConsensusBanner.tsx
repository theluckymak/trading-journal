import { ArrowUp, ArrowDown } from 'lucide-react';

interface ConsensusBannerProps {
  direction: string;
  agreement: string;
}

export default function ConsensusBanner({ direction, agreement }: ConsensusBannerProps) {
  const isUp = direction === 'UP';

  return (
    <div className={`rounded-2xl p-4 backdrop-blur-xl border flex items-center justify-between ${
      isUp
        ? 'bg-emerald-500/10 border-emerald-500/30'
        : 'bg-red-500/10 border-red-500/30'
    }`}>
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isUp ? 'bg-emerald-500/20' : 'bg-red-500/20'
        }`}>
          {isUp ? (
            <ArrowUp className="w-4 h-4 text-emerald-400" />
          ) : (
            <ArrowDown className="w-4 h-4 text-red-400" />
          )}
        </div>
        <div>
          <span className="text-white/60 text-sm">Model Consensus: </span>
          <span className={`font-bold text-lg ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
            {direction}
          </span>
        </div>
      </div>
      <div className="text-white/60 text-sm">
        <span className="font-semibold text-white">{agreement}</span> models agree
      </div>
    </div>
  );
}
