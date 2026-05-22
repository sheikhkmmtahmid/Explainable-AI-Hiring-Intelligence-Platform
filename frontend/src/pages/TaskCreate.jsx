import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import { createTask } from '../api/tasks'
import { getUsers } from '../api/users'
import { useAuth } from '../context/AuthContext'

export default function TaskCreate() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isManager = user?.role === 'admin' || user?.role === 'recruiter'

  const [form, setForm] = useState({ title: '', description: '', status: 'pending', assigned_to: '' })
  const [users, setUsers] = useState([])
  const [saving, setSaving] = useState(false)

  // Task 2: managers need the user list to assign tasks
  useEffect(() => {
    if (isManager) {
      getUsers()
        .then(({ data }) => setUsers(data))
        .catch(() => {})
    }
  }, [isManager])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        title: form.title,
        description: form.description,
        status: form.status,
        ...(isManager && form.assigned_to ? { assigned_to: form.assigned_to } : {}),
      }
      await createTask(payload)
      toast.success('Task created')
      navigate('/tasks')
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? 'Failed to create task')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/tasks')}
          className="rounded-lg p-2 text-gray-400 hover:bg-surface-700 hover:text-white transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-2xl font-bold text-white">New Task</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 rounded-xl border border-surface-400 bg-surface-800 p-6">
        {/* Task 6: title — any user can set it on creation; editing is manager-only */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-300">
            Title <span className="text-red-400">*</span>
          </label>
          <input
            required
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="Task title"
            className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
          />
        </div>

        {/* Task 5: description editable by both */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-gray-300">Description</label>
          <textarea
            rows={4}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Describe the task…"
            className="w-full resize-none rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white focus:border-scarlet-500 focus:outline-none"
            >
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>

          {/* Task 2: only managers can assign to other users */}
          {isManager && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-300">Assign To</label>
              <select
                value={form.assigned_to}
                onChange={(e) => setForm({ ...form, assigned_to: e.target.value })}
                className="w-full rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white focus:border-scarlet-500 focus:outline-none"
              >
                <option value="">— Unassigned —</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username} ({u.role})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {!isManager && (
          <p className="rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs text-blue-300">
            This task will be assigned to you automatically.
          </p>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/tasks')}
            className="rounded-lg border border-surface-400 px-4 py-2 text-sm text-gray-300 hover:bg-surface-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-lg bg-scarlet-600 px-4 py-2 text-sm font-medium text-white hover:bg-scarlet-700 disabled:opacity-60 transition-colors"
          >
            {saving ? 'Saving…' : <><Save size={15} /> Create Task</>}
          </button>
        </div>
      </form>
    </div>
  )
}
