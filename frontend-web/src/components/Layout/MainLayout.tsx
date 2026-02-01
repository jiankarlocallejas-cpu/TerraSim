import React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Toolbar } from './Toolbar'
import './MainLayout.css'

export const MainLayout: React.FC = () => {
  return (
    <div className="main-layout">
      <Sidebar />
      <div className="main-content">
        <Toolbar />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
