import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, BarChart3, CheckCircle2, AlertTriangle, Trophy } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import LoadingSpinner from '../components/LoadingSpinner'
import { getMatchResult } from '../api/matching'
import { getCandidate } from '../api/candidates'
import { getJob } from '../api/jobs'

const pct = v => Math.round((v ?? 0) * 100)
const scoreColor = v => v >= 0.7 ? 'text-emerald-400' : v >= 0.4 ? 'text-gold-400' : 'text-scarlet-400'

function WinnerBadge() {
  return (
    <span className="inline-flex items-center gap-1 text-xs font-semibold text-gold-400 bg-gold-500/10 border border-gold-500/20 rounded-full px-2 py-0.5">
      <Trophy className="w-3 h-3" /> Better
    </span>
  )
}

function MetricRow({ label, a, b }) {
  const aWins = a > b
  const bWins = b > a
  return (
    <div className="grid grid-cols-3 gap-4 items-center py-3 border-b border-surface-400 last:border-0">
      <div className="flex items-center justify-between gap-2">
        <span className={`text-base font-bold ${scoreColor(a)}`}>{pct(a)}%</span>
        {aWins && <WinnerBadge />}
      </div>
      <div className="text-center text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</div>
      <div className="flex items-center justify-between gap-2 flex-row-reverse">
        <span className={`text-base font-bold ${scoreColor(b)}`}>{pct(b)}%</span>
        {bWins && <WinnerBadge />}
      </div>
    </div>
  )
}

function SkillTags({ skills, variant }) {
  if (!skills?.length) return <span className="text-xs text-gray-600">None</span>
  const styles = {
    green: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    amber: 'bg-gold-500/10 text-gold-400 border border-gold-500/20',
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map(s => (
        <span key={s} className={`text-xs rounded-full px-2.5 py-0.5 ${styles[variant]}`}>{s}</span>
      ))}
    </div>
  )
}

export default function CandidateCompare() {
  const { jobId, matchIdA, matchIdB } = useParams()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    Promise.all([
      getMatchResult(matchIdA),
      getMatchResult(matchIdB),
      getJob(jobId),
    ]).then(async ([rA, rB, rJob]) => {
      const mA = rA.data
      const mB = rB.data
      const job = rJob.data
      const [cA, cB] = await Promise.all([
        getCandidate(mA.candidate),
        getCandidate(mB.candidate),
      ])
      const jobSkills = new Set((job.skill_requirements ?? []).map(s => s.skill_name?.toLowerCase()))
      const toSkillNames = arr => arr.map(s => s.skill_name?.toLowerCase()).filter(Boolean)

      const skillsA = toSkillNames(cA.data.skills ?? [])
      const skillsB = toSkillNames(cB.data.skills ?? [])

      const matchingA = skillsA.filter(s => jobSkills.has(s))
      const missingA  = [...jobSkills].filter(s => !skillsA.includes(s))
      const matchingB = skillsB.filter(s => jobSkills.has(s))
      const missingB  = [...jobSkills].filter(s => !skillsB.includes(s))

      setData({ mA, mB, cA: cA.data, cB: cB.data, job, matchingA, missingA, matchingB, missingB })
    }).finally(() => setLoading(false))
  }, [matchIdA, matchIdB, jobId])

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />
  if (!data) return (
    <div className="card text-center py-16 text-gray-500">Could not load comparison data.</div>
  )

  const { mA, mB, cA, cB, job, matchingA, missingA, matchingB, missingB } = data

  const radarData = [
    { subject: 'Semantic',   a: pct(mA.semantic_score),      b: pct(mB.semantic_score) },
    { subject: 'Skills',     a: pct(mA.skill_overlap_score), b: pct(mB.skill_overlap_score) },
    { subject: 'Experience', a: pct(mA.experience_score),    b: pct(mB.experience_score) },
    { subject: 'Education',  a: pct(mA.education_score),     b: pct(mB.education_score) },
  ]

  const eduMap = { high_school: 'High School', associate: 'Associate', bachelor: "Bachelor's", master: "Master's", phd: 'PhD' }
  const remoteMap = { remote: 'Remote', onsite: 'On-site', hybrid: 'Hybrid', flexible: 'Flexible' }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <Link to={`/matching/${jobId}`} className="btn-ghost text-sm inline-flex">
        <ArrowLeft className="w-4 h-4" /> Back to Results
      </Link>

      <div>
        <h1 className="page-title">Candidate Comparison</h1>
        <p className="text-gray-500 text-sm mt-1">{job.title} · {job.company}</p>
      </div>

      {/* Candidate headers */}
      <div className="grid grid-cols-2 gap-4">
        {[{ c: cA, m: mA, matchId: matchIdA }, { c: cB, m: mB, matchId: matchIdB }].map(({ c, m, matchId }) => {
          const overall = m.overall_score
          const aheadOf = matchId === matchIdA ? mB.overall_score : mA.overall_score
          const isBetter = overall > aheadOf
          return (
            <div key={matchId} className={`card p-5 relative ${isBetter ? 'border border-gold-500/30' : ''}`}>
              {isBetter && (
                <span className="absolute top-3 right-3 inline-flex items-center gap-1 text-xs font-semibold text-gold-400 bg-gold-500/10 border border-gold-500/20 rounded-full px-2.5 py-0.5">
                  <Trophy className="w-3 h-3" /> Higher Match
                </span>
              )}
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-surface-400 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                  {c.full_name?.[0] ?? '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <Link to={`/candidates/${c.id}`} className="font-semibold text-white hover:text-scarlet-400 transition-colors">
                    {c.full_name}
                  </Link>
                  <p className="text-sm text-gray-400 mt-0.5">{c.current_title || '—'}</p>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
                    {c.years_of_experience > 0 && <span>{c.years_of_experience} yrs exp</span>}
                    {c.highest_education && <span>{eduMap[c.highest_education] ?? c.highest_education}</span>}
                    {(c.city || c.country) && <span>{[c.city, c.country].filter(Boolean).join(', ')}</span>}
                    {c.remote_preference && <span>{remoteMap[c.remote_preference] ?? c.remote_preference}</span>}
                  </div>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <div className={`text-3xl font-bold ${scoreColor(overall)}`}>{pct(overall)}%</div>
                  <div className="text-xs text-gray-500 mt-0.5">Overall Match</div>
                </div>
                <Link to={`/matching/${jobId}/explain/${matchId}`} className="btn-secondary text-xs">
                  <BarChart3 className="w-3.5 h-3.5" /> Explanation
                </Link>
              </div>
            </div>
          )
        })}
      </div>

      {/* Radar chart */}
      <div className="card p-5">
        <h2 className="section-title mb-4">Score Radar</h2>
        <ResponsiveContainer width="100%" height={240}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#2E2E2E" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 12 }} />
            <Radar name={cA.full_name} dataKey="a" stroke="#AE0001" fill="#AE0001" fillOpacity={0.25} dot={{ fill: '#AE0001', r: 3 }} />
            <Radar name={cB.full_name} dataKey="b" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.25} dot={{ fill: '#3B82F6', r: 3 }} />
            <Tooltip
              contentStyle={{ background: '#1E1E1E', border: '1px solid #2E2E2E', borderRadius: 8 }}
              labelStyle={{ color: '#fff' }}
              formatter={v => [`${v}%`]}
            />
            <Legend
              formatter={(value) => <span className="text-xs text-gray-400">{value}</span>}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Score breakdown side by side */}
      <div className="card p-5">
        <div className="grid grid-cols-3 gap-4 mb-3 text-sm font-semibold text-center">
          <div className="text-left text-white truncate">{cA.full_name}</div>
          <div className="text-gray-500 text-xs uppercase tracking-wide flex items-center justify-center">Score</div>
          <div className="text-right text-white truncate">{cB.full_name}</div>
        </div>
        <MetricRow label="Overall"    a={mA.overall_score}       b={mB.overall_score} />
        <MetricRow label="Semantic"   a={mA.semantic_score}      b={mB.semantic_score} />
        <MetricRow label="Skills"     a={mA.skill_overlap_score} b={mB.skill_overlap_score} />
        <MetricRow label="Experience" a={mA.experience_score}    b={mB.experience_score} />
        <MetricRow label="Education"  a={mA.education_score}     b={mB.education_score} />
      </div>

      {/* Skills comparison */}
      <div className="grid grid-cols-2 gap-4">
        {/* Candidate A skills */}
        <div className="space-y-4">
          <div className="card p-5 space-y-3">
            <h2 className="flex items-center gap-2 section-title">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> {cA.full_name} · Matching Skills
            </h2>
            <SkillTags skills={matchingA} variant="green" />
          </div>
          <div className="card p-5 space-y-3">
            <h2 className="flex items-center gap-2 section-title">
              <AlertTriangle className="w-4 h-4 text-gold-400" /> {cA.full_name} · Missing Skills
            </h2>
            <SkillTags skills={missingA} variant="amber" />
          </div>
        </div>

        {/* Candidate B skills */}
        <div className="space-y-4">
          <div className="card p-5 space-y-3">
            <h2 className="flex items-center gap-2 section-title">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> {cB.full_name} · Matching Skills
            </h2>
            <SkillTags skills={matchingB} variant="green" />
          </div>
          <div className="card p-5 space-y-3">
            <h2 className="flex items-center gap-2 section-title">
              <AlertTriangle className="w-4 h-4 text-gold-400" /> {cB.full_name} · Missing Skills
            </h2>
            <SkillTags skills={missingB} variant="amber" />
          </div>
        </div>
      </div>
    </div>
  )
}
