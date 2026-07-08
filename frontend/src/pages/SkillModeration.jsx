import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Check, X, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { listPendingSkills, reviewPendingSkill } from '../api/taxonomy'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

const STATUS_TABS = [
  { value: 'pending', label: 'Pending Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
]

const SOURCE_LABELS = {
  esco_sync: 'ESCO Sync',
  corpus_mining: 'Corpus Mining',
  user_submitted: 'Recruiter Submitted',
}

const MATCH_TYPE_LABELS = {
  fuzzy: 'Possible typo/variant of',
  embedding: 'Semantically similar to',
}

export default function SkillModeration() {
  const { user } = useAuth()
  const [tab, setTab] = useState('pending')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)

  const fetch = () => {
    setLoading(true)
    listPendingSkills(tab)
      .then(({ data }) => setItems(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetch() }, [tab])

  if (!user || user.role !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <p className="text-lg font-medium">Access denied</p>
        <p className="text-sm mt-1">Skill taxonomy moderation is admin-only.</p>
        <Link to="/" className="mt-4 text-scarlet-400 hover:underline text-sm">Go to Dashboard</Link>
      </div>
    )
  }

  const review = async (pending, action) => {
    setBusyId(pending.id)
    try {
      await reviewPendingSkill(pending.id, action)
      toast.success(action === 'approve' ? `Approved "${pending.proposed_name}"` : `Rejected "${pending.proposed_name}"`)
      setItems((prev) => prev.filter((p) => p.id !== pending.id))
    } catch {
      toast.error('Failed to update skill')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Link to="/" className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back to Dashboard</Link>

      <div>
        <h1 className="page-title flex items-center gap-2"><Sparkles className="w-6 h-6 text-scarlet-400" /> Skill Taxonomy Moderation</h1>
        <p className="text-gray-500 text-sm mt-1">
          Skills discovered from ESCO, mined from job/CV text, or typed by recruiters while posting a job. Nothing here
          reaches the shared skill library until you approve it — approving a flagged duplicate merges it as an alias
          instead of creating a redundant entry.
        </p>
      </div>

      <div className="flex gap-2">
        {STATUS_TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t.value ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20' : 'text-gray-400 hover:text-white hover:bg-surface-600'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="Nothing here"
          description={tab === 'pending' ? 'No skills are waiting for review right now.' : `No ${tab} skills yet.`}
        />
      ) : (
        <div className="card divide-y divide-surface-400">
          {items.map((p) => (
            <div key={p.id} className="p-4 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-white">{p.proposed_name}</span>
                  <span className="badge text-xs bg-surface-500 text-gray-400">{SOURCE_LABELS[p.source] ?? p.source}</span>
                  {p.similar_existing_skill && (
                    <span className="badge text-xs bg-gold-500/15 text-gold-400 border border-gold-500/20">
                      {MATCH_TYPE_LABELS[p.similarity_match_type] ?? 'Similar to'} "{p.similar_existing_skill.canonical_name}"
                      {p.similarity_score != null && ` (${Math.round(p.similarity_score * 100)}%)`}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1 truncate">{p.source_detail}</p>
              </div>
              {tab === 'pending' && (
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    disabled={busyId === p.id}
                    onClick={() => review(p, 'approve')}
                    className="btn-secondary text-xs py-1.5 px-3"
                    title={p.similar_existing_skill ? 'Merge as alias' : 'Add as new skill'}
                  >
                    <Check className="w-3.5 h-3.5" /> {p.similar_existing_skill ? 'Merge' : 'Approve'}
                  </button>
                  <button
                    disabled={busyId === p.id}
                    onClick={() => review(p, 'reject')}
                    className="btn-ghost text-xs py-1.5 px-3 text-scarlet-400 hover:bg-scarlet-500/10 border border-scarlet-500/20"
                  >
                    <X className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
