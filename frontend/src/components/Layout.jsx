import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShoppingCart, MessageSquare, Building2, Settings, Key, FileText, LogOut, Zap } from 'lucide-react'

const navItems = [
  { to: '/orders',   label: 'Orders',      icon: ShoppingCart },
  { to: '/banks',    label: 'Banks',       icon: Building2 },
  { to: '/settings', label: 'Settings',    icon: Settings },
  { to: '/secrets',  label: 'Integrations', icon: Key },
  { to: '/logs',     label: 'Logs',        icon: FileText },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-binance-gray border-r border-binance-gray-light flex flex-col">
        <div className="px-4 py-5 border-b border-binance-gray-light">
          <div className="flex items-center gap-2">
            <Zap size={20} className="text-binance-yellow" />
            <span className="text-binance-yellow font-bold text-sm">P2P Bot</span>
          </div>
          <p className="text-xs text-binance-text-secondary mt-1 truncate">{user?.username}</p>
        </div>

        <nav className="flex-1 py-4 overflow-y-auto">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-binance-gray-light text-binance-yellow border-r-2 border-binance-yellow'
                    : 'text-binance-text-secondary hover:text-binance-text-primary hover:bg-binance-gray-light'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-binance-gray-light transition-colors border-t border-binance-gray-light"
        >
          <LogOut size={16} />
          Logout
        </button>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-binance-dark">
        <div className="p-6 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
