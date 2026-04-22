import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Sparkles, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import ScoreBar from '../components/ScoreBar'
import { getExplanation, generateExplanation } from '../api/explainability'
import toast from 'react-hot-toast'

export default function ExplanationDetail() {
  const { jobId, matchId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => { load() }, [matchId])

  const load = () => {
    setLoading(true)
    getExplanation(matchId)
      .then(({ data }) => setData(data))
      .catch(() => autoGenerate())
      .finally(() => setLoading(false))
  }

  const autoGenerate = () => {
    generateExplanation(matchId, 'shap')
      .then(({ data }) => setData(data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }

  const regenerate = async () => {
    setGenerating(true)
    try {
      const { data: result } = await generateExplanation(matchId, 'shap')
      setData(result)
      toast.success('Explanation refreshed')
    } catch {
      toast.error('Failed to regenerate explanation')
    } finally {
      setGenerating(false)
    }
  }

  const pct = v => Math.round((v ?? 0) * 100)

  const radarData = data ? [
    { subject: 'Semantic',   value: pct(data.semantic_score) },
    { subject: 'Skills',     value: pct(data.skill_overlap_score) },
    { subject: 'Experience', value: pct(data.experience_score) },
    { subject: 'Education',  value: pct(data.education_score) },
  ] : []

  const overall = data?.overall_score ?? 0
  const scoreColor = overall >= 0.7 ? 'text-emerald-400' : overall >= 0.4 ? 'text-gold-400' : 'text-scarlet-400'

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <Link to={`/matching/${jobId}`} className="btn-ghost text-sm inline-flex">
        <ArrowLeft className="w-4 h-4" /> Back to Results
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Match Explanation</h1>
          <p className="text-gray-500 text-sm mt-1">AI-generated reasoning for this candidate-job fit</p>
        </div>
        {data && (
          <button onClick={regenerate} disabled={generating} className="btn-secondary text-sm">
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Refreshing…' : 'Refresh'}
          </button>
        )}
      </div>

      {!data ? (
        <div className="card text-center py-16">
          <Sparkles className="w-10 h-10 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 font-medium">Could not generate explanation</p>
          <p className="text-gray-600 text-sm mt-2">Make sure matching has been run for this candidate.</p>
          <button onClick={regenerate} disabled={generating} className="btn-primary mt-4 text-sm">
            <Sparkles className="w-4 h-4" /> Try Again
          </button>
        </div>
      ) : (
        <>
          {/* Overall score + summary */}
          <div className="card p-6">
            <div className="flex items-start gap-6">
              <div className="text-center flex-shrink-0">
                <div className={`text-4xl font-bold ${scoreColor}`}>
                  {pct(overall)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">Overall Match</div>
              </div>
              {data.summary_text && (
                <p className="flex-1 text-sm text-gray-300 leading-relaxed bg-surface-600 rounded-xl p-4 border border-surface-300">
                  {data.summary_text}
                </p>
              )}
            </div>
          </div>

          {/* Radar + Score bars */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="card p-5">
              <h2 className="section-title mb-4">Score Radar</h2>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#2E2E2E" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 12 }} />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="#AE0001"
                    fill="#AE0001"
                    fillOpacity={0.35}
                    dot={{ fill: '#AE0001', r: 3 }}
                  />
                  <Tooltip
                    contentStyle={{ background: '#1E1E1E', border: '1px solid #2E2E2E', borderRadius: 8 }}
                    labelStyle={{ color: '#fff' }}
                    formatter={v => [`${v}%`]}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <h2 className="section-title mb-4">Score Breakdown</h2>
              <div className="space-y-4">
                <ScoreBar label="Semantic Match"  value={data.semantic_score ?? 0}      color="scarlet" />
                <ScoreBar label="Skill Overlap"   value={data.skill_overlap_score ?? 0} color="gold" />
                <ScoreBar label="Experience Fit"  value={data.experience_score ?? 0}    color="blue" />
                <ScoreBar label="Education Match" value={data.education_score ?? 0}     color="purple" />
              </div>
            </div>
          </div>

          {/* Feature importances */}
          {data.feature_importances && Object.keys(data.feature_importances).length > 0 && (
            <div className="card p-5">
              <h2 className="section-title mb-4">What Drove This Score</h2>
              <div className="space-y-3">
                {Object.entries(data.feature_importances)
                  .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                  .map(([feat, val]) => (
                  <div key={feat} className="flex items-center gap-4">
                    <span className="text-sm text-gray-400 w-44 flex-shrink-0 capitalize">
                      {feat.replace(/_/g, ' ')}
                    </span>
                    <div className="flex-1 h-2 bg-surface-400 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${val >= 0 ? 'bg-emerald-500' : 'bg-scarlet-500'}`}
                        style={{ width: `${Math.min(Math.abs(val) * 100, 100)}%` }}
                      />
                    </div>
                    <span className={`text-xs font-mono w-16 text-right flex-shrink-0 ${val >= 0 ? 'text-emerald-400' : 'text-scarlet-400'}`}>
                      {val >= 0 ? '+' : ''}{(val * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Matching / Missing skills */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.matching_skills?.length > 0 && (
              <div className="card p-5">
                <h2 className="flex items-center gap-2 section-title mb-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Matching Skills
                </h2>
                <div className="flex flex-wrap gap-1.5">
                  {data.matching_skills.map(s => (
                    <span key={s} className="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs">{s}</span>
                  ))}
                </div>
              </div>
            )}
            {data.missing_skills?.length > 0 && (
              <div className="card p-5">
                <h2 className="flex items-center gap-2 section-title mb-3">
                  <AlertTriangle className="w-4 h-4 text-gold-400" /> Missing Skills
                </h2>
                <div className="flex flex-wrap gap-1.5">
                  {data.missing_skills.map(s => (
                    <span key={s} className="badge bg-gold-500/10 text-gold-400 border border-gold-500/20 text-xs">{s}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Top factors */}
          {(data.top_positive_factors?.length > 0 || data.top_negative_factors?.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {data.top_positive_factors?.length > 0 && (
                <div className="card p-5">
                  <h2 className="section-title mb-3 text-emerald-400">Strengths</h2>
                  <ul className="space-y-2">
                    {data.top_positive_factors.map((f, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                        {String(f?.feature ?? f).replace(/_/g, ' ')}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {data.top_negative_factors?.length > 0 && (
                <div className="card p-5">
                  <h2 className="section-title mb-3 text-gold-400">Areas to Note</h2>
                  <ul className="space-y-2">
                    {data.top_negative_factors.map((f, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                        <AlertTriangle className="w-3.5 h-3.5 text-gold-400 flex-shrink-0" />
                        {String(f?.feature ?? f).replace(/_/g, ' ')}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
