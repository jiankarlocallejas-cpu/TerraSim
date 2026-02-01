import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Map as MapIcon,
  Science as ScienceIcon,
  Folder as FolderIcon,
  Settings as SettingsIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import './Sidebar.css'

export const Sidebar: React.FC = () => {
  const [isOpen, setIsOpen] = React.useState(true)

  const navItems = [
    { path: '/', label: 'Dashboard', icon: DashboardIcon },
    { path: '/analysis', label: 'Analysis', icon: ScienceIcon },
    { path: '/projects', label: 'Projects', icon: FolderIcon },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ]

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <div className="logo">
          <MapIcon className="logo-icon" />
          {isOpen && <h1>TerraSim</h1>}
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="toggle-btn"
          aria-label="Toggle sidebar"
          title={isOpen ? 'Collapse' : 'Expand'}
        >
          {isOpen ? <CloseIcon /> : <MenuIcon />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `nav-link ${isActive ? 'active' : ''}`
            }
            title={!isOpen ? label : ''}
          >
            <Icon className="nav-icon" />
            {isOpen && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {isOpen && <p className="version">TerraSim</p>}
        <p className="text-sm text-muted">v1.0.0</p>
      </div>
    </aside>
  )
}
