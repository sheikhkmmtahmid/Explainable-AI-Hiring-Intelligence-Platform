import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Users, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import { getCandidates } from '../api/candidates'

const PAGE_SIZE = 50

const TABS = [
  { key: 'real',      label: 'My Candidates', params: { is_synthetic: false } },
  { key: 'synthetic', label: 'Synthetic',      params: { is_synthetic: true  } },
  { key: 'all',       label: 'All',            params: {}                       },
]

export default function CandidateList() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading]       = useState(true)
  const [search, setSearch]         = useState('')
  const [tab, setTab]               = useState('real')
  const [page, setPage]             = useState(1)
  const [total, setTotal]           = useState(0)

  const tabParams = TABS.find(t => t.key === tab)?.params ?? {}
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const fetch = useCallback(() => {
    setLoading(true)
    getCandidates({
      search: search || undefined,
      page_size: PAGE_SIZE,
      page,
      ...tabParams,
    })
      .then(({ data }) => {
        setCandidates(data.results ?? data)
        setTotal(data.count ?? (data.results ? data.count : (data.results ?? data).length))
      })
      .finally(() => setLoading(false))
  }, [search, tab, page])

  useEffect(() => { fetch() }, [fetch])

  const switchTab = t => { setTab(t); setPage(1); setSearch('') }
  const goPage = p => setPage(Math.max(1, Math.min(p, totalPages)))

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Candidates</h1>
          <p className="text-gray-500 text-sm mt-1">{total.toLocaleString()} profiles</p>
        </div>
        <Link to="/candidates/new" className="btn-primary">
          <Plus className="w-4 h-4" /> Add Candidate
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-surface-700 p-1 rounded-xl w-fit border border-surface-400">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => switchTab(t.key)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.key ? 'bg-scarlet-500 text-white shadow' : 'text-gray-400 hover:text-white'
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
          placeholder="Search by name, title, location…"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
        />
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="py-20" />
      ) : candidates.length === 0 ? (
        <EmptyState
          icon={Users}
          title={tab === 'real' ? 'No candidates added yet' : 'No candidates found'}
          description={tab === 'real' ? 'Add your first candidate to get started.' : 'Try a different filter or search term.'}
          action={tab === 'real' ? <Link to="/candidates/new" className="btn-primary"><Plus className="w-4 h-4" /> Add Candidate</Link> : null}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {candidates.map(c => (
              <Link
                key={c.id}
                to={`/candidates/${c.id}`}
                className="card flex items-center gap-4 px-4 py-4 hover:border-scarlet-500/30 hover:bg-surface-600 transition-all group"
              >
                <div className="w-10 h-10 rounded-full bg-scarlet-500/20 border border-scarlet-500/30 flex items-center justify-center text-sm font-bold text-scarlet-400 flex-shrink-0">
                  {c.full_name?.[0]?.toUpperCase() ?? '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-white group-hover:text-scarlet-400 transition-colors truncate">
                      {c.full_name}
                    </p>
                    {c.is_synthetic && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-surface-500 text-gray-500 flex-shrink-0">synthetic</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 truncate mt-0.5">{c.current_title || 'Candidate'}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-600">{c.years_of_experience}y exp</span>
                    {c.highest_education && <span className="text-xs text-gray-600 capitalize">· {c.highest_education}</span>}
                    {c.country && <span className="text-xs text-gray-600">· {c.country}</span>}
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-scarlet-400 transition-colors flex-shrink-0" />
              </Link>
            ))}
          </div>

          {/* Pagination */}
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
