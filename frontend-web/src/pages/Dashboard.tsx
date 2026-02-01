import React, { useState } from 'react'
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Map as MapIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import { CesiumViewer } from '../components/CesiumViewer'
import './Dashboard.css'

interface StatCard {
  label: string
  value: string | number
  change?: string
  icon: React.ReactNode
  color: string
}

export const Dashboard: React.FC = () => {
  const [showViewer, setShowViewer] = useState(false)

  const stats: StatCard[] = [
    {
      label: 'Active Analyses',
      value: '12',
      change: '+3 today',
      icon: <SpeedIcon />,
      color: '#00d4ff',
    },
    {
      label: 'Total Projects',
      value: '48',
      change: '+2 this week',
      icon: <TrendingUpIcon />,
      color: '#8b5cf6',
    },
    {
      label: 'Data Processed',
      value: '2.4 TB',
      change: '+340 GB',
      icon: <StorageIcon />,
      color: '#10b981',
    },
    {
      label: 'Success Rate',
      value: '99.2%',
      change: 'Excellent',
      icon: <CheckCircleIcon />,
      color: '#f59e0b',
    },
  ]

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="text-muted">Welcome back to TerraSim</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => window.location.href = '/analysis'}>+ New Analysis</button>
          <button className="btn btn-secondary" onClick={() => window.location.href = '/settings'}>Settings</button>
        </div>
      </div>

      <div className="stats-grid">
        {stats.map((stat, idx) => (
          <div key={idx} className="stat-card" style={{ borderTopColor: stat.color }}>
            <div className="stat-icon" style={{ color: stat.color }}>
              {stat.icon}
            </div>
            <div className="stat-content">
              <p className="stat-label">{stat.label}</p>
              <h3 className="stat-value">{stat.value}</h3>
              <p className="stat-change">{stat.change}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-content">
        {/* 3D Terrain Viewer */}
        {showViewer && (
          <div className="viewer-modal">
            <div className="viewer-container">
              <button
                className="viewer-close-btn"
                onClick={() => setShowViewer(false)}
              >
                <CloseIcon />
              </button>
              <CesiumViewer
                terrain={true}
                enableDragging={true}
                enableZoom={true}
                initialLocation={{ longitude: 0, latitude: 45, height: 15000000 }}
              />
            </div>
          </div>
        )}

        <div className="content-section">
          <div className="section-header">
            <h2>3D Terrain Visualization</h2>
            <button
              className="btn btn-primary-sm"
              onClick={() => setShowViewer(!showViewer)}
            >
              <MapIcon style={{ marginRight: '8px' }} />
              {showViewer ? 'Close Viewer' : 'Open 3D Viewer'}
            </button>
          </div>
          {!showViewer && (
            <div className="viewer-preview">
              <p>
                Interactive 3D terrain visualization with real-time elevation data
              </p>
              <button
                className="btn btn-primary"
                onClick={() => setShowViewer(true)}
              >
                Launch 3D Viewer
              </button>
            </div>
          )}
        </div>

        <div className="content-section">
          <div className="section-header">
            <h2>Recent Analyses</h2>
            <button className="view-all-btn" onClick={() => window.location.href = '/analyses'}>View All →</button>
          </div>
          <div className="analyses-list">
            {[
              {
                name: 'Mountain Erosion Study',
                status: 'completed',
                progress: 100,
                date: 'Jan 28, 2026',
              },
              {
                name: 'Valley Formation Analysis',
                status: 'running',
                progress: 67,
                date: 'Jan 29, 2026',
              },
              {
                name: 'Coastal Erosion Model',
                status: 'pending',
                progress: 0,
                date: 'Jan 29, 2026',
              },
            ].map((analysis, idx) => (
              <div key={idx} className="analysis-item">
                <div className="analysis-info">
                  <h4>{analysis.name}</h4>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${analysis.progress}%`,
                        backgroundColor:
                          analysis.status === 'completed'
                            ? '#10b981'
                            : analysis.status === 'running'
                              ? '#00d4ff'
                              : '#5a5a5a',
                      }}
                    />
                  </div>
                </div>
                <div className="analysis-meta">
                  <span className={`status status-${analysis.status}`}>
                    {analysis.status}
                  </span>
                  <span className="date">{analysis.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="content-section">
          <div className="section-header">
            <h2>Quick Actions</h2>
          </div>
          <div className="actions-grid">
            {[
              { title: 'Import Data', desc: 'Add new DEM or raster files', href: '/analysis' },
              { title: 'View Results', desc: 'Check analysis outputs', href: '/results' },
              { title: 'Export Report', desc: 'Generate analysis report', href: '/results' },
              { title: 'Manage Layers', desc: 'Organize map layers', href: '/analysis' },
            ].map((action, idx) => (
              <div key={idx} className="action-card">
                <h4>{action.title}</h4>
                <p>{action.desc}</p>
                <button className="action-btn" onClick={() => window.location.href = action.href}>Go →</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
