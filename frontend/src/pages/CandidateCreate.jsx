import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Upload, FileCheck, X } from 'lucide-react'
import { createCandidate, uploadCV } from '../api/candidates'
import toast from 'react-hot-toast'

export default function CandidateCreate() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '', email: '', phone: '', current_title: '',
    years_of_experience: '', highest_education: 'bachelor',
    country: '', city: '', summary: '',
    availability_status: 'actively_looking',
    expected_salary_min: '', expected_salary_max: '', salary_currency: 'USD',
  })
  const [cvFile, setCvFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef(null)

  const ACCEPTED = ['.pdf', '.docx', '.txt']
  const pickFile = (file) => {
    if (!file) return
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ACCEPTED.includes(ext)) { toast.error('Only PDF, DOCX, or TXT files are accepted'); return }
    if (file.size > 10 * 1024 * 1024) { toast.error('File must be under 10 MB'); return }
    setCvFile(file)
  }

  const onDragOver  = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = (e) => { e.preventDefault(); setDragging(false) }
  const onDrop      = (e) => { e.preventDefault(); setDragging(false); pickFile(e.dataTransfer.files[0]) }

  const onChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data: candidate } = await createCandidate(form)
      if (cvFile) {
        await uploadCV(candidate.id, cvFile)
        toast.success('Candidate added and CV uploaded. Parsing in background…')
      } else {
        toast.success('Candidate added successfully')
      }
      navigate(`/candidates/${candidate.id}`)
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        // Extract first field error from DRF validation response
        const firstKey = Object.keys(data)[0]
        const firstMsg = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey]
        toast.error(`${firstKey}: ${firstMsg}`)
      } else {
        toast.error(typeof data === 'string' ? data : 'Failed to create candidate')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <Link to="/candidates" className="btn-ghost text-sm inline-flex"><ArrowLeft className="w-4 h-4" /> Back</Link>

      <div>
        <h1 className="page-title">Add Candidate</h1>
        <p className="text-gray-500 text-sm mt-1">Create a candidate profile and optionally upload a CV.</p>
      </div>

      <form onSubmit={submit} className="space-y-6">
        {/* Personal */}
        <div className="card p-5 space-y-4">
          <h2 className="section-title">Personal Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="label">Full Name <span className="text-scarlet-400">*</span></label>
              <input className="input" name="full_name" value={form.full_name} onChange={onChange} required />
            </div>
            <div>
              <label className="label">Email <span className="text-scarlet-400">*</span></label>
              <input className="input" type="email" name="email" value={form.email} onChange={onChange} required />
            </div>
            <div>
              <label className="label">Phone</label>
              <input className="input" name="phone" value={form.phone} onChange={onChange} />
            </div>
            <div>
              <label className="label">City</label>
              <input className="input" name="city" value={form.city} onChange={onChange} />
            </div>
            <div>
              <label className="label">Country</label>
              <input className="input" name="country" value={form.country} onChange={onChange} />
            </div>
          </div>
        </div>

        {/* Professional */}
        <div className="card p-5 space-y-4">
          <h2 className="section-title">Professional Profile</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="label">Current Title</label>
              <input className="input" name="current_title" value={form.current_title} onChange={onChange} placeholder="e.g. Senior Software Engineer" />
            </div>
            <div>
              <label className="label">Years of Experience</label>
              <input className="input" type="number" min="0" max="50" name="years_of_experience" value={form.years_of_experience} onChange={onChange} />
            </div>
            <div>
              <label className="label">Highest Education</label>
              <select name="highest_education" className="input" value={form.highest_education} onChange={onChange}>
                <option value="high_school">High School</option>
                <option value="associate">Associate</option>
                <option value="bachelor">Bachelor</option>
                <option value="master">Master</option>
                <option value="phd">PhD</option>
              </select>
            </div>
            <div>
              <label className="label">Availability</label>
              <select name="availability_status" className="input" value={form.availability_status} onChange={onChange}>
                <option value="actively_looking">Actively Looking</option>
                <option value="open">Open to Offers</option>
                <option value="not_looking">Not Looking</option>
              </select>
            </div>
            <div>
              <label className="label">Expected Salary (Min)</label>
              <input className="input" type="number" name="expected_salary_min" value={form.expected_salary_min} onChange={onChange} />
            </div>
          </div>
          <div>
            <label className="label">Professional Summary</label>
            <textarea name="summary" rows={4} className="input resize-none" value={form.summary} onChange={onChange}
              placeholder="Brief summary of the candidate's background and goals…" />
          </div>
        </div>

        {/* CV Upload */}
        <div className="card p-5 space-y-3">
          <h2 className="section-title">CV / Resume</h2>
          <p className="text-xs text-gray-500">Upload a PDF, DOCX, or TXT file. Skills will be auto-extracted.</p>

          <div
            onDragOver={onDragOver}
            onDragEnter={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-all select-none
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
        </div>

        <div className="flex justify-end gap-3">
          <Link to="/candidates" className="btn-secondary">Cancel</Link>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Saving…' : 'Add Candidate'}
          </button>
        </div>
      </form>
    </div>
  )
}
