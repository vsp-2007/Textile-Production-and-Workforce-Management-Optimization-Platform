import React, { useState, useEffect } from 'react'
import { Link, useLocation, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../App'
import './Layout.css'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: 'bi-speedometer2', roles: ['admin', 'supervisor', 'operator'] },
  { name: 'Floor Map', href: '/floor-map', icon: 'bi-diagram-3', roles: ['admin', 'supervisor'] },
  { name: 'Scheduler', href: '/scheduler', icon: 'bi-calendar3', roles: ['admin', 'supervisor'] },
  { name: 'Reports', href: '/reports', icon: 'bi-file-earmark-bar-graph', roles: ['admin', 'supervisor'] },
  { name: 'Machines', href: '/machines', icon: 'bi-cpu', roles: ['admin', 'supervisor'] },
  { name: 'Operators', href: '/operators', icon: 'bi-people', roles: ['admin', 'supervisor'] },
  { name: 'Profile', href: '/profile', icon: 'bi-person', roles: ['admin', 'supervisor', 'operator'] },
]

function Layout() {
  const { user, logout, isAdmin, isSupervisor, isOperator, toggleTheme } = useAuth()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Determine user role for navigation filtering
  const userRole = user?.role || 'operator'

  const filteredNav = navigation.filter(item => item.roles.includes(userRole))

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div className="app-layout">
      {/* Sidebar Overlay for Mobile */}
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''} ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <i className="bi bi-thread"></i>
          </div>
          <span className="sidebar-title">TexWorkforce</span>
        </div>

        <nav className="sidebar-nav">
          {filteredNav.map((section) => (
            <div key={section.name} className="nav-section">
              <NavLink
                to={section.href}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setSidebarOpen(false)}
              >
                <i className={`bi ${section.icon}`}></i>
                <span>{section.name}</span>
              </NavLink>
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-menu" onClick={() => setSidebarOpen(false)}>
            <div className="user-avatar">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="user-info">
              <div className="user-name">{user?.name || 'User'}</div>
              <div className="user-role">{userRole.charAt(0).toUpperCase() + userRole.slice(1)}</div>
            </div>
          </div>
          
          <div className="sidebar-actions">
            <button 
              className="btn btn-ghost btn-sm"
              onClick={toggleTheme}
              title="Toggle Theme"
            >
              <i className={`bi ${document.documentElement.classList.contains('high-contrast') ? 'bi-sun' : 'bi-moon'}`}></i>
            </button>
            <button 
              className="btn btn-ghost btn-sm"
              onClick={handleLogout}
              title="Logout"
            >
              <i className="bi bi-box-arrow-right"></i>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Top Bar */}
        <header className="top-bar">
          <div className="top-bar-left">
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(true)}
              aria-label="Toggle sidebar"
            >
              <i className="bi bi-list"></i>
            </button>
            <h1 className="page-title">{getPageTitle(location.pathname)}</h1>
          </div>

          <div className="top-bar-right">
            <div className="notification-dropdown">
              <button className="notification-btn" aria-label="Notifications">
                <i className="bi bi-bell"></i>
                <span className="notification-badge">3</span>
              </button>
            </div>
            
            <div className="user-dropdown">
              <Link to="/profile" className="user-avatar-small">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </Link>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

function getPageTitle(pathname) {
  const titles = {
    '/dashboard': 'Dashboard',
    '/floor-map': 'Floor Map',
    '/scheduler': 'Shift Scheduler',
    '/reports': 'Reports',
    '/machines': 'Machines',
    '/operators': 'Operators',
    '/profile': 'Profile',
  }
  
  for (const [path, title] of Object.entries(titles)) {
    if (pathname.startsWith(path)) return title
  }
  return 'TexWorkforce Optimizer'
}

export default Layout