import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Save, Pencil, X, Trash2, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { getTask, updateTask, deleteTask } from '../api/tasks'
import { getUsers } from '../api/users'
import { useAuth } from '../context/AuthContext'

const STATUS_LABEL = { pending: 'Pending', in_progress: 'In Progress', done: 'Done' }

// Task 1: reusable delete confirmation modal
function DeleteConfirmModal({ task, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-md rounded-xl border border-surface-400 bg-surface-800 p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/15">
            <AlertTriangle size={20} className="text-red-400" />
          </div>
          <h2 className="text-lg font-semibold text-white">Delete Task</h2>
        </div>
        <p className="mb-1 text-sm text-gray-300">Are you sure you want to delete this task?</p>
        <p className="mb-6 truncate rounded bg-surface-700 px-3 py-2 text-sm font-medium text-white">
          {task.title}
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-lg border border-surface-400 px-4 py-2 text-sm text-gray-300 hover:bg-surface-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
          >
            Yes, delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default function TaskDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isManager = user?.role === 'admin' || user?.role === 'recruiter'

  const [task, setTask] = useState(null)
  const [users, setUsers] = useState([])
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [showDelete, setShowDelete] = useState(false)

  useEffect(() => {
    getTask(id)
      .then(({ data }) => {
        setTask(data)
        setForm({
          title: data.title,
          description: data.description,
          status: data.status,
          assigned_to: data.assigned_to ?? '',
        })
      })
      .catch(() => {
        toast.error('Task not found')
        navigate('/tasks')
      })

    if (isManager) {
      getUsers()
        .then(({ data }) => setUsers(data))
        .catch(() => {})
    }
  }, [id])

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = { description: form.description, status: form.status }
      // Task 6: only managers can update the title
      if (isManager) {
        payload.title = form.title
        payload.assigned_to = form.assigned_to || null
      }
      const { data } = await updateTask(id, payload)
      setTask(data)
      setEditing(false)
      toast.success('Task updated')
    } catch (err) {
      toast.error(err?.response?.data?.detail ?? 'Failed to update task')
    } finally {
      setSaving(false)
    }
  }

  // Task 1: confirm → delete → redirect to task list
  const handleDeleteConfirm = async () => {
    try {
      await deleteTask(id)
      toast.success('Task deleted')
      navigate('/tasks')
    } catch {
      toast.error('Failed to delete task')
    }
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-400">Loading…</div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header row */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/tasks')}
            className="rounded-lg p-2 text-gray-400 hover:bg-surface-700 hover:text-white transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <h1 className="text-2xl font-bold text-white truncate">
            {editing && isManager ? (
              <input
                autoFocus
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="bg-transparent border-b border-scarlet-500 text-white focus:outline-none text-2xl font-bold w-full"
              />
            ) : (
              task.title
            )}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          {/* Task 6: edit button shown to all, but title field only editable by manager */}
          {!editing ? (
            <button
              onClick={() => setEditing(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-surface-400 px-3 py-1.5 text-sm text-gray-300 hover:bg-surface-700 transition-colors"
            >
              <Pencil size={14} /> Edit
            </button>
          ) : (
            <>
              <button
                onClick={() => { setEditing(false); setForm({ title: task.title, description: task.description, status: task.status, assigned_to: task.assigned_to ?? '' }) }}
                className="rounded-lg border border-surface-400 px-3 py-1.5 text-sm text-gray-300 hover:bg-surface-700 transition-colors"
              >
                <X size={14} />
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-lg bg-scarlet-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-scarlet-700 disabled:opacity-60 transition-colors"
              >
                <Save size={14} /> {saving ? 'Saving…' : 'Save'}
              </button>
            </>
          )}

          {/* Task 4: delete only visible to manager/admin */}
          {isManager && (
            <button
              onClick={() => setShowDelete(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 px-3 py-1.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 size={14} /> Delete
            </button>
          )}
        </div>
      </div>

      {/* Task card */}
      <div className="space-y-5 rounded-xl border border-surface-400 bg-surface-800 p-6">
        {/* Meta row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Status</p>
            {editing ? (
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full rounded-lg border border-surface-400 bg-surface-700 px-2 py-1.5 text-sm text-white focus:border-scarlet-500 focus:outline-none"
              >
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            ) : (
              <span className="text-sm font-medium text-white">{STATUS_LABEL[task.status]}</span>
            )}
          </div>

          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Created By</p>
            <p className="text-sm text-white">{task.created_by_username}</p>
          </div>

          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Assigned To</p>
            {/* Task 2: manager can reassign; employee sees read-only */}
            {editing && isManager ? (
              <select
                value={form.assigned_to}
                onChange={(e) => setForm({ ...form, assigned_to: e.target.value })}
                className="w-full rounded-lg border border-surface-400 bg-surface-700 px-2 py-1.5 text-sm text-white focus:border-scarlet-500 focus:outline-none"
              >
                <option value="">— Unassigned —</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username} ({u.role})
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-sm text-white">
                {task.assigned_to_username ?? <span className="italic text-gray-500">Unassigned</span>}
              </p>
            )}
          </div>
        </div>

        {/* Description — Task 5: editable by everyone */}
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Description</p>
          {editing ? (
            <textarea
              rows={5}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Describe the task…"
              className="w-full resize-none rounded-lg border border-surface-400 bg-surface-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-scarlet-500 focus:outline-none"
            />
          ) : (
            <p className="text-sm text-gray-300 whitespace-pre-wrap">
              {task.description || <span className="italic text-gray-500">No description.</span>}
            </p>
          )}
        </div>

        {/* Role hint for employees */}
        {editing && !isManager && (
          <p className="rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs text-blue-300">
            You can update the description and status. Only managers can change the title or reassign tasks.
          </p>
        )}

        <div className="pt-2 border-t border-surface-400 flex gap-4 text-xs text-gray-500">
          <span>Created: {new Date(task.created_at).toLocaleString()}</span>
          <span>Updated: {new Date(task.updated_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Task 1: Delete confirmation modal */}
      {showDelete && (
        <DeleteConfirmModal
          task={task}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  )
}
