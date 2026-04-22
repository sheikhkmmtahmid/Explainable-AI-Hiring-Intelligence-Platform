import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Briefcase, Users, GitMerge, TrendingUp, ArrowRight, Clock } from 'lucide-react'
import StatCard from '../components/StatCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { getJobs } from '../api/jobs'
import { getCandidates } from '../api/candidates'

export default function Dashboard() {
  const [jobs, setJobs] = useState([])
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getJobs({ page_size: 5, ordering: '-posted_at' }), getCandidates({ page_size: 5 })])
      .then(([j, c]) => {
        setJobs(j.data.results ?? j.data)
        setCandidates(c.data.results ?? c.data)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />

  const activeJobs = jobs.filter(j => j.status === 'active').length

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Overview of your hiring pipeline</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Briefcase}   label="Total Jobs"      value={jobs.length}       sub={`${activeJobs} active`} accent />
        <StatCard icon={Users}       label="Candidates"      value={candidates.length} sub="in database" />
        <StatCard icon={GitMerge}    label="Matches Run"     value="—"                 sub="across all jobs" />
        <StatCard icon={TrendingUp}  label="Avg Match Score" value="—"                 sub="overall" />
      </div>

      {/* Recent Jobs */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-400">
          <h2 className="section-title">Recent Jobs</h2>
          <Link to="/jobs" className="text-xs text-scarlet-400 hover:text-scarlet-300 flex items-center gap-1 font-medium">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="divide-y divide-surface-400">
          {jobs.slice(0, 5).map(job => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="flex items-center justify-between px-5 py-3.5 hover:bg-surface-600 transition-colors group"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate group-hover:text-scarlet-400 transition-colors">
                  {job.title}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">{job.company} · {job.city || job.country || 'Remote'}</p>
              </div>
              <div className="flex items-center gap-3 ml-4 flex-shrink-0">
                <span className={`badge ${job.status === 'active' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-surface-500 text-gray-400'}`}>
                  {job.status}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-scarlet-400 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Candidates */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-surface-400">
          <h2 className="section-title">Recent Candidates</h2>
          <Link to="/candidates" className="text-xs text-scarlet-400 hover:text-scarlet-300 flex items-center gap-1 font-medium">
            View all <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="divide-y divide-surface-400">
          {candidates.slice(0, 5).map(c => (
            <Link
              key={c.id}
              to={`/candidates/${c.id}`}
              className="flex items-center justify-between px-5 py-3.5 hover:bg-surface-600 transition-colors group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-full bg-scarlet-500/20 border border-scarlet-500/30 flex items-center justify-center text-xs font-bold text-scarlet-400 flex-shrink-0">
                  {c.full_name?.[0]?.toUpperCase() ?? '?'}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white truncate group-hover:text-scarlet-400 transition-colors">
                    {c.full_name}
                  </p>
                  <p className="text-xs text-gray-500">{c.current_title || 'Candidate'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 ml-4 flex-shrink-0">
                <span className="text-xs text-gray-500">{c.years_of_experience}y exp</span>
                <ArrowRight className="w-3.5 h-3.5 text-gray-600 group-hover:text-scarlet-400 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
