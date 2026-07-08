import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Check, Landmark, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getPendingPayments, reviewPayment } from '../api/billing'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

export default function BillingModeration() {
  const { user } = useAuth()
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)

  const fetch = () => {
    setLoading(true)
    getPendingPayments().then(({ data }) => setPayments(data.results ?? data)).finally(() => setLoading(false))
  }
  useEffect(() => { fetch() }, [])

  if (!user || !user.is_platform_staff) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <p className="text-lg font-medium">Access denied</p>
        <p className="text-sm mt-1">Payment review is platform-staff only.</p>
        <Link to="/" className="mt-4 text-scarlet-400 hover:underline text-sm">Go to Dashboard</Link>
      </div>
    )
  }

  const review = async (payment, action) => {
    setBusyId(payment.id)
    try {
      await reviewPayment(payment.id, action)
      toast.success(action === 'approve' ? `Approved ${payment.organization_name}'s payment` : `Rejected ${payment.organization_name}'s payment`)
      setPayments((prev) => prev.filter((p) => p.id !== payment.id))
    } catch {
      toast.error('Failed to update payment')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Link to="/" className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back to Dashboard</Link>

      <div>
        <h1 className="page-title flex items-center gap-2"><Landmark className="w-6 h-6 text-scarlet-400" /> Payment Review</h1>
        <p className="text-gray-500 text-sm mt-1">
          Manually-submitted payments (bank transfer, mobile banking without a live integration, etc.) awaiting confirmation.
        </p>
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : payments.length === 0 ? (
        <EmptyState icon={Landmark} title="Nothing to review" description="No manual payments are waiting for confirmation." />
      ) : (
        <div className="card divide-y divide-surface-400">
          {payments.map((p) => (
            <div key={p.id} className="p-4 flex items-center justify-between gap-4 flex-wrap">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-white">{p.organization_name}</span>
                  <span className="badge text-xs bg-surface-500 text-gray-400">{p.provider_name}</span>
                  <span className="text-sm text-gray-300">{p.amount} {p.currency}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">Reference: {p.external_reference || '(none)'}</p>
                {p.proof_note && <p className="text-xs text-gray-500">Note: {p.proof_note}</p>}
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button disabled={busyId === p.id} onClick={() => review(p, 'approve')} className="btn-secondary text-xs py-1.5 px-3">
                  <Check className="w-3.5 h-3.5" /> Approve
                </button>
                <button disabled={busyId === p.id} onClick={() => review(p, 'reject')} className="btn-ghost text-xs py-1.5 px-3 text-scarlet-400 hover:bg-scarlet-500/10 border border-scarlet-500/20">
                  <X className="w-3.5 h-3.5" /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
