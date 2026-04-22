import { AlertTriangle } from 'lucide-react'

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Delete', onConfirm, onCancel, danger = true }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative bg-surface-700 border border-surface-400 rounded-2xl shadow-2xl w-full max-w-sm p-6 animate-fade-in">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-4 ${danger ? 'bg-scarlet-500/15' : 'bg-gold-500/15'}`}>
          <AlertTriangle className={`w-5 h-5 ${danger ? 'text-scarlet-400' : 'text-gold-400'}`} />
        </div>
        <h3 className="text-base font-semibold text-white mb-1">{title}</h3>
        <p className="text-sm text-gray-400 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="btn-ghost text-sm">Cancel</button>
          <button
            onClick={onConfirm}
            className={`text-sm font-medium px-4 py-2 rounded-lg transition-colors ${
              danger
                ? 'bg-scarlet-500 hover:bg-scarlet-600 text-white'
                : 'bg-gold-500 hover:bg-gold-600 text-black'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
