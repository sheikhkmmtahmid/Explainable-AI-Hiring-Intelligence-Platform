import { useState } from 'react'
import Sidebar from './Sidebar'
import { Menu } from 'lucide-react'
import LogoIcon from './LogoIcon'

export default function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-surface-900">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — drawer on mobile, static on md+ */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-60 transform transition-transform duration-200 ease-in-out
        md:static md:translate-x-0 md:transition-none
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <header className="flex items-center gap-3 px-4 py-3 bg-surface-800 border-b border-surface-400 md:hidden flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-400 hover:text-white transition-colors p-1"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <LogoIcon size={28} />
            <span className="font-bold text-white text-sm">HiringAI</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5 sm:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
