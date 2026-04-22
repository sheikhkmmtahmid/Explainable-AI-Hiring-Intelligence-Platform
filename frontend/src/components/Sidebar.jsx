import { NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard, Briefcase, Users, GitMerge,
  BarChart3, LogOut,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import LogoIcon from './LogoIcon'

const nav = [
  { to: '/',           icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs',       icon: Briefcase,       label: 'Jobs' },
  { to: '/candidates', icon: Users,           label: 'Candidates' },
  { to: '/matching',   icon: GitMerge,        label: 'Matching' },
  { to: '/fairness',   icon: BarChart3,       label: 'Fairness' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="w-60 flex-shrink-0 bg-surface-800 border-r border-surface-400 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-surface-400">
        <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <LogoIcon size={36} />
          <div>
            <p className="font-bold text-white text-sm leading-tight">HiringAI</p>
            <p className="text-xs text-gray-500">Intelligence Platform</p>
          </div>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-scarlet-500/15 text-scarlet-400 border border-scarlet-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-surface-600'
              }`
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-3 py-4 border-t border-surface-400">
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
