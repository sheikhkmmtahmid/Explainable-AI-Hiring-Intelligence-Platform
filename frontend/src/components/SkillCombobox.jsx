import { useEffect, useRef, useState } from 'react'
import { Plus, Search, X } from 'lucide-react'
import { searchSkills, proposeSkill } from '../api/taxonomy'
import toast from 'react-hot-toast'

/**
 * Multi-select skill picker: typeahead against the shared SkillTaxonomy,
 * plus an "add new" path for anything not found. New names are usable on
 * the job immediately (skills are free-text on JobSkillRequirement) but are
 * also queued as PendingSkill server-side so the taxonomy stays curated and
 * de-duplicated instead of drifting from ad hoc spelling variants.
 *
 * value: string[] of skill names already selected.
 * onChange: (nextValue: string[]) => void
 */
export default function SkillCombobox({ value = [], onChange, placeholder = 'Search or add a skill…' }) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState([])
  const [searching, setSearching] = useState(false)
  const [open, setOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    const q = query.trim()
    if (!q) { setOptions([]); setSearching(false); return }
    // While results for the current query are still loading, hide the "add
    // new" fallback -- otherwise it flashes before the real match arrives
    // and a quick click can propose a skill that already exists.
    setSearching(true)
    const timer = setTimeout(() => {
      searchSkills(q)
        .then(({ data }) => setOptions(data.results ?? data))
        .catch(() => setOptions([]))
        .finally(() => setSearching(false))
    }, 200)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    const onClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const isSelected = (name) => value.some((v) => v.toLowerCase() === name.toLowerCase())

  const addSkill = (name) => {
    if (!name.trim() || isSelected(name)) return
    onChange([...value, name.trim()])
    setQuery('')
    setOptions([])
  }

  const removeSkill = (name) => {
    onChange(value.filter((v) => v.toLowerCase() !== name.toLowerCase()))
  }

  const handleAddNew = async () => {
    const name = query.trim()
    if (!name) return
    setSubmitting(true)
    try {
      const { data } = await proposeSkill(name)
      if (data.status === 'existing') {
        addSkill(data.skill.canonical_name)
        toast.success(`"${data.skill.canonical_name}" already exists in the skill library — added.`)
      } else if (data.status === 'possible_duplicate') {
        addSkill(name)
        const similar = data.pending_skill?.similar_existing_skill?.canonical_name
        toast(`Added "${name}". It looks similar to "${similar}" — flagged for a moderator to review.`, { icon: '⚠️' })
      } else {
        addSkill(name)
        toast.success(`Added "${name}". Submitted to the skill library for review.`)
      }
    } catch {
      addSkill(name)
      toast.error('Could not check the skill library, but added it to this job anyway.')
    } finally {
      setSubmitting(false)
    }
  }

  const exactOptionMatch = options.some((o) => o.canonical_name.toLowerCase() === query.trim().toLowerCase())

  return (
    <div ref={containerRef} className="relative">
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {value.map((name) => (
            <span key={name} className="badge text-xs bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20 gap-1">
              {name}
              <button type="button" onClick={() => removeSkill(name)} className="hover:text-white">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="relative">
        <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          className="input pl-9"
          value={query}
          placeholder={placeholder}
          onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key !== 'Enter' || searching || !query.trim()) return
            e.preventDefault()
            const exact = options.find((o) => o.canonical_name.toLowerCase() === query.trim().toLowerCase())
            if (exact) addSkill(exact.canonical_name)
            else if (options.length > 0) addSkill(options[0].canonical_name)
            else handleAddNew()
          }}
        />
      </div>

      {open && query.trim() && (
        <div className="absolute z-20 mt-1 w-full card max-h-64 overflow-y-auto shadow-lg">
          {searching ? (
            <p className="px-3 py-2 text-xs text-gray-500">Searching…</p>
          ) : (
            <>
              {options.map((o) => (
                <button
                  type="button"
                  key={o.id}
                  disabled={isSelected(o.canonical_name)}
                  onClick={() => { addSkill(o.canonical_name); setOpen(false) }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-surface-600 transition-colors flex items-center justify-between disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span>{o.canonical_name}</span>
                  <span className="text-xs text-gray-500">{o.category}</span>
                </button>
              ))}
              {/* Only offered once the current query's own results are in
                  (not while a slower earlier fetch might still resolve) --
                  otherwise a quick click could propose a skill that already
                  exists, right before its matching option would have appeared. */}
              {!exactOptionMatch && (
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => { handleAddNew(); setOpen(false) }}
                  className="w-full text-left px-3 py-2 text-sm text-scarlet-400 hover:bg-surface-600 transition-colors flex items-center gap-1.5 border-t border-surface-400"
                >
                  <Plus className="w-3.5 h-3.5" /> Add "{query.trim()}" as a new skill
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
