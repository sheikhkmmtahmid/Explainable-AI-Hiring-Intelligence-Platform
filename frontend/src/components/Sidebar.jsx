import { NavLink, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Briefcase, Users,
  BarChart3, LogOut, X, ClipboardList, UserPlus, Inbox, Sparkles, CreditCard, Landmark, Info,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import LogoIcon from './LogoIcon'

const nav = [
  { to: '/',             icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs',         icon: Briefcase,       label: 'Jobs' },
  { to: '/candidates',   icon: Users,           label: 'Candidates' },
  { to: '/applications', icon: Inbox,           label: 'Applications' },
  { to: '/fairness',     icon: BarChart3,       label: 'Fairness' },
  { to: '/tasks',        icon: ClipboardList,   label: 'Tasks' },
]

const ACTIVE_CLASSES = 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20'
const INACTIVE_CLASSES = 'text-gray-400 hover:text-white hover:bg-surface-600'

// A candidate profile opened from a job's context (?returnTo=/jobs/.. or /matching/..)
// should keep "Jobs" highlighted instead of "Candidates" — the user is still
// conceptually inside the job flow, not browsing the candidate list.
function isNavActive(to, pathname, jobContextActive) {
  if (jobContextActive) {
    if (to === '/jobs') return true
    if (to === '/candidates') return false
  }
  if (to === '/') return pathname === '/'
  return pathname === to || pathname.startsWith(`${to}/`)
}

export default function Sidebar({ onClose }) {
  const { user, logout } = useAuth()
  const isManager = user?.role === 'admin' || user?.role === 'recruiter'
  const isAdmin = user?.role === 'admin'
  const isPlatformStaff = !!user?.is_platform_staff
  const location = useLocation()
  const returnTo = new URLSearchParams(location.search).get('returnTo')
  const jobContextActive =
    location.pathname.startsWith('/candidates/') &&
    !!returnTo &&
    (returnTo.startsWith('/jobs') || returnTo.startsWith('/matching'))

  return (
    <aside className="w-60 flex-shrink-0 bg-surface-800 border-r border-surface-400 flex flex-col h-screen">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-surface-400 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity" onClick={onClose}>
          <LogoIcon size={36} />
          <div>
            <p className="font-bold text-white text-sm leading-tight">HiringAI</p>
            <p className="text-xs text-gray-500">Intelligence Platform</p>
          </div>
        </Link>
        {/* Close button — mobile only */}
        <button
          onClick={onClose}
          className="md:hidden text-gray-500 hover:text-white transition-colors p-1"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => {
          const active = isNavActive(to, location.pathname, jobContextActive)
          return (
            <Link
              key={to}
              to={to}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                active ? ACTIVE_CLASSES : INACTIVE_CLASSES
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          )
        })}

        {/* Task 10: "Create New User" button — only visible to admin and manager */}
        {isManager && (
          <>
            <div className="my-2 border-t border-surface-400" />
            <NavLink
              to="/users/create"
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20'
                    : 'text-gray-400 hover:text-white hover:bg-surface-600'
                }`
              }
            >
              <UserPlus className="w-4 h-4 flex-shrink-0" />
              Create New User
            </NavLink>
          </>
        )}

        {isAdmin && (
          <NavLink
            to="/skills/moderation"
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-surface-600'
              }`
            }
          >
            <Sparkles className="w-4 h-4 flex-shrink-0" />
            Skill Moderation
          </NavLink>
        )}

        {isAdmin && (
          <NavLink
            to="/billing"
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-surface-600'
              }`
            }
          >
            <CreditCard className="w-4 h-4 flex-shrink-0" />
            Billing
          </NavLink>
        )}

        {isPlatformStaff && (
          <NavLink
            to="/billing/moderation"
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-surface-600'
              }`
            }
          >
            <Landmark className="w-4 h-4 flex-shrink-0" />
            Payment Review
          </NavLink>
        )}
      </nav>

      {/* User */}
      <div className="px-3 py-4 border-t border-surface-400 space-y-2">
        <Link
          to="/about"
          onClick={onClose}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-500 hover:text-white hover:bg-surface-600 transition-colors"
        >
          <Info className="w-3.5 h-3.5 flex-shrink-0" />
          About &amp; data sources
        </Link>
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-surface-600">
          <div className="w-7 h-7 rounded-full bg-scarlet-500 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {user?.username?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">{user?.username ?? 'User'}</p>
            <p className="text-xs text-gray-500 truncate capitalize">{user?.role ?? 'recruiter'}</p>
          </div>
          <button onClick={logout} className="text-gray-500 hover:text-scarlet-400 transition-colors">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
