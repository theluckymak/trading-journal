interface ModelComparisonTableProps {
  performance: Record<string, {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    auc_roc: number;
  }>;
}

export default function ModelComparisonTable({ performance }: ModelComparisonTableProps) {
  const models = Object.entries(performance);

  return (
    <div className="rounded-2xl p-6 backdrop-blur-xl bg-white/[0.04] border border-white/[0.06]">
      <h3 className="text-lg font-semibold text-white mb-4">Model Performance Comparison</h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left py-3 px-2 text-white/50 font-medium">Model</th>
              <th className="text-center py-3 px-2 text-white/50 font-medium">Accuracy</th>
              <th className="text-center py-3 px-2 text-white/50 font-medium">Precision</th>
              <th className="text-center py-3 px-2 text-white/50 font-medium">Recall</th>
              <th className="text-center py-3 px-2 text-white/50 font-medium">F1 Score</th>
              <th className="text-center py-3 px-2 text-white/50 font-medium">AUC-ROC</th>
            </tr>
          </thead>
          <tbody>
            {models.map(([name, metrics]) => {
              const isBest = models.every(
                ([, m]) => metrics.f1_score >= m.f1_score
              );

              return (
                <tr
                  key={name}
                  className={`border-b border-white/[0.03] ${
                    isBest ? 'bg-cyan-500/5' : ''
                  }`}
                >
                  <td className="py-3 px-2">
                    <span className="text-white font-medium">{name}</span>
                    {isBest && (
                      <span className="ml-2 text-xs text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded-full">
                        Best
                      </span>
                    )}
                  </td>
                  <td className="text-center py-3 px-2 text-white font-mono">
                    {(metrics.accuracy * 100).toFixed(1)}%
                  </td>
                  <td className="text-center py-3 px-2 text-white font-mono">
                    {(metrics.precision * 100).toFixed(1)}%
                  </td>
                  <td className="text-center py-3 px-2 text-white font-mono">
                    {(metrics.recall * 100).toFixed(1)}%
                  </td>
                  <td className="text-center py-3 px-2 text-white font-mono">
                    {metrics.f1_score.toFixed(4)}
                  </td>
                  <td className="text-center py-3 px-2 text-white font-mono">
                    {metrics.auc_roc.toFixed(4)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
