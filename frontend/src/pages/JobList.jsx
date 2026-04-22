import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Briefcase, MapPin, ArrowRight } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import { getJobs } from '../api/jobs'

const EMP_LABELS = {
  full_time: 'Full-time', part_time: 'Part-time',
  contract: 'Contract', internship: 'Internship', freelance: 'Freelance',
}
const STATUS_STYLES = {
  active: 'bg-emerald-500/15 text-emerald-400',
  closed: 'bg-surface-500 text-gray-500',
  draft:  'bg-gold-500/15 text-gold-400',
  filled: 'bg-blue-500/15 text-blue-400',
}

const TABS = [
  { key: 'manual',    label: 'My Jobs',   params: { source: 'manual', ordering: '-created_at' } },
  { key: 'active',    label: 'Active',    params: { status: 'active', ordering: '-posted_at'  } },
  { key: 'all',       label: 'All Jobs',  params: { ordering: '-posted_at' } },
]

export default function JobList() {
  const [jobs, setJobs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [tab, setTab]         = useState('manual')

  const fetchJobs = useCallback(() => {
    setLoading(true)
    const tabParams = TABS.find(t => t.key === tab)?.params ?? {}
    getJobs({ search: search || undefined, page_size: 100, ...tabParams })
      .then(({ data }) => setJobs(data.results ?? data))
      .finally(() => setLoading(false))
  }, [search, tab])

  useEffect(() => { fetchJobs() }, [fetchJobs])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Jobs</h1>
          <p className="text-gray-500 text-sm mt-1">{jobs.length} positions</p>
        </div>
        <Link to="/jobs/new" className="btn-primary">
          <Plus className="w-4 h-4" /> Post a Job
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-surface-700 p-1 rounded-xl w-fit border border-surface-400">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setSearch('') }}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.key
                ? 'bg-scarlet-500 text-white shadow'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          className="input pl-9"
          placeholder="Search by title, company, location…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title={tab === 'manual' ? 'No manually posted jobs yet' : 'No jobs found'}
          description={tab === 'manual'
            ? 'Post your first job to start matching candidates against it.'
            : 'Try a different filter or search term.'}
          action={tab === 'manual'
            ? <Link to="/jobs/new" className="btn-primary"><Plus className="w-4 h-4" /> Post a Job</Link>
            : null}
        />
      ) : (
        <div className="space-y-2">
          {jobs.map(job => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="card flex items-center justify-between px-5 py-4 hover:border-scarlet-500/30 hover:bg-surface-600 transition-all group"
            >
              <div className="flex items-start gap-4 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-surface-500 flex items-center justify-center flex-shrink-0">
                  <Briefcase className="w-5 h-5 text-gray-400" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-white group-hover:text-scarlet-400 transition-colors truncate">
                    {job.title}
                  </p>
                  <p className="text-sm text-gray-500 mt-0.5">{job.company}</p>
                  <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                    {(job.city || job.country) && (
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <MapPin className="w-3 h-3" />
                        {[job.city, job.country].filter(Boolean).join(', ')}
                      </span>
                    )}
                    {job.employment_type && (
                      <span className="text-xs text-gray-500">{EMP_LABELS[job.employment_type] ?? job.employment_type}</span>
                    )}
                    {job.salary_min && (
                      <span className="text-xs text-gray-500">
                        {job.salary_currency} {(job.salary_min / 1000).toFixed(0)}k – {(job.salary_max / 1000).toFixed(0)}k
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 ml-4 flex-shrink-0">
                <span className={`badge ${STATUS_STYLES[job.status] ?? 'bg-surface-500 text-gray-400'}`}>
                  {job.status}
                </span>
                <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-scarlet-400 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
