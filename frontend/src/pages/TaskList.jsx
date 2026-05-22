import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Trash2, Eye, CheckCircle2, Clock, Loader2, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { getTasks, deleteTask } from '../api/tasks'
import { useAuth } from '../context/AuthContext'

const STATUS_STYLES = {
  pending:     'bg-yellow-500/15 text-yellow-400',
  in_progress: 'bg-blue-500/15 text-blue-400',
  done:        'bg-green-500/15 text-green-400',
}

const STATUS_ICONS = {
  pending:     <Clock size={12} />,
  in_progress: <Loader2 size={12} />,
  done:        <CheckCircle2 size={12} />,
}

const STATUS_LABEL = {
  pending:     'Pending',
  in_progress: 'In Progress',
  done:        'Done',
}

// Task 1: Delete confirmation modal
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
        <p className="mb-1 text-sm text-gray-300">
          Are you sure you want to delete this task?
        </p>
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

export default function TaskList() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [toDelete, setToDelete] = useState(null)   // Task object awaiting confirmation

  const isManager = user?.role === 'admin' || user?.role === 'recruiter'

  useEffect(() => {
    getTasks()
      .then(({ data }) => setTasks(data.results ?? data))
      .catch(() => toast.error('Failed to load tasks'))
      .finally(() => setLoading(false))
  }, [])

  // Task 1: after confirm → delete → redirect to task list (we're already here, just refresh)
  const handleDeleteConfirm = async () => {
    try {
      await deleteTask(toDelete.id)
      setTasks((prev) => prev.filter((t) => t.id !== toDelete.id))
      toast.success('Task deleted')
    } catch {
      toast.error('Failed to delete task')
    } finally {
      setToDelete(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Tasks</h1>
          <p className="mt-1 text-sm text-gray-400">
            {isManager ? 'All tasks across your team' : 'Your assigned & created tasks'}
          </p>
        </div>
        <Link
          to="/tasks/new"
          className="inline-flex items-center gap-2 rounded-lg bg-scarlet-600 px-4 py-2 text-sm font-medium text-white hover:bg-scarlet-700 transition-colors"
        >
          <Plus size={16} /> New Task
        </Link>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-scarlet-400" />
        </div>
      ) : tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-surface-400 bg-surface-800 py-20 text-gray-400">
          <CheckCircle2 size={40} className="mb-3 opacity-30" />
          <p className="text-lg font-medium">No tasks yet</p>
          <p className="text-sm">Create your first task to get started.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-surface-400 bg-surface-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-400 text-left text-xs uppercase tracking-wide text-gray-400">
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3 hidden sm:table-cell">Status</th>
                <th className="px-4 py-3 hidden md:table-cell">Assigned To</th>
                <th className="px-4 py-3 hidden md:table-cell">Created By</th>
                <th className="px-4 py-3 hidden lg:table-cell">Created</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-400">
              {tasks.map((task) => (
                <tr key={task.id} className="hover:bg-surface-700 transition-colors">
                  <td className="px-4 py-3 font-medium text-white max-w-xs truncate">
                    {task.title}
                    {/* Show status badge inline on mobile */}
                    <span className={`ml-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium sm:hidden ${STATUS_STYLES[task.status]}`}>
                      {STATUS_ICONS[task.status]} {STATUS_LABEL[task.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[task.status]}`}>
                      {STATUS_ICONS[task.status]} {STATUS_LABEL[task.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell text-gray-300">
                    {task.assigned_to_username ?? <span className="italic text-gray-500">Unassigned</span>}
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell text-gray-300">
                    {task.created_by_username}
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell text-gray-400">
                    {new Date(task.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        to={`/tasks/${task.id}`}
                        className="rounded p-1.5 text-gray-400 hover:bg-surface-600 hover:text-white transition-colors"
                        title="View / Edit"
                      >
                        <Eye size={15} />
                      </Link>
                      {/* Task 4: delete button only visible to manager/admin */}
                      {isManager && (
                        <button
                          onClick={() => setToDelete(task)}
                          className="rounded p-1.5 text-gray-400 hover:bg-red-500/15 hover:text-red-400 transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Task 1: Delete confirmation modal */}
      {toDelete && (
        <DeleteConfirmModal
          task={toDelete}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setToDelete(null)}
        />
      )}
    </div>
  )
}
