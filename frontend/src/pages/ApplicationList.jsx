import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { BarChart3, Briefcase, ChevronLeft, ChevronRight, ClipboardList, X } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import JobFilterCombobox from '../components/JobFilterCombobox'
import { getApplications, updateApplicationStatus } from '../api/applications'
import { STATUS_OPTIONS, STATUS_STYLES } from '../constants/applicationStatus'
import toast from 'react-hot-toast'

const PAGE_SIZE = 50

export default function ApplicationList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [applications, setApplications] = useState([])
  const [loading, setLoading]           = useState(true)
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') ?? '')
  const [page, setPage]                 = useState(Number(searchParams.get('page')) || 1)
  const [total, setTotal]               = useState(0)
  const totalPages = Math.ceil(total / PAGE_SIZE)

  // Job filter: id lives in the URL so a deep link (from a job's detail
  // page) or a page refresh both keep the filter intact without an extra
  // round trip just to resolve which job was selected.
  const [jobFilter, setJobFilter] = useState(() => {
    const id = searchParams.get('job')
    return id ? { id, title: searchParams.get('job_title') ?? `Job #${id}`, company: searchParams.get('job_company') ?? '' } : null
  })

  const fetch = useCallback(() => {
    setLoading(true)
    getApplications({ status: statusFilter || undefined, job: jobFilter?.id || undefined, page_size: PAGE_SIZE, page })
      .then(({ data }) => {
        const results = data.results ?? data
        setApplications(results)
        setTotal(data.count ?? results.length)
      })
      .finally(() => setLoading(false))
  }, [statusFilter, jobFilter, page])

  useEffect(() => { fetch() }, [fetch])

  const onStatusFilterChange = (value) => {
    setStatusFilter(value)
    setPage(1)
    setSearchParams((prev) => {
      const params = Object.fromEntries(prev)
      if (value) params.status = value; else delete params.status
      params.page = '1'
      return params
    })
  }

  const onJobFilterSelect = (job) => {
    setJobFilter({ id: job.id, title: job.title, company: job.company })
    setPage(1)
    setSearchParams((prev) => {
      const params = Object.fromEntries(prev)
      params.job = String(job.id)
      params.job_title = job.title
      params.job_company = job.company
      params.page = '1'
      return params
    })
  }

  const clearJobFilter = () => {
    setJobFilter(null)
    setPage(1)
    setSearchParams((prev) => {
      const params = Object.fromEntries(prev)
      delete params.job; delete params.job_title; delete params.job_company
      params.page = '1'
      return params
    })
  }

  const goPage = (p) => {
    const next = Math.max(1, Math.min(p, totalPages))
    setPage(next)
    setSearchParams((prev) => {
      const params = Object.fromEntries(prev)
      params.page = String(next)
      return params
    })
  }

  const handleStatusChange = async (application, newStatus) => {
    const prevStatus = application.status
    setApplications((prev) =>
      prev.map((a) => (a.id === application.id ? { ...a, status: newStatus } : a))
    )
    try {
      await updateApplicationStatus(application.id, newStatus)
      toast.success(`${application.candidate_name} marked as ${newStatus}`)
    } catch {
      toast.error('Failed to update status')
      setApplications((prev) =>
        prev.map((a) => (a.id === application.id ? { ...a, status: prevStatus } : a))
      )
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Applications</h1>
        <p className="text-gray-500 text-sm mt-1">{total.toLocaleString()} applications</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          className="input w-auto"
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        {jobFilter ? (
          <span className="badge text-sm bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20 gap-2 py-1.5 px-3">
            <Briefcase className="w-3.5 h-3.5" />
            {jobFilter.title}{jobFilter.company && <span className="text-scarlet-400/70"> · {jobFilter.company}</span>}
            <button onClick={clearJobFilter} className="hover:text-white ml-1"><X className="w-3.5 h-3.5" /></button>
          </span>
        ) : (
          <JobFilterCombobox onSelect={onJobFilterSelect} />
        )}
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : applications.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No applications found"
          description="Try a different status filter, or check back once candidates have applied to jobs."
        />
      ) : (
        <>
          <div className="card overflow-hidden">
            <div className="hidden sm:grid sm:grid-cols-12 gap-4 px-5 py-3 border-b border-surface-400 text-xs font-medium text-gray-500 uppercase tracking-wide">
              <div className="col-span-3">Candidate</div>
              <div className="col-span-3">Job</div>
              <div className="col-span-2">Match Score</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-2">Update Status</div>
            </div>
            <div className="divide-y divide-surface-400">
              {applications.map((app) => (
                <div key={app.id} className="px-4 sm:px-5 py-4 hover:bg-surface-600 transition-colors">
                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 sm:gap-4 sm:items-center">
                    <div className="sm:col-span-3 min-w-0">
                      <Link
                        to={`/candidates/${app.candidate}?returnTo=${encodeURIComponent('/applications')}`}
                        className="text-sm font-medium text-white hover:text-scarlet-400 transition-colors truncate block"
                      >
                        {app.candidate_name}
                      </Link>
                    </div>
                    <div className="sm:col-span-3 min-w-0">
                      <Link
                        to={`/jobs/${app.job}?returnTo=${encodeURIComponent('/applications')}`}
                        className="text-sm text-white hover:text-scarlet-400 transition-colors truncate block flex items-center gap-1.5"
                      >
                        <Briefcase className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                        {app.job_title}
                      </Link>
                      <p className="text-xs text-gray-500 truncate">{app.company}</p>
                    </div>
                    <div className="sm:col-span-2">
                      {app.overall_match_score != null && app.match_result_id != null ? (
                        <Link
                          to={`/matching/${app.job}/explain/${app.match_result_id}?returnTo=${encodeURIComponent('/applications')}`}
                          className="text-sm text-gray-300 hover:text-scarlet-400 transition-colors flex items-center gap-1"
                          title="See why this score was given"
                        >
                          {(app.overall_match_score * 100).toFixed(0)}%
                          <BarChart3 className="w-3 h-3 text-gray-500" />
                        </Link>
                      ) : (
                        <span className="text-sm text-gray-300">
                          {app.overall_match_score != null ? `${(app.overall_match_score * 100).toFixed(0)}%` : '—'}
                        </span>
                      )}
                    </div>
                    <div className="sm:col-span-2">
                      <span className={`badge text-xs ${STATUS_STYLES[app.status] ?? 'bg-surface-500 text-gray-400'}`}>
                        {app.status}
                      </span>
                    </div>
                    <div className="sm:col-span-2">
                      <select
                        className="input text-xs py-1.5"
                        value={app.status}
                        onChange={(e) => handleStatusChange(app, e.target.value)}
                      >
                        {STATUS_OPTIONS.filter((o) => o.value).map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button onClick={() => goPage(page - 1)} disabled={page === 1} className="btn-ghost p-2 disabled:opacity-30">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-400">Page {page} of {totalPages.toLocaleString()}</span>
              <button onClick={() => goPage(page + 1)} disabled={page === totalPages} className="btn-ghost p-2 disabled:opacity-30">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
