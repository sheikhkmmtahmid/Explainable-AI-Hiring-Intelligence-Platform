import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import LogoIcon from '../components/LogoIcon'
import toast from 'react-hot-toast'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)

  const fillDemo = () => setForm({ username: 'admin', password: 'admin1234' })

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/')
    } catch {
      toast.error('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center px-4">
      {/* Background glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-scarlet-500/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex mb-4">
            <LogoIcon size={56} />
          </div>
          <h1 className="text-2xl font-bold text-white">HiringAI</h1>
          <p className="text-sm text-gray-500 mt-1">Explainable Hiring Intelligence Platform</p>
        </div>

        {/* Demo credentials banner */}
        <div className="mb-4 rounded-lg border border-scarlet-500/30 bg-scarlet-500/10 px-4 py-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <div className="text-gray-300 leading-snug">
              <span className="font-medium text-white">Demo access</span>
              <br />
              <span className="text-gray-400">username: </span><span className="font-mono text-scarlet-300">admin</span>
              {'  ·  '}
              <span className="text-gray-400">password: </span><span className="font-mono text-scarlet-300">admin1234</span>
            </div>
            <button
              type="button"
              onClick={fillDemo}
              className="flex-shrink-0 rounded-md bg-scarlet-600 hover:bg-scarlet-500 px-3 py-1.5 text-xs font-medium text-white transition-colors"
            >
              Fill in
            </button>
          </div>
        </div>

        {/* Card */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-white mb-5">Sign in to your account</h2>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="label">Username</label>
              <input
                className="input"
                placeholder="admin"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  className="input pr-10"
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center mt-2">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          Powered by SBERT · SHAP · LIME
        </p>
      </div>
    </div>
  )
}
