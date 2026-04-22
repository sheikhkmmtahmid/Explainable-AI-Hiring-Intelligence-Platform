export default function ScoreBar({ label, value, max = 1, color = 'scarlet' }) {
  const pct = Math.min((value / max) * 100, 100)
  const colorMap = {
    scarlet: 'bg-scarlet-500',
    gold: 'bg-gold-500',
    green: 'bg-emerald-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
  }
  const scoreColor = pct >= 70 ? 'text-emerald-400' : pct >= 40 ? 'text-gold-400' : 'text-scarlet-400'

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-xs">
        <span className="text-gray-400 font-medium">{label}</span>
        <span className={`font-semibold ${scoreColor}`}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1.5 bg-surface-400 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${colorMap[color]}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
