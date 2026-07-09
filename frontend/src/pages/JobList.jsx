import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Plus, Search, Briefcase, MapPin, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import { getJobs } from '../api/jobs'

const PAGE_SIZE = 50

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

// Real-world job postings (imported from public datasets or posted through
// the platform) carry their true original posted_at date, which is often
// years older than synthetic data's -- ordering those tabs by -created_at
// (when the row entered this database) instead of -posted_at keeps them
// reachable instead of buried under every synthetic listing.
const TABS = [
  { key: 'manual',    label: 'My Jobs',    params: { source: 'manual', ordering: '-created_at' } },
  { key: 'active',    label: 'Active',     params: { status: 'active', ordering: '-posted_at'  } },
  { key: 'real',      label: 'Real Data',  params: { is_synthetic: false, ordering: '-created_at' } },
  { key: 'synthetic', label: 'Synthetic',  params: { is_synthetic: true,  ordering: '-posted_at'  } },
  { key: 'all',       label: 'All Jobs',   params: { ordering: '-posted_at' } },
]

export default function JobList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [jobs, setJobs]       = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState(searchParams.get('q') ?? '')
  const [tab, setTab]         = useState(searchParams.get('tab') ?? 'manual')
  const [page, setPage]       = useState(Number(searchParams.get('page')) || 1)
  const [total, setTotal]     = useState(0)

  const tabParams = TABS.find(t => t.key === tab)?.params ?? {}
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const fetchJobs = useCallback(() => {
    setLoading(true)
    getJobs({ search: search || undefined, page_size: PAGE_SIZE, page, ...tabParams })
      .then(({ data }) => {
        const results = data.results ?? data
        setJobs(results)
        setTotal(data.count ?? results.length)
      })
      .finally(() => setLoading(false))
  }, [search, tab, page])

  useEffect(() => { fetchJobs() }, [fetchJobs])

  const syncParams = (next) => {
    const params = { tab: next.tab ?? tab }
    const q = next.search ?? search
    const p = next.page ?? page
    if (q) params.q = q
    if (p > 1) params.page = String(p)
    setSearchParams(params)
  }

  const selectTab = (key) => {
    setTab(key); setPage(1); setSearch('')
    syncParams({ tab: key, search: '', page: 1 })
  }

  const onSearchChange = (value) => {
    setSearch(value); setPage(1)
    syncParams({ search: value, page: 1 })
  }

  const goPage = (p) => {
    const next = Math.max(1, Math.min(p, totalPages))
    setPage(next)
    syncParams({ page: next })
  }

  const listReturnTo = `/jobs?${searchParams.toString()}`

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Jobs</h1>
          <p className="text-gray-500 text-sm mt-1">{total.toLocaleString()} positions</p>
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
            onClick={() => selectTab(t.key)}
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
          onChange={e => onSearchChange(e.target.value)}
        />
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title={tab === 'manual' && !search ? 'No manually posted jobs yet' : 'No jobs found'}
          description={tab === 'manual' && !search
            ? 'Post your first job to start matching candidates against it.'
            : 'Try a different filter or search term.'}
          action={tab === 'manual' && !search
            ? <Link to="/jobs/new" className="btn-primary"><Plus className="w-4 h-4" /> Post a Job</Link>
            : null}
        />
      ) : (
        <>
        <div className="space-y-2">
          {jobs.map(job => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}?returnTo=${encodeURIComponent(listReturnTo)}`}
              className="card flex items-center justify-between px-5 py-4 hover:border-scarlet-500/30 hover:bg-surface-600 transition-all group"
            >
              <div className="flex items-start gap-4 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-surface-500 flex items-center justify-center flex-shrink-0">
                  <Briefcase className="w-5 h-5 text-gray-400" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-white group-hover:text-scarlet-400 transition-colors truncate">
                      {job.title}
                    </p>
                    {job.is_synthetic && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-surface-500 text-gray-500 flex-shrink-0">synthetic</span>
                    )}
                  </div>
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

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => goPage(page - 1)}
              disabled={page === 1}
              className="btn-ghost p-2 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-400">
              Page {page} of {totalPages.toLocaleString()}
            </span>
            <button
              onClick={() => goPage(page + 1)}
              disabled={page === totalPages}
              className="btn-ghost p-2 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
        </>
      )}
    </div>
  )
}
