export default function StatCard({ icon: Icon, label, value, sub, accent = false }) {
  return (
    <div className={`card p-5 flex items-start gap-4 ${accent ? 'border-scarlet-500/30 bg-scarlet-900/10' : ''}`}>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${accent ? 'bg-scarlet-500/20' : 'bg-surface-500'}`}>
        <Icon className={`w-5 h-5 ${accent ? 'text-scarlet-400' : 'text-gray-400'}`} />
      </div>
      <div className="min-w-0">
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value ?? '—'}</p>
        {sub && <p className="text-xs text-gray-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
