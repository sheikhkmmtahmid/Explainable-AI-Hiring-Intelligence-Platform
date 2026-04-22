import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { createJob } from '../api/jobs'
import toast from 'react-hot-toast'

const FIELD = ({ label, name, form, onChange, type = 'text', required = false, className = '' }) => (
  <div className={className}>
    <label className="label">{label}{required && <span className="text-scarlet-400 ml-1">*</span>}</label>
    <input className="input" type={type} name={name} value={form[name] ?? ''} onChange={onChange} required={required} />
  </div>
)

export default function JobCreate() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '', company: '', description: '', requirements: '', responsibilities: '',
    country: '', city: '', region: '', work_model: 'onsite',
    employment_type: 'full_time', experience_level: 'mid',
    salary_min: '', salary_max: '', salary_currency: 'USD',
    industry: '', status: 'active',
  })
  const [loading, setLoading] = useState(false)

  const onChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        ...form,
        salary_min: form.salary_min !== '' ? Number(form.salary_min) : null,
        salary_max: form.salary_max !== '' ? Number(form.salary_max) : null,
      }
      const { data } = await createJob(payload)
      toast.success('Job posted successfully')
      navigate(`/jobs/${data.id}`)
    } catch (err) {
      const d = err.response?.data
      if (d && typeof d === 'object') {
        const key = Object.keys(d)[0]
        const msg = Array.isArray(d[key]) ? d[key][0] : d[key]
        toast.error(`${key}: ${msg}`)
      } else {
        toast.error(typeof d === 'string' ? d : 'Failed to create job')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Link to="/jobs" className="btn-ghost text-sm"><ArrowLeft className="w-4 h-4" /> Back</Link>
      </div>

      <div>
        <h1 className="page-title">Post a New Job</h1>
        <p className="text-gray-500 text-sm mt-1">Fill in the details. Embeddings will be generated automatically.</p>
      </div>

      <form onSubmit={submit} className="space-y-6">
        {/* Core */}
        <div className="card p-5 space-y-4">
          <h2 className="section-title">Job Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <FIELD label="Job Title" name="title" form={form} onChange={onChange} required className="col-span-2" />
            <FIELD label="Company" name="company" form={form} onChange={onChange} required />
            <FIELD label="Industry" name="industry" form={form} onChange={onChange} />
          </div>
          <div>
            <label className="label">Description <span className="text-scarlet-400">*</span></label>
            <textarea
              name="description" rows={5} required
              className="input resize-none"
              value={form.description}
              onChange={onChange}
              placeholder="Describe the role, responsibilities, and what you're looking for…"
            />
          </div>
          <div>
            <label className="label">Requirements</label>
            <p className="text-xs text-gray-500 mb-1">Enter one requirement per line. Skills listed here are used for candidate matching.</p>
            <textarea name="requirements" rows={5} className="input resize-none font-mono text-xs" value={form.requirements} onChange={onChange}
              placeholder={"Python (3+ years)\nMachine learning with scikit-learn or XGBoost\nSQL and data pipeline experience\nFamiliarity with AWS or cloud platforms\nExperience with NLP or entity resolution"} />
          </div>
          <div>
            <label className="label">Responsibilities</label>
            <p className="text-xs text-gray-500 mb-1">Enter one responsibility per line.</p>
            <textarea name="responsibilities" rows={4} className="input resize-none font-mono text-xs" value={form.responsibilities} onChange={onChange}
              placeholder={"Build and deploy predictive models\nCollaborate with engineering on MLOps pipelines\nPresent findings to non-technical stakeholders\nEnsure model explainability and regulatory compliance"} />
          </div>
        </div>

        {/* Location & Type */}
        <div className="card p-5 space-y-4">
          <h2 className="section-title">Location & Type</h2>
          <div className="grid grid-cols-3 gap-4">
            <FIELD label="City" name="city" form={form} onChange={onChange} />
            <FIELD label="Region / State" name="region" form={form} onChange={onChange} />
            <FIELD label="Country" name="country" form={form} onChange={onChange} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">Work Model</label>
              <select name="work_model" className="input" value={form.work_model} onChange={onChange}>
                <option value="onsite">On-site</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>
            <div>
              <label className="label">Employment Type</label>
              <select name="employment_type" className="input" value={form.employment_type} onChange={onChange}>
                <option value="full_time">Full-time</option>
                <option value="part_time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </select>
            </div>
            <div>
              <label className="label">Experience Level</label>
              <select name="experience_level" className="input" value={form.experience_level} onChange={onChange}>
                <option value="entry">Entry</option>
                <option value="mid">Mid</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
                <option value="executive">Executive</option>
              </select>
            </div>
          </div>
        </div>

        {/* Salary */}
        <div className="card p-5 space-y-4">
          <h2 className="section-title">Compensation</h2>
          <div className="grid grid-cols-3 gap-4">
            <FIELD label="Min Salary" name="salary_min" form={form} onChange={onChange} type="number" />
            <FIELD label="Max Salary" name="salary_max" form={form} onChange={onChange} type="number" />
            <div>
              <label className="label">Currency</label>
              <select name="salary_currency" className="input" value={form.salary_currency} onChange={onChange}>
                <option>USD</option><option>EUR</option><option>GBP</option><option>BDT</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <Link to="/jobs" className="btn-secondary">Cancel</Link>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Posting…' : 'Post Job'}
          </button>
        </div>
      </form>
    </div>
  )
}
