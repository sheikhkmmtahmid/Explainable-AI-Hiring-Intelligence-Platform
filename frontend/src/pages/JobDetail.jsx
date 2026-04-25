import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, MapPin, Briefcase, Zap, BarChart3, ChevronRight, RefreshCw, Pencil, Trash2, X, Check } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ConfirmDialog from '../components/ConfirmDialog'
import ScoreBar from '../components/ScoreBar'
import { getJob, updateJob, deleteJob } from '../api/jobs'
import { triggerMatching, getTopCandidates } from '../api/matching'
import toast from 'react-hot-toast'

const TextAsList = ({ text }) => {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean)
  if (lines.length <= 1) return <p className="text-sm text-gray-400 leading-relaxed">{text}</p>
  return (
    <ul className="space-y-1.5">
      {lines.map((line, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
          <span className="text-scarlet-500 mt-1.5 flex-shrink-0 w-1 h-1 rounded-full bg-scarlet-500 inline-block" />
          <span className="leading-relaxed">{line.replace(/^[-*•]\s*/, '')}</span>
        </li>
      ))}
    </ul>
  )
}

const SEL = ({ label, name, form, onChange, children }) => (
  <div>
    <label className="label">{label}</label>
    <select name={name} className="input" value={form[name] ?? ''} onChange={onChange}>{children}</select>
  </div>
)
const INP = ({ label, name, form, onChange, type = 'text', required = false, className = '' }) => (
  <div className={className}>
    <label className="label">{label}{required && <span className="text-scarlet-400 ml-1">*</span>}</label>
    <input className="input" type={type} name={name} value={form[name] ?? ''} onChange={onChange} required={required} />
  </div>
)

export default function JobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [job, setJob]               = useState(null)
  const [matches, setMatches]       = useState([])
  const [loadingJob, setLoadingJob] = useState(true)
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [editing, setEditing]       = useState(false)
  const [saving, setSaving]         = useState(false)
  const [form, setForm]             = useState({})
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting]     = useState(false)

  useEffect(() => {
    getJob(id).then(({ data }) => setJob(data)).finally(() => setLoadingJob(false))
    fetchMatches()
  }, [id])

  const fetchMatches = () => {
    setLoadingMatches(true)
    getTopCandidates(id, 20).then(({ data }) => setMatches(data)).catch(() => {}).finally(() => setLoadingMatches(false))
  }

  const handleTrigger = async () => {
    setTriggering(true)
    try {
      await triggerMatching(id)
      toast.success('Matching queued! Results will appear shortly.')
      setTimeout(fetchMatches, 3000)
    } catch { toast.error('Failed to trigger matching') }
    finally { setTriggering(false) }
  }

  const startEdit = () => {
    setForm({
      title:            job.title ?? '',
      company:          job.company ?? '',
      description:      job.description ?? '',
      requirements:     job.requirements ?? '',
      responsibilities: job.responsibilities ?? '',
      country:          job.country ?? '',
      city:             job.city ?? '',
      region:           job.region ?? '',
      work_model:       job.work_model ?? 'onsite',
      employment_type:  job.employment_type ?? 'full_time',
      experience_level: job.experience_level ?? 'mid',
      industry:         job.industry ?? '',
      salary_min:       job.salary_min ?? '',
      salary_max:       job.salary_max ?? '',
      salary_currency:  job.salary_currency ?? 'USD',
      status:           job.status ?? 'active',
    })
    setEditing(true)
  }

  const cancelEdit = () => setEditing(false)
  const onChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const save = async () => {
    setSaving(true)
    try {
      const payload = {
        ...form,
        salary_min: form.salary_min !== '' ? Number(form.salary_min) : null,
        salary_max: form.salary_max !== '' ? Number(form.salary_max) : null,
      }
      const { data } = await updateJob(id, payload)
      setJob(data)
      setEditing(false)
      toast.success('Job updated')
    } catch (err) {
      const d = err.response?.data
      if (d && typeof d === 'object') {
        const key = Object.keys(d)[0]
        toast.error(`${key}: ${Array.isArray(d[key]) ? d[key][0] : d[key]}`)
      } else { toast.error('Failed to save') }
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteJob(id)
      toast.success('Job deleted')
      navigate('/jobs')
    } catch { toast.error('Failed to delete job'); setDeleting(false) }
    setConfirmDelete(false)
  }

  if (loadingJob) return <LoadingSpinner size="lg" className="min-h-[60vh]" />
  if (!job) return <p className="text-gray-500">Job not found.</p>

  return (
    <div className="space-y-6 animate-fade-in">
      <ConfirmDialog
        open={confirmDelete}
        title="Delete Job"
        message={`Permanently delete "${job.title}" at ${job.company}? All match results will also be removed.`}
        confirmLabel={deleting ? 'Deleting…' : 'Delete Job'}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(false)}
      />

      <Link to="/jobs" className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back to Jobs</Link>

      {/* ── EDIT MODE ── */}
      {editing ? (
        <>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h1 className="page-title">Edit Job</h1>
            <div className="flex gap-2">
              <button onClick={cancelEdit} className="btn-ghost text-sm"><X className="w-4 h-4" /> Cancel</button>
              <button onClick={save} disabled={saving} className="btn-primary text-sm">
                <Check className="w-4 h-4" /> {saving ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>

          <div className="card p-5 space-y-4">
            <h2 className="section-title">Job Details</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <INP label="Job Title" name="title" form={form} onChange={onChange} required className="sm:col-span-2" />
              <INP label="Company"  name="company" form={form} onChange={onChange} required />
              <INP label="Industry" name="industry" form={form} onChange={onChange} />
            </div>
            <div>
              <label className="label">Description <span className="text-scarlet-400">*</span></label>
              <textarea name="description" rows={5} required className="input resize-none" value={form.description} onChange={onChange} />
            </div>
            <div>
              <label className="label">Requirements</label>
              <p className="text-xs text-gray-500 mb-1">One requirement per line. Skills listed here are used for candidate matching.</p>
              <textarea name="requirements" rows={5} className="input resize-none font-mono text-xs" value={form.requirements} onChange={onChange}
                placeholder={"Python (3+ years)\nMachine learning with scikit-learn or XGBoost\nSQL and data pipeline experience\nFamiliarity with AWS or cloud platforms"} />
            </div>
            <div>
              <label className="label">Responsibilities</label>
              <p className="text-xs text-gray-500 mb-1">One responsibility per line.</p>
              <textarea name="responsibilities" rows={4} className="input resize-none font-mono text-xs" value={form.responsibilities} onChange={onChange}
                placeholder={"Build and deploy predictive models\nCollaborate with engineering on MLOps pipelines\nEnsure model explainability and compliance"} />
            </div>
          </div>

          <div className="card p-5 space-y-4">
            <h2 className="section-title">Location & Type</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <INP label="City"   name="city"    form={form} onChange={onChange} />
              <INP label="Region" name="region"  form={form} onChange={onChange} />
              <INP label="Country" name="country" form={form} onChange={onChange} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <SEL label="Work Model" name="work_model" form={form} onChange={onChange}>
                <option value="onsite">On-site</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
              </SEL>
              <SEL label="Employment Type" name="employment_type" form={form} onChange={onChange}>
                <option value="full_time">Full-time</option>
                <option value="part_time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </SEL>
              <SEL label="Experience Level" name="experience_level" form={form} onChange={onChange}>
                <option value="entry">Entry</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="executive">Executive</option>
              </SEL>
            </div>
          </div>

          <div className="card p-5 space-y-4">
            <h2 className="section-title">Compensation & Status</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <INP label="Min Salary" name="salary_min" form={form} onChange={onChange} type="number" />
              <INP label="Max Salary" name="salary_max" form={form} onChange={onChange} type="number" />
              <SEL label="Currency" name="salary_currency" form={form} onChange={onChange}>
                <option>USD</option><option>EUR</option><option>GBP</option><option>BDT</option>
              </SEL>
              <SEL label="Status" name="status" form={form} onChange={onChange}>
                <option value="active">Active</option>
                <option value="closed">Closed</option>
                <option value="draft">Draft</option>
              </SEL>
            </div>
          </div>
        </>
      ) : (

      /* ── VIEW MODE ── */
      <>
        {/* Header */}
        <div className="card p-6">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-surface-500 flex items-center justify-center flex-shrink-0">
                <Briefcase className="w-6 h-6 text-gray-400" />
              </div>
              <div className="min-w-0">
                <h1 className="text-xl font-bold text-white">{job.title}</h1>
                <p className="text-gray-400 mt-0.5">{job.company}</p>
                <div className="flex items-center flex-wrap gap-2 mt-2">
                  {(job.city || job.country) && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <MapPin className="w-3 h-3" /> {[job.city, job.country].filter(Boolean).join(', ')}
                    </span>
                  )}
                  <span className="badge bg-surface-500 text-gray-400 capitalize">{job.work_model}</span>
                  <span className="badge bg-surface-500 text-gray-400 capitalize">{job.employment_type?.replace('_', ' ')}</span>
                  <span className="badge bg-surface-500 text-gray-400 capitalize">{job.experience_level}</span>
                  {job.salary_min && (
                    <span className="text-xs text-gray-500">
                      {job.salary_currency} {Number(job.salary_min).toLocaleString()}–{Number(job.salary_max).toLocaleString()}
                    </span>
                  )}
                  <span className={`badge text-xs ${job.status === 'active' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-surface-500 text-gray-400'}`}>
                    {job.status}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 flex-shrink-0">
              <button onClick={fetchMatches} className="btn-secondary text-sm"><RefreshCw className="w-4 h-4" /></button>
              <button onClick={handleTrigger} disabled={triggering} className="btn-primary text-sm">
                <Zap className="w-4 h-4" /> {triggering ? 'Queuing…' : 'Run Matching'}
              </button>
              <button onClick={startEdit} className="btn-secondary text-sm"><Pencil className="w-4 h-4" /> Edit</button>
              <button onClick={() => setConfirmDelete(true)} className="btn-ghost text-sm text-scarlet-400 hover:bg-scarlet-500/10 border border-scarlet-500/20">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {job.skill_requirements?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-surface-400">
              <p className="text-xs font-medium text-gray-500 mb-2">Required Skills</p>
              <div className="flex flex-wrap gap-1.5">
                {job.skill_requirements.map(s => (
                  <span key={s.id} className={`badge text-xs ${s.is_required ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20' : 'bg-surface-500 text-gray-400'}`}>
                    {s.skill_name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Description / Requirements / Responsibilities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-5">
            <h2 className="section-title mb-3">Description</h2>
            <p className="text-sm text-gray-400 leading-relaxed whitespace-pre-line">{job.description}</p>
          </div>
          <div className="space-y-4">
            {job.requirements && (
              <div className="card p-5">
                <h2 className="section-title mb-3">Requirements</h2>
                <TextAsList text={job.requirements} />
              </div>
            )}
            {job.responsibilities && (
              <div className="card p-5">
                <h2 className="section-title mb-3">Responsibilities</h2>
                <TextAsList text={job.responsibilities} />
              </div>
            )}
          </div>
        </div>

        {/* Top candidates */}
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-surface-400">
            <div>
              <h2 className="section-title">Top Matched Candidates</h2>
              <p className="text-xs text-gray-500 mt-0.5">Ranked by overall match score</p>
            </div>
            <Link to={`/matching/${id}`} className="text-xs text-scarlet-400 hover:text-scarlet-300 flex items-center gap-1 font-medium">
              Full report <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          {loadingMatches ? (
            <LoadingSpinner className="py-12" />
          ) : matches.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-sm">No match results yet.</p>
              <p className="text-gray-600 text-xs mt-1">Click "Run Matching" to rank candidates for this job.</p>
            </div>
          ) : (
            <div className="divide-y divide-surface-400">
              {matches.slice(0, 10).map((m, i) => (
                <div key={m.id} className="px-5 py-4 hover:bg-surface-600 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-7 h-7 rounded-full bg-scarlet-500/20 border border-scarlet-500/30 flex items-center justify-center text-xs font-bold text-scarlet-400 flex-shrink-0">
                        {i + 1}
                      </div>
                      <Link to={`/candidates/${m.candidate}`} className="text-sm font-medium text-white hover:text-scarlet-400 transition-colors">
                        {m.candidate_name}
                      </Link>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className={`text-lg font-bold ${m.overall_score >= 0.7 ? 'text-emerald-400' : m.overall_score >= 0.4 ? 'text-gold-400' : 'text-scarlet-400'}`}>
                        {(m.overall_score * 100).toFixed(0)}%
                      </span>
                      <Link to={`/matching/${id}/explain/${m.id}`} className="btn-ghost text-xs py-1 px-2">
                        <BarChart3 className="w-3 h-3" /> Explain
                      </Link>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <ScoreBar label="Semantic"    value={m.semantic_score}      color="scarlet" />
                    <ScoreBar label="Skills"      value={m.skill_overlap_score} color="gold" />
                    <ScoreBar label="Experience"  value={m.experience_score}    color="blue" />
                    <ScoreBar label="Education"   value={m.education_score}     color="purple" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </>
      )}
    </div>
  )
}
