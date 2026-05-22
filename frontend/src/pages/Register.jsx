import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import client from '../api/client'
import LogoIcon from '../components/LogoIcon'

/*
  Task 9:  Without authentication, new user can be created with default role 'Employee' (candidate).
           The backend enforces this — the role field is ignored and always set to candidate.
  Task 10: A "Create New User" button on this page links to /users/create for admins/managers
           who are already logged in and want to create non-employee accounts.
*/

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    organisation: '',
    country: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await client.post('/auth/register/', { ...form, role: 'candidate' })
      toast.success('Account created! Please log in.')
      navigate('/login')
    } catch (err) {
      const errors = err?.response?.data
      if (errors && typeof errors === 'object') {
        const msg = Object.entries(errors)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join(' | ')
        toast.error(msg)
      } else {
        toast.error('Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-900 px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <LogoIcon className="h-10 w-10" />
          <h1 className="text-2xl font-bold text-white">Create Account</h1>
          <p className="text-sm text-gray-400">
            New accounts are created as <span className="font-medium text-white">Employee</span> by default.
          </p>
        </div>

        {/* Task 10: "Create New User" button — for admin/manager already signed in */}
        <div className="rounded-lg border border-scarlet-500/30 bg-scarlet-500/10 px-4 py-3 text-sm text-gray-300">
          <span className="font-medium text-white">Admin or Manager?</span> Use the{' '}
          <Link to="/users/create" className="font-medium text-scarlet-400 hover:underline">
            Create New User
          </Link>{' '}
          page to create accounts with manager or admin roles.
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-xl border border-surface-400 bg-surface-800 p-6 shadow-xl"
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-300">Organisation</label>
              <input
                value={form.organisation}
                onChange={(e) => setForm({ ...form, organisation: e.target.value })}
                placeholder="Optional"
                className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-300">Country</label>
              <input
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
                placeholder="Optional"
                className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-scarlet-600 py-2.5 text-sm font-semibold text-white hover:bg-scarlet-700 disabled:opacity-60 transition-colors"
          >
            {loading ? 'Creating account…' : 'Create Account'}
          </button>

          <p className="text-center text-sm text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-scarlet-400 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
