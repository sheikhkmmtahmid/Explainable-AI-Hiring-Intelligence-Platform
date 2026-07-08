import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Building2, Check, CreditCard, Landmark, Smartphone } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { getPlans, getProviders, getSubscription, subscribe, submitPaymentProof } from '../api/billing'
import { updateMyOrganization } from '../api/organizations'
import { COUNTRIES } from '../constants/countries'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_STYLES = {
  active: 'bg-emerald-500/15 text-emerald-400',
  trialing: 'bg-blue-500/15 text-blue-400',
  past_due: 'bg-gold-500/15 text-gold-400',
  canceled: 'bg-surface-500 text-gray-400',
  incomplete: 'bg-surface-500 text-gray-400',
}

const PROVIDER_ICONS = { stripe: CreditCard, sslcommerz: Smartphone, manual: Landmark }

export default function Billing() {
  const { user, refreshUser } = useAuth()
  const [plans, setPlans] = useState([])
  const [providers, setProviders] = useState([])
  const [subscription, setSubscription] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [selectedProvider, setSelectedProvider] = useState(null)
  const [starting, setStarting] = useState(false)
  const [pendingPayment, setPendingPayment] = useState(null)
  const [proofNote, setProofNote] = useState('')
  const [proofRef, setProofRef] = useState('')
  const [submittingProof, setSubmittingProof] = useState(false)
  const [countryDraft, setCountryDraft] = useState('')
  const [savingCountry, setSavingCountry] = useState(false)

  const hasOrg = !!user?.organization

  useEffect(() => {
    if (user?.organization) setCountryDraft(user.organization.country ?? '')
  }, [user?.organization?.country])

  const fetchBillingData = () => {
    if (!hasOrg) { setLoading(false); return }
    setLoading(true)
    Promise.all([
      getPlans(),
      getProviders(),
      // No subscription yet is a normal, expected state (not an error) --
      // don't let a 404 here fail the other two requests via Promise.all.
      getSubscription().catch(() => ({ data: null })),
    ])
      .then(([p, prov, sub]) => {
        setPlans(p.data.results ?? p.data)
        setProviders(prov.data.results ?? prov.data)
        setSubscription(sub.data)
      })
      .finally(() => setLoading(false))
  }

  useEffect(fetchBillingData, [hasOrg])

  const handleSaveCountry = async () => {
    setSavingCountry(true)
    try {
      await updateMyOrganization({ country: countryDraft })
      await refreshUser()
      toast.success('Company country updated — recommended payment methods refreshed below.')
    } catch {
      toast.error('Failed to update company details')
    } finally {
      setSavingCountry(false)
    }
  }

  if (!user || (user.role !== 'admin' && !user.is_platform_staff)) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <p className="text-lg font-medium">Access denied</p>
        <p className="text-sm mt-1">Only your organization's admin can manage billing.</p>
        <Link to="/" className="mt-4 text-scarlet-400 hover:underline text-sm">Go to Dashboard</Link>
      </div>
    )
  }

  if (!hasOrg) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <p className="text-lg font-medium">You're platform staff</p>
        <p className="text-sm mt-1">This page manages a company's own subscription. To confirm customer payments, use Payment Review.</p>
        <Link to="/billing/moderation" className="mt-4 text-scarlet-400 hover:underline text-sm">Go to Payment Review</Link>
      </div>
    )
  }

  const orgCountry = user.organization?.country
  const isRecommended = (provider) => orgCountry && provider.recommended_countries?.includes(orgCountry)

  const handleSubscribe = async () => {
    if (!selectedPlan || !selectedProvider) return
    setStarting(true)
    try {
      const { data } = await subscribe(selectedPlan.id, selectedProvider.code)
      if (data.redirect_url) {
        window.location.href = data.redirect_url
        return
      }
      if (data.requires_proof) {
        setPendingPayment(data)
        toast.success('Follow the instructions below, then submit your payment reference.')
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start subscription')
    } finally {
      setStarting(false)
    }
  }

  const handleSubmitProof = async () => {
    if (!proofRef.trim()) {
      toast.error('Enter a payment reference (transaction ID, bank reference, etc.)')
      return
    }
    setSubmittingProof(true)
    try {
      await submitPaymentProof(pendingPayment.payment_id, { proof_note: proofNote, external_reference: proofRef })
      toast.success('Submitted for review. Your subscription activates once confirmed.')
      setPendingPayment(null)
      setProofNote(''); setProofRef('')
    } catch {
      toast.error('Failed to submit payment reference')
    } finally {
      setSubmittingProof(false)
    }
  }

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      <Link to="/" className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back to Dashboard</Link>

      <div>
        <h1 className="page-title">Billing</h1>
        <p className="text-gray-500 text-sm mt-1">Manage your organization's subscription and payment method.</p>
      </div>

      <div className="card p-5 space-y-3">
        <h2 className="section-title flex items-center gap-2"><Building2 className="w-4 h-4 text-gray-400" /> Company Details</h2>
        <p className="text-xs text-gray-500">
          Set your company's country so we can recommend the payment method most people actually use there —
          local mobile banking and cards where we support them, or bank transfer everywhere else.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="flex-1 max-w-xs">
            <label className="label">Country</label>
            <select className="input" value={countryDraft} onChange={(e) => setCountryDraft(e.target.value)}>
              <option value="">Select a country…</option>
              {COUNTRIES.map((c) => (
                <option key={c.code} value={c.code}>{c.name}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSaveCountry}
            disabled={savingCountry || countryDraft === (user.organization.country ?? '')}
            className="btn-secondary text-sm"
          >
            {savingCountry ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>

      {subscription && (
        <div className="card p-5 flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-sm text-gray-500">Current plan</p>
            <p className="text-lg font-semibold text-white">{subscription.plan?.name}</p>
          </div>
          <span className={`badge text-sm ${STATUS_STYLES[subscription.status] ?? 'bg-surface-500 text-gray-400'}`}>
            {subscription.status.replace('_', ' ')}
          </span>
        </div>
      )}

      {pendingPayment ? (
        <div className="card p-5 space-y-4">
          <h2 className="section-title">Complete Your Payment</h2>
          <p className="text-sm text-gray-400">{pendingPayment.instructions}</p>
          <div>
            <label className="label">Payment reference / transaction ID</label>
            <input className="input" value={proofRef} onChange={(e) => setProofRef(e.target.value)} placeholder="e.g. bKash TrxID, bank reference number" />
          </div>
          <div>
            <label className="label">Note (optional)</label>
            <textarea className="input resize-none" rows={3} value={proofNote} onChange={(e) => setProofNote(e.target.value)} placeholder="Any detail that helps us confirm your payment" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleSubmitProof} disabled={submittingProof} className="btn-primary text-sm">
              {submittingProof ? 'Submitting…' : 'Submit for Review'}
            </button>
            <button onClick={() => setPendingPayment(null)} className="btn-ghost text-sm">Cancel</button>
          </div>
        </div>
      ) : (
        <>
          <div>
            <h2 className="section-title mb-3">Choose a Plan</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {plans.map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan)}
                  className={`card p-5 text-left transition-all ${selectedPlan?.id === plan.id ? 'border-scarlet-500 ring-1 ring-scarlet-500' : 'hover:border-surface-300'}`}
                >
                  <p className="text-lg font-semibold text-white">{plan.name}</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {plan.price === '0.00' ? 'Free' : `${plan.currency} ${plan.price}`}
                    {plan.price !== '0.00' && <span className="text-sm text-gray-500 font-normal">/{plan.billing_interval === 'yearly' ? 'yr' : 'mo'}</span>}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">{plan.description}</p>
                  <ul className="text-xs text-gray-400 mt-3 space-y-1">
                    <li>{plan.max_active_jobs ?? 'Unlimited'} active jobs</li>
                    <li>{plan.max_seats ?? 'Unlimited'} team seats</li>
                  </ul>
                </button>
              ))}
            </div>
          </div>

          <div>
            <h2 className="section-title mb-3">Choose How to Pay</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {providers.map((provider) => {
                const Icon = PROVIDER_ICONS[provider.code] ?? CreditCard
                const recommended = isRecommended(provider)
                return (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider)}
                    disabled={!provider.is_configured}
                    className={`card p-4 text-left transition-all disabled:opacity-40 disabled:cursor-not-allowed ${selectedProvider?.id === provider.id ? 'border-scarlet-500 ring-1 ring-scarlet-500' : 'hover:border-surface-300'}`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-gray-400" />
                      <p className="text-sm font-medium text-white">{provider.name}</p>
                      {recommended && <span className="badge text-xs bg-scarlet-500/15 text-scarlet-400">Recommended</span>}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">{provider.description}</p>
                    {!provider.is_configured && (
                      <p className="text-xs text-gold-400 mt-2">Not yet set up by the platform operator.</p>
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          <button
            onClick={handleSubscribe}
            disabled={!selectedPlan || !selectedProvider || starting}
            className="btn-primary"
          >
            <Check className="w-4 h-4" /> {starting ? 'Starting…' : 'Subscribe'}
          </button>
        </>
      )}
    </div>
  )
}
