import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Zap, BarChart3, RefreshCw, GitCompare } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ScoreBar from '../components/ScoreBar'
import { getJob } from '../api/jobs'
import { triggerMatching, getMatchResults } from '../api/matching'
import toast from 'react-hot-toast'

export default function MatchResults() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState(null)
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [selected, setSelected] = useState([])

  useEffect(() => {
    Promise.all([getJob(jobId), getMatchResults(jobId)])
      .then(([j, m]) => {
        setJob(j.data)
        const results = m.data.results ?? m.data
        setMatches(results.sort((a, b) => b.overall_score - a.overall_score))
      })
      .finally(() => setLoading(false))
  }, [jobId])

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      await triggerMatching(jobId)
      toast.success('Matching queued. Refresh in a moment.')
    } catch { toast.error('Failed') } finally { setTriggering(false) }
  }

  const refresh = () => {
    setLoading(true)
    setSelected([])
    getMatchResults(jobId)
      .then(({ data }) => setMatches((data.results ?? data).sort((a, b) => b.overall_score - a.overall_score)))
      .finally(() => setLoading(false))
  }

  const toggleSelect = (id) => {
    setSelected(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : prev.length < 2 ? [...prev, id] : [prev[1], id]
    )
  }

  const handleCompare = () => {
    if (selected.length === 2)
      navigate(`/matching/${jobId}/compare/${selected[0]}/${selected[1]}`)
  }

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />

  return (
    <div className="space-y-5 animate-fade-in">
      <Link to={`/jobs/${jobId}`} className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back to Job</Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="page-title">Match Results</h1>
          <p className="text-gray-500 text-sm mt-1">{job?.title} · {matches.length} candidates ranked</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          {selected.length > 0 && (
            <span className="text-xs text-gray-400">{selected.length}/2 selected</span>
          )}
          <button
            onClick={handleCompare}
            disabled={selected.length !== 2}
            className={`btn-secondary text-sm transition-all ${selected.length === 2 ? 'opacity-100' : 'opacity-40 cursor-not-allowed'}`}
          >
            <GitCompare className="w-4 h-4" /> Compare
          </button>
          <button onClick={refresh} className="btn-secondary text-sm"><RefreshCw className="w-4 h-4" /></button>
          <button onClick={handleTrigger} disabled={triggering} className="btn-primary text-sm">
            <Zap className="w-4 h-4" /> {triggering ? 'Queuing…' : 'Re-run'}
          </button>
        </div>
      </div>

      {selected.length > 0 && (
        <div className="rounded-xl border border-scarlet-500/30 bg-scarlet-500/5 px-4 py-2.5 text-sm text-scarlet-300 flex items-center justify-between gap-2">
          <span>
            {selected.length === 1
              ? 'Select one more candidate to compare.'
              : 'Two candidates selected. Click Compare to see them side by side.'}
          </span>
          <button onClick={() => setSelected([])} className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex-shrink-0">Clear</button>
        </div>
      )}

      {matches.length === 0 ? (
        <div className="card text-center py-16">
          <p className="text-gray-500">No results yet. Run matching to rank candidates.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          {/* Desktop header row — hidden on mobile */}
          <div className="hidden sm:grid sm:grid-cols-12 gap-4 px-5 py-3 border-b border-surface-400 text-xs font-medium text-gray-500 uppercase tracking-wide">
            <div className="col-span-1">#</div>
            <div className="col-span-3">Candidate</div>
            <div className="col-span-2">Overall</div>
            <div className="col-span-5">Score Breakdown</div>
            <div className="col-span-1" />
          </div>

          <div className="divide-y divide-surface-400">
            {matches.map((m, i) => {
              const score = m.overall_score
              const scoreColor = score >= 0.7 ? 'text-emerald-400' : score >= 0.4 ? 'text-gold-400' : 'text-scarlet-400'
              const isSelected = selected.includes(m.id)
              return (
                <div
                  key={m.id}
                  className={`px-4 sm:px-5 py-4 transition-colors ${isSelected ? 'bg-scarlet-500/8 border-l-2 border-scarlet-500' : 'hover:bg-surface-600'}`}
                >
                  {/* Mobile layout */}
                  <div className="sm:hidden">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(m.id)}
                          className="w-3.5 h-3.5 rounded accent-scarlet-500 cursor-pointer flex-shrink-0"
                        />
                        <span className="text-xs text-gray-500 flex-shrink-0">{i + 1}.</span>
                        <Link to={`/candidates/${m.candidate}`} className="text-sm font-medium text-white hover:text-scarlet-400 transition-colors truncate">
                          {m.candidate_name}
                        </Link>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`text-lg font-bold ${scoreColor}`}>{(score * 100).toFixed(0)}%</span>
                        <Link to={`/matching/${jobId}/explain/${m.id}`} className="btn-ghost text-xs py-1 px-2">
                          <BarChart3 className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <ScoreBar label="Semantic"   value={m.semantic_score}      color="scarlet" />
                      <ScoreBar label="Skills"     value={m.skill_overlap_score} color="gold" />
                      <ScoreBar label="Experience" value={m.experience_score}    color="blue" />
                      <ScoreBar label="Education"  value={m.education_score}     color="purple" />
                    </div>
                  </div>

                  {/* Desktop layout */}
                  <div className="hidden sm:grid sm:grid-cols-12 gap-4 items-center">
                    <div className="col-span-1 flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(m.id)}
                        className="w-3.5 h-3.5 rounded accent-scarlet-500 cursor-pointer flex-shrink-0"
                      />
                      <span className="text-sm font-medium text-gray-500">{i + 1}</span>
                    </div>
                    <div className="col-span-3">
                      <Link to={`/candidates/${m.candidate}`} className="text-sm font-medium text-white hover:text-scarlet-400 transition-colors">
                        {m.candidate_name}
                      </Link>
                    </div>
                    <div className="col-span-2">
                      <span className={`text-xl font-bold ${scoreColor}`}>{(score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="col-span-5 space-y-1.5">
                      <ScoreBar label="Semantic"   value={m.semantic_score}      color="scarlet" />
                      <ScoreBar label="Skills"     value={m.skill_overlap_score} color="gold" />
                      <ScoreBar label="Experience" value={m.experience_score}    color="blue" />
                      <ScoreBar label="Education"  value={m.education_score}     color="purple" />
                    </div>
                    <div className="col-span-1 flex justify-end">
                      <Link to={`/matching/${jobId}/explain/${m.id}`} className="btn-ghost text-xs py-1 px-2">
                        <BarChart3 className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
