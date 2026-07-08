import { useEffect, useRef, useState } from 'react'
import { Briefcase, Search } from 'lucide-react'
import { getJobsWithCounts } from '../api/applications'

/**
 * Searchable job picker for the Applications list -- built for a
 * non-technical recruiter: shows job title + company + applicant count per
 * option (not a bare ID), defaults to the busiest jobs first (relevance,
 * not an alphabetical firehose), and only lists jobs that actually have
 * applicants.
 */
export default function JobFilterCombobox({ onSelect, placeholder = 'Filter by job…' }) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState([])
  const [open, setOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    getJobsWithCounts(query.trim()).then(({ data }) => setOptions(data)).catch(() => setOptions([]))
  }, [query])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  return (
    <div ref={containerRef} className="relative w-full sm:w-80">
      <div className="relative">
        <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          className="input pl-9"
          value={query}
          placeholder={placeholder}
          onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
        />
      </div>
      {open && (
        <div className="absolute z-20 mt-1 w-full card max-h-72 overflow-y-auto shadow-lg">
          {options.length === 0 ? (
            <p className="px-3 py-2 text-xs text-gray-500">No jobs with applicants match "{query}".</p>
          ) : (
            options.map((job) => (
              <button
                type="button"
                key={job.id}
                onClick={() => { onSelect(job); setQuery(''); setOpen(false) }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-surface-600 transition-colors flex items-center justify-between gap-3"
              >
                <span className="flex items-center gap-2 min-w-0">
                  <Briefcase className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                  <span className="truncate">
                    <span className="text-white">{job.title}</span>
                    <span className="text-gray-500"> · {job.company}</span>
                  </span>
                </span>
                <span className="text-xs text-gray-500 flex-shrink-0">{job.applicant_count} applicant{job.applicant_count === 1 ? '' : 's'}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
