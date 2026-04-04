interface IndicatorsPanelProps {
  indicators: Record<string, number>;
  price: {
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  };
}

function formatValue(key: string, value: number): string {
  if (key === 'obv' || key === 'volume') return value.toLocaleString();
  if (Math.abs(value) > 100) return value.toFixed(2);
  if (Math.abs(value) > 1) return value.toFixed(4);
  return value.toFixed(6);
}

function getIndicatorColor(key: string, value: number): string {
  if (key === 'rsi_14') {
    if (value > 70) return 'text-red-400';
    if (value < 30) return 'text-emerald-400';
  }
  if (key === 'willr_14') {
    if (value > -20) return 'text-red-400';
    if (value < -80) return 'text-emerald-400';
  }
  if (key === 'macd_hist') {
    return value > 0 ? 'text-emerald-400' : 'text-red-400';
  }
  return 'text-white';
}

const INDICATOR_GROUPS: Record<string, string[]> = {
  'Momentum': ['rsi_14', 'stoch_k', 'stoch_d', 'willr_14', 'roc_10', 'cci_20'],
  'Trend': ['macd', 'macd_signal', 'macd_hist', 'adx_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26'],
  'Volatility': ['atr_14', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_pct', 'bb_width'],
  'Returns': ['return_1d', 'return_5d', 'return_10d', 'volatility_10d', 'volatility_20d'],
};

export default function IndicatorsPanel({ indicators, price }: IndicatorsPanelProps) {
  return (
    <div className="rounded-2xl p-6 backdrop-blur-xl bg-white/[0.04] border border-white/[0.06]">
      <h3 className="text-lg font-semibold text-white mb-4">Technical Indicators</h3>

      {/* Price Info */}
      <div className="grid grid-cols-4 gap-3 mb-6 pb-4 border-b border-white/[0.06]">
        {[
          { label: 'Open', value: price.open },
          { label: 'High', value: price.high },
          { label: 'Low', value: price.low },
          { label: 'Close', value: price.close },
        ].map(({ label, value }) => (
          <div key={label} className="text-center">
            <div className="text-white/40 text-xs mb-1">{label}</div>
            <div className="text-white font-mono text-sm">{value.toFixed(4)}</div>
          </div>
        ))}
      </div>

      {/* Indicator Groups */}
      {Object.entries(INDICATOR_GROUPS).map(([group, keys]) => {
        const groupIndicators = keys.filter((k) => indicators[k] !== undefined);
        if (groupIndicators.length === 0) return null;

        return (
          <div key={group} className="mb-4">
            <div className="text-white/50 text-xs font-semibold uppercase tracking-wider mb-2">
              {group}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {groupIndicators.map((key) => (
                <div key={key} className="flex justify-between items-center py-1 px-2 rounded bg-white/[0.03]">
                  <span className="text-white/50 text-xs">{key}</span>
                  <span className={`text-xs font-mono ${getIndicatorColor(key, indicators[key])}`}>
                    {formatValue(key, indicators[key])}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
