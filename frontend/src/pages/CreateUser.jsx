import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, UserPlus, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import { createUser } from '../api/users'
import { useAuth } from '../context/AuthContext'

/*
  Task 7:  Admin can create admin, recruiter (manager), or candidate (employee)
  Task 8:  Manager (recruiter) can create recruiter or candidate
  Task 10: This page is reachable via a "Create New User" button in the sidebar
           (visible only to admin and manager)
*/

// Role options per actor role
const ROLE_OPTIONS = {
  admin: [
    { value: 'admin',     label: 'Admin' },
    { value: 'recruiter', label: 'Manager (Recruiter)' },
    { value: 'candidate', label: 'Employee (Candidate)' },
    { value: 'analyst',   label: 'Analyst' },
  ],
  recruiter: [
    { value: 'recruiter', label: 'Manager (Recruiter)' },
    { value: 'candidate', label: 'Employee (Candidate)' },
  ],
}

export default function CreateUser() {
  const { user: actor } = useAuth()
  const navigate = useNavigate()

  const roleOptions = ROLE_OPTIONS[actor?.role] ?? []

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: roleOptions[0]?.value ?? '',
    organization_name: '',
    phone: '',
    country: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)

  // Guard: only admin and recruiter/manager can access this page
  if (!actor || !['admin', 'recruiter'].includes(actor.role)) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <p className="text-lg font-medium">Access denied</p>
        <p className="text-sm mt-1">You do not have permission to create users.</p>
        <Link to="/" className="mt-4 text-scarlet-400 hover:underline text-sm">Go to Dashboard</Link>
      </div>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createUser(form)
      toast.success(`User "${form.username}" created as ${form.role}`)
      navigate('/tasks')
    } catch (err) {
      const errors = err?.response?.data
      if (errors && typeof errors === 'object') {
        const msg = Object.entries(errors)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ')
        toast.error(msg)
      } else {
        toast.error('Failed to create user')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="rounded-lg p-2 text-gray-400 hover:bg-surface-700 hover:text-white transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">Create New User</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {actor.role === 'admin'
              ? 'You can create admin, manager, or employee accounts.'
              : 'You can create manager or employee accounts.'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 rounded-xl border border-surface-400 bg-surface-800 p-6">

        {/* Role — Task 7 & 8: options differ by actor role */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-300">
            Role <span className="text-red-400">*</span>
          </label>
          <select
            required
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white focus:border-scarlet-500 focus:outline-none"
          >
            {roleOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">
              Username <span className="text-red-400">*</span>
            </label>
            <input
              required
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              placeholder="johndoe"
              className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">
              Email <span className="text-red-400">*</span>
            </label>
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="john@example.com"
              className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-300">
            Password <span className="text-red-400">*</span>
          </label>
          <div className="relative">
            <input
              required
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Min. 8 characters"
              className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 pr-10 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          {actor.is_platform_staff && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-300">Organization</label>
              <input
                value={form.organization_name}
                onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
                placeholder="Company name (existing or new)"
                className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
              />
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">Country</label>
            <input
              value={form.country}
              onChange={(e) => setForm({ ...form, country: e.target.value })}
              placeholder="Bangladesh"
              className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="rounded-lg border border-surface-400 px-4 py-2 text-sm text-gray-300 hover:bg-surface-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-lg bg-scarlet-600 px-4 py-2 text-sm font-medium text-white hover:bg-scarlet-700 disabled:opacity-60 transition-colors"
          >
            {saving ? 'Creating…' : <><UserPlus size={15} /> Create User</>}
          </button>
        </div>
      </form>
    </div>
  )
}
