import { useEffect, useState, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, MapPin, Briefcase, GraduationCap, Pencil, X, Check, Upload, FileCheck, FileText, CheckCircle2, Clock, Trash2 } from 'lucide-react'
import LoadingSpinner from '../components/LoadingSpinner'
import ConfirmDialog from '../components/ConfirmDialog'
import { getCandidate, updateCandidate, deleteCandidate, uploadCV, deleteCV } from '../api/candidates'
import toast from 'react-hot-toast'

const EDUCATION_OPTIONS = [
  { value: 'high_school', label: 'High School' },
  { value: 'associate',   label: 'Associate' },
  { value: 'bachelor',    label: "Bachelor's" },
  { value: 'master',      label: "Master's" },
  { value: 'phd',         label: 'PhD' },
  { value: 'other',       label: 'Other' },
]

const AVAILABILITY_OPTIONS = [
  { value: 'actively_looking', label: 'Actively Looking' },
  { value: 'open',             label: 'Open to Offers' },
  { value: 'not_looking',      label: 'Not Looking' },
]

const REMOTE_OPTIONS = [
  { value: 'onsite',   label: 'On-site' },
  { value: 'remote',   label: 'Remote' },
  { value: 'hybrid',   label: 'Hybrid' },
  { value: 'flexible', label: 'Flexible' },
]

function Field({ label, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export default function CandidateDetail() {
  const { id } = useParams()
  const [candidate, setCandidate] = useState(null)
  const [loading, setLoading]     = useState(true)
  const [editing, setEditing]     = useState(false)
  const [saving, setSaving]       = useState(false)
  const [form, setForm]           = useState({})
  const [uploading, setUploading]     = useState(false)
  const [cvFile, setCvFile]           = useState(null)
  const [dragging, setDragging]       = useState(false)
  const [confirmDelete, setConfirmDelete]   = useState(false)
  const [confirmDeleteCV, setConfirmDeleteCV] = useState(null) // cv object
  const [deleting, setDeleting]       = useState(false)
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    getCandidate(id).then(({ data }) => setCandidate(data)).finally(() => setLoading(false))
  }, [id])

  const startEdit = () => {
    const c = candidate
    setForm({
      full_name:            c.full_name ?? '',
      email:                c.email ?? '',
      phone:                c.phone ?? '',
      city:                 c.city ?? '',
      country:              c.country ?? '',
      current_title:        c.current_title ?? '',
      years_of_experience:  c.years_of_experience ?? '',
      highest_education:    c.highest_education ?? 'bachelor',
      education_field:      c.education_field ?? '',
      availability_status:  c.availability_status ?? 'open',
      remote_preference:    c.remote_preference ?? 'flexible',
      expected_salary_min:  c.expected_salary_min ?? '',
      expected_salary_max:  c.expected_salary_max ?? '',
      salary_currency:      c.salary_currency ?? 'USD',
      summary:              c.summary ?? '',
    })
    setEditing(true)
  }

  const cancelEdit = () => { setEditing(false); setForm({}) }

  const onChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const save = async () => {
    setSaving(true)
    try {
      const { data } = await updateCandidate(id, form)
      setCandidate(data)
      setEditing(false)
      toast.success('Profile updated')
    } catch (err) {
      const d = err.response?.data
      if (d && typeof d === 'object') {
        const key = Object.keys(d)[0]
        const msg = Array.isArray(d[key]) ? d[key][0] : d[key]
        toast.error(`${key}: ${msg}`)
      } else {
        toast.error('Failed to save changes')
      }
    } finally {
      setSaving(false)
    }
  }

  // CV drag-and-drop
  const ACCEPTED = ['.pdf', '.docx', '.txt']
  const pickFile = (file) => {
    if (!file) return
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ACCEPTED.includes(ext)) { toast.error('Only PDF, DOCX, or TXT files are accepted'); return }
    if (file.size > 10 * 1024 * 1024) { toast.error('File must be under 10 MB'); return }
    setCvFile(file)
  }
  const onDragOver  = e => { e.preventDefault(); setDragging(true) }
  const onDragLeave = e => { e.preventDefault(); setDragging(false) }
  const onDrop      = e => { e.preventDefault(); setDragging(false); pickFile(e.dataTransfer.files[0]) }

  const handleUploadCV = async () => {
    if (!cvFile) return
    setUploading(true)
    try {
      await uploadCV(id, cvFile)
      setCvFile(null)
      toast.success('CV uploaded. Parsing skills in background…')
      // Refresh to pick up newly parsed skills
      const { data } = await getCandidate(id)
      setCandidate(data)
    } catch {
      toast.error('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteCandidate = async () => {
    setDeleting(true)
    try {
      await deleteCandidate(id)
      toast.success('Candidate deleted')
      navigate('/candidates')
    } catch {
      toast.error('Failed to delete candidate')
      setDeleting(false)
    }
    setConfirmDelete(false)
  }

  const handleDeleteCV = async () => {
    if (!confirmDeleteCV) return
    try {
      await deleteCV(id, confirmDeleteCV.id)
      setCandidate(c => ({ ...c, cvs: c.cvs.filter(cv => cv.id !== confirmDeleteCV.id) }))
      toast.success('CV removed')
    } catch {
      toast.error('Failed to delete CV')
    }
    setConfirmDeleteCV(null)
  }

  if (loading) return <LoadingSpinner size="lg" className="min-h-[60vh]" />
  if (!candidate) return <p className="text-gray-500">Candidate not found.</p>

  const c = candidate

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <ConfirmDialog
        open={confirmDelete}
        title="Delete Candidate"
        message={`Permanently delete ${candidate?.full_name}? This cannot be undone.`}
        confirmLabel={deleting ? 'Deleting…' : 'Delete'}
        onConfirm={handleDeleteCandidate}
        onCancel={() => setConfirmDelete(false)}
      />
      <ConfirmDialog
        open={!!confirmDeleteCV}
        title="Remove CV"
        message={`Remove "${confirmDeleteCV?.original_filename}"? The file will be permanently deleted.`}
        confirmLabel="Remove"
        onConfirm={handleDeleteCV}
        onCancel={() => setConfirmDeleteCV(null)}
      />

      <Link to="/candidates" className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back</Link>

      {/* ── EDIT MODE ── */}
      {editing ? (
        <>
          <div className="flex items-center justify-between">
            <h1 className="page-title">Edit Candidate</h1>
            <div className="flex gap-2">
              <button onClick={cancelEdit} className="btn-ghost text-sm"><X className="w-4 h-4" /> Cancel</button>
              <button onClick={save} disabled={saving} className="btn-primary text-sm">
                <Check className="w-4 h-4" /> {saving ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>

          {/* Personal */}
          <div className="card p-5 space-y-4">
            <h2 className="section-title">Personal Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Full Name *">
                <input className="input" name="full_name" value={form.full_name} onChange={onChange} required />
              </Field>
              <Field label="Email *">
                <input className="input" type="email" name="email" value={form.email} onChange={onChange} required />
              </Field>
              <Field label="Phone">
                <input className="input" name="phone" value={form.phone} onChange={onChange} />
              </Field>
              <Field label="City">
                <input className="input" name="city" value={form.city} onChange={onChange} />
              </Field>
              <Field label="Country">
                <input className="input" name="country" value={form.country} onChange={onChange} />
              </Field>
              <Field label="Remote Preference">
                <select className="input" name="remote_preference" value={form.remote_preference} onChange={onChange}>
                  {REMOTE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </Field>
            </div>
          </div>

          {/* Professional */}
          <div className="card p-5 space-y-4">
            <h2 className="section-title">Professional Profile</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Field label="Current Title">
                  <input className="input" name="current_title" value={form.current_title} onChange={onChange} placeholder="e.g. Senior Data Scientist" />
                </Field>
              </div>
              <Field label="Years of Experience">
                <input className="input" type="number" min="0" max="50" name="years_of_experience" value={form.years_of_experience} onChange={onChange} />
              </Field>
              <Field label="Highest Education">
                <select className="input" name="highest_education" value={form.highest_education} onChange={onChange}>
                  {EDUCATION_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </Field>
              <Field label="Education Field">
                <input className="input" name="education_field" value={form.education_field} onChange={onChange} placeholder="e.g. Computer Science" />
              </Field>
              <Field label="Availability">
                <select className="input" name="availability_status" value={form.availability_status} onChange={onChange}>
                  {AVAILABILITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </Field>
              <Field label="Expected Salary (Min)">
                <input className="input" type="number" name="expected_salary_min" value={form.expected_salary_min} onChange={onChange} />
              </Field>
              <Field label="Expected Salary (Max)">
                <input className="input" type="number" name="expected_salary_max" value={form.expected_salary_max} onChange={onChange} />
              </Field>
              <Field label="Salary Currency">
                <input className="input" name="salary_currency" value={form.salary_currency} onChange={onChange} placeholder="USD" />
              </Field>
            </div>
            <Field label="Professional Summary">
              <textarea name="summary" rows={4} className="input resize-none" value={form.summary} onChange={onChange}
                placeholder="Brief summary of background and goals…" />
            </Field>
          </div>
        </>
      ) : (

      /* ── VIEW MODE ── */
      <>
        {/* Header */}
        <div className="card p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-scarlet-500/20 border border-scarlet-500/30 flex items-center justify-center text-xl font-bold text-scarlet-400">
                {c.full_name?.[0]?.toUpperCase()}
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">{c.full_name}</h1>
                <p className="text-gray-400 mt-0.5">{c.current_title || 'Candidate'}</p>
                <div className="flex items-center flex-wrap gap-3 mt-2">
                  {c.country && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <MapPin className="w-3 h-3" />{[c.city, c.country].filter(Boolean).join(', ')}
                    </span>
                  )}
                  {c.years_of_experience != null && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <Briefcase className="w-3 h-3" />{c.years_of_experience}y experience
                    </span>
                  )}
                  {c.highest_education && (
                    <span className="flex items-center gap-1 text-xs text-gray-500">
                      <GraduationCap className="w-3 h-3" />{c.highest_education}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={startEdit} className="btn-secondary text-sm">
                <Pencil className="w-4 h-4" /> Edit Profile
              </button>
              <button onClick={() => setConfirmDelete(true)} className="btn-ghost text-sm text-scarlet-400 hover:bg-scarlet-500/10 border border-scarlet-500/20">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {c.summary && (
            <div className="mt-4 pt-4 border-t border-surface-400">
              <p className="text-sm text-gray-400 leading-relaxed">{c.summary}</p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Skills */}
          <div className="card p-5">
            <h2 className="section-title mb-3">Skills</h2>
            {c.skills?.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {c.skills.map(s => (
                  <span key={s.id} className="badge bg-scarlet-500/10 text-scarlet-400 border border-scarlet-500/20 text-xs">
                    {s.skill_name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No skills yet. Upload a CV to auto-extract.</p>
            )}
          </div>

          {/* Details */}
          <div className="card p-5">
            <h2 className="section-title mb-3">Details</h2>
            <dl className="space-y-2">
              {[
                ['Email', c.email],
                ['Phone', c.phone],
                ['Education Field', c.education_field],
                ['Availability', c.availability_status?.replace(/_/g, ' ')],
                ['Remote Preference', c.remote_preference],
                ['Expected Salary', c.expected_salary_min
                  ? `${c.salary_currency ?? 'USD'} ${Number(c.expected_salary_min).toLocaleString()}${c.expected_salary_max ? ' – ' + Number(c.expected_salary_max).toLocaleString() : ''}`
                  : null],
              ].filter(([, v]) => v).map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm gap-4">
                  <dt className="text-gray-500 flex-shrink-0">{k}</dt>
                  <dd className="text-white capitalize text-right">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        {/* Experience */}
        {c.experiences?.length > 0 && (
          <div className="card p-5">
            <h2 className="section-title mb-4">Experience</h2>
            <div className="space-y-4">
              {c.experiences.map(exp => (
                <div key={exp.id} className="flex gap-3">
                  <div className="w-1 rounded-full bg-scarlet-500/40 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-white text-sm">{exp.job_title}</p>
                    <p className="text-xs text-gray-500">{exp.company} · {exp.start_date} – {exp.end_date ?? 'Present'}</p>
                    {exp.description && <p className="text-xs text-gray-400 mt-1">{exp.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CV Upload */}
        <div className="card p-5 space-y-3">
          <h2 className="section-title">Upload New CV</h2>
          <p className="text-xs text-gray-500">Uploading a new CV will re-extract and update the candidate's skills automatically.</p>

          <div
            onDragOver={onDragOver}
            onDragEnter={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex flex-col items-center justify-center w-full h-28 border-2 border-dashed rounded-xl cursor-pointer transition-all select-none
              ${dragging
                ? 'border-scarlet-400 bg-scarlet-500/10 scale-[1.01]'
                : cvFile
                  ? 'border-emerald-500/40 bg-emerald-500/5'
                  : 'border-surface-300 hover:border-scarlet-500/50 hover:bg-scarlet-500/5'
              }`}
          >
            {cvFile ? (
              <>
                <FileCheck className="w-6 h-6 text-emerald-400 mb-2" />
                <span className="text-sm text-emerald-300 font-medium max-w-xs truncate px-4">{cvFile.name}</span>
                <button
                  type="button"
                  onClick={e => { e.stopPropagation(); setCvFile(null) }}
                  className="mt-1.5 text-xs text-gray-500 hover:text-scarlet-400 flex items-center gap-1 transition-colors"
                >
                  <X className="w-3 h-3" /> Remove
                </button>
              </>
            ) : (
              <>
                <Upload className={`w-6 h-6 mb-2 transition-colors ${dragging ? 'text-scarlet-400' : 'text-gray-500'}`} />
                <span className={`text-sm transition-colors ${dragging ? 'text-scarlet-300' : 'text-gray-400'}`}>
                  {dragging ? 'Drop file here' : 'Click to upload or drag & drop'}
                </span>
                <span className="text-xs text-gray-600 mt-1">PDF, DOCX, TXT · max 10 MB</span>
              </>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={e => pickFile(e.target.files[0])}
          />

          {cvFile && (
            <div className="flex justify-end">
              <button onClick={handleUploadCV} disabled={uploading} className="btn-primary text-sm">
                <Upload className="w-4 h-4" /> {uploading ? 'Uploading…' : 'Upload CV'}
              </button>
            </div>
          )}

          {/* Uploaded CV history */}
          {c.cvs?.length > 0 && (
            <div className="mt-2 space-y-2">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Uploaded CVs</p>
              {[...c.cvs].sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at)).map(cv => (
                <div key={cv.id} className="flex items-center justify-between rounded-lg bg-surface-600 border border-surface-400 px-4 py-2.5 gap-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <span className="text-sm text-white truncate">{cv.original_filename}</span>
                    {cv.is_primary && (
                      <span className="badge bg-scarlet-500/15 text-scarlet-400 text-xs flex-shrink-0">Primary</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-xs text-gray-500">
                      {new Date(cv.uploaded_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                    {cv.parsed_at ? (
                      <span className="flex items-center gap-1 text-xs text-emerald-400">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Parsed
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-gold-400">
                        <Clock className="w-3.5 h-3.5" /> Pending
                      </span>
                    )}
                    <button
                      onClick={() => setConfirmDeleteCV(cv)}
                      className="text-gray-600 hover:text-scarlet-400 transition-colors ml-1"
                      title="Remove CV"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
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
