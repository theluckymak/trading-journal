import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

interface FeatureImportanceChartProps {
  importance: Record<string, number>;
  title?: string;
  topN?: number;
}

const COLORS = [
  '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe',
  '#818cf8', '#a5b4fc', '#c7d2fe', '#64748b', '#94a3b8',
  '#06b6d4', '#22d3ee', '#67e8f9', '#a5f3fc', '#cffafe',
];

export default function FeatureImportanceChart({
  importance,
  title = 'Feature Importance',
  topN = 12,
}: FeatureImportanceChartProps) {
  const data = Object.entries(importance)
    .sort(([, a], [, b]) => b - a)
    .slice(0, topN)
    .map(([name, value]) => ({
      name: name.replace(/_/g, ' '),
      value: parseFloat((value * 100).toFixed(2)),
    }))
    .reverse(); // Reverse for horizontal bar (top to bottom)

  return (
    <div className="rounded-2xl p-6 backdrop-blur-xl bg-white/[0.04] border border-white/[0.06]">
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={Math.max(300, data.length * 32)}>
        <BarChart data={data} layout="vertical" margin={{ left: 100, right: 30, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            type="number"
            tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
            tickFormatter={(v) => `${v}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 11 }}
            width={95}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff',
            }}
            formatter={(value: number) => [`${value}%`, 'Importance']}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
