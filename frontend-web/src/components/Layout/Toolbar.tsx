import React from 'react'
import {
  Search as SearchIcon,
  Help as HelpIcon,
  AccountCircle as ProfileIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material'
import './Toolbar.css'

export const Toolbar: React.FC = () => {
  const [searchQuery, setSearchQuery] = React.useState('')

  return (
    <div className="toolbar">
      <div className="toolbar-search">
        <SearchIcon className="search-icon" />
        <input
          type="text"
          placeholder="Search projects, analyses, data..."
          className="search-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="toolbar-actions">
        <button className="toolbar-action-btn" title="Notifications">
          <NotificationsIcon />
          <span className="notification-badge">3</span>
        </button>
        <button className="toolbar-action-btn" title="Help">
          <HelpIcon />
        </button>
        <button className="toolbar-action-btn profile-btn" title="Profile">
          <ProfileIcon />
        </button>
      </div>
    </div>
  )
}
