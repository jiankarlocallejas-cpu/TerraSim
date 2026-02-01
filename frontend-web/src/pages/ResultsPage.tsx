import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { CesiumViewer } from '../components/CesiumViewer'
import * as Cesium from 'cesium'
import {
  Download as DownloadIcon,
  Share as ShareIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import {
  SimulationResult,
} from '../services/simulationEngine'
import {
  downloadFile,
  generateHTMLReport,
  exportAsJSON,
  exportAsCSV,
} from '../services/exportService'

export const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [showExportMenu, setShowExportMenu] = useState(false)

  useEffect(() => {
    // Fetch analysis results
    const fetchResults = async () => {
      try {
        const response = await fetch(`/api/analyses/${id}/results`)
        if (response.ok) {
          const data = await response.json()
          setResult(data)
        } else {
          console.error('Failed to fetch results:', response.status)
        }
      } catch (error) {
        console.error('Error fetching results:', error)
      } finally {
        setLoading(false)
      }
    }

    if (id) {
      fetchResults()
    } else {
      setLoading(false)
    }
  }, [id])
  const handleExport = (format: 'html' | 'json' | 'csv') => {
    if (!result) return

    let blob: Blob
    let filename: string

    switch (format) {
      case 'html':
        blob = generateHTMLReport(result)
        filename = `terrasim-report-${result.id}.html`
        break
      case 'json':
        blob = exportAsJSON(result)
        filename = `terrasim-results-${result.id}.json`
        break
      case 'csv':
        blob = exportAsCSV(result)
        filename = `terrasim-results-${result.id}.csv`
        break
      default:
        return
    }

    downloadFile(blob, filename)
    setShowExportMenu(false)
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading results...</div>
  }

  if (!result) {
    return <div style={{ padding: '20px' }}>No results found</div>
  }

  return (
    <div style={{ display: 'flex', height: '100%', gap: '24px', padding: '32px', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.5) 0%, rgba(30, 41, 59, 0.5) 100%)' }}>
      {/* 3D Visualization */}
      <div style={{ flex: 1, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)' }}>
        <CesiumViewer
          terrain={true}
          enableDragging={true}
          enableZoom={true}
          initialLocation={{ longitude: 2.5, latitude: 47.5, height: 3000000 }}
        />
      </div>

      {/* Results Panel */}
      <div
        style={{
          width: '420px',
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '16px',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          overflow: 'auto',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
        }}
      >
        <div>
          <h2 style={{ margin: '0 0 12px 0', fontSize: '1.75rem', fontWeight: '700', background: 'linear-gradient(135deg, #00d4ff 0%, #0ea5e9 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{result.name}</h2>
          <p style={{ margin: '0', fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.6)' }}>
            Analysis ID: {result.id}
          </p>
        </div>

        {/* Status Badge */}
        <div
          style={{
            padding: '16px',
            background:
              result.status === 'completed'
                ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%)'
                : 'linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(249, 115, 22, 0.1) 100%)',
            border:
              result.status === 'completed'
                ? '1px solid rgba(16, 185, 129, 0.4)'
                : '1px solid rgba(251, 146, 60, 0.4)',
            borderRadius: '12px',
            backdropFilter: 'blur(4px)',
          }}
        >
          <p style={{ margin: '0', fontSize: '0.85rem', fontWeight: '600', color: 'rgba(255, 255, 255, 0.9)' }}>
            Status:{' '}
            <span
              style={{
                color:
                  result.status === 'completed' ? 'rgb(16, 185, 129)' : 'rgb(251, 146, 60)',
                fontWeight: '700',
              }}
            >
              {result.status.toUpperCase()}
            </span>
          </p>
          <p style={{ margin: '6px 0 0 0', fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.7)' }}>
            ✓ Completed {new Date(result.completedAt || '').toLocaleDateString()}
          </p>
        </div>

        {/* Analysis Metadata */}
        <div
          style={{
            padding: '12px',
            background: 'rgba(59, 130, 246, 0.05)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '6px',
          }}
        >
          <h3 style={{ margin: '0 0 12px 0', fontSize: '0.95rem', fontWeight: '600' }}>
            <InfoIcon style={{ fontSize: '16px', marginRight: '6px', verticalAlign: 'text-bottom' }} />
            Analysis Metadata
          </h3>
          <div style={{ fontSize: '0.85rem', display: 'grid', gap: '8px' }}>
            <div>
              <p style={{ margin: '0', color: 'var(--muted-foreground)' }}>Type</p>
              <p style={{ margin: '2px 0 0 0', fontWeight: '500' }}>{result.type}</p>
            </div>
            <div>
              <p style={{ margin: '0', color: 'var(--muted-foreground)' }}>Extent</p>
              <p style={{ margin: '2px 0 0 0', fontWeight: '500' }}>{result.metadata.extent}</p>
            </div>
            <div>
              <p style={{ margin: '0', color: 'var(--muted-foreground)' }}>Resolution</p>
              <p style={{ margin: '2px 0 0 0', fontWeight: '500' }}>
                {result.metadata.resolution}m
              </p>
            </div>
            <div>
              <p style={{ margin: '0', color: 'var(--muted-foreground)' }}>Data Points</p>
              <p style={{ margin: '2px 0 0 0', fontWeight: '500' }}>
                {result.metadata.dataPoints.toLocaleString()}
              </p>
            </div>
            <div>
              <p style={{ margin: '0', color: 'var(--muted-foreground)' }}>Processing Time</p>
              <p style={{ margin: '2px 0 0 0', fontWeight: '500' }}>
                {result.metadata.processingTime}
              </p>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div>
          <h3 style={{ margin: '0 0 14px 0', fontSize: '0.95rem', fontWeight: '700', color: 'rgba(255, 255, 255, 0.95)' }}>
            📊 Key Metrics
          </h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div
              style={{
                padding: '14px',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(109, 40, 217, 0.1) 100%)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '10px',
                backdropFilter: 'blur(4px)',
              }}
            >
              <p style={{ margin: '0', fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.6)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '600' }}>
                Total Erosion
              </p>
              <p style={{ margin: '6px 0 0 0', fontSize: '1.3rem', fontWeight: '700', color: 'rgb(139, 92, 246)' }}>
                {result.statistics.totalErosion.toFixed(2)}
                <span style={{ fontSize: '0.8rem', marginLeft: '4px', color: 'rgba(255, 255, 255, 0.7)' }}>m³</span>
              </p>
            </div>
            <div
              style={{
                padding: '14px',
                background: 'linear-gradient(135deg, rgba(244, 114, 182, 0.15) 0%, rgba(219, 39, 119, 0.1) 100%)',
                border: '1px solid rgba(244, 114, 182, 0.3)',
                borderRadius: '10px',
                backdropFilter: 'blur(4px)',
              }}
            >
              <p style={{ margin: '0', fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.6)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '600' }}>
                Peak Erosion
              </p>
              <p style={{ margin: '6px 0 0 0', fontSize: '1.3rem', fontWeight: '700', color: 'rgb(244, 114, 182)' }}>
                {result.statistics.peakErosion.toFixed(2)}
                <span style={{ fontSize: '0.8rem', marginLeft: '4px', color: 'rgba(255, 255, 255, 0.7)' }}>m</span>
              </p>
            </div>
            <div
              style={{
                padding: '14px',
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(22, 163, 74, 0.1) 100%)',
                border: '1px solid rgba(34, 197, 94, 0.3)',
                borderRadius: '10px',
                backdropFilter: 'blur(4px)',
              }}
            >
              <p style={{ margin: '0', fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.6)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '600' }}>
                Mean Erosion
              </p>
              <p style={{ margin: '6px 0 0 0', fontSize: '1.3rem', fontWeight: '700', color: 'rgb(34, 197, 94)' }}>
                {result.statistics.meanErosion.toFixed(2)}
                <span style={{ fontSize: '0.8rem', marginLeft: '4px', color: 'rgba(255, 255, 255, 0.7)' }}>m</span>
              </p>
            </div>
            <div
              style={{
                padding: '14px',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '10px',
                backdropFilter: 'blur(4px)',
              }}
            >
              <p style={{ margin: '0', fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.6)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '600' }}>
                Affected Area
              </p>
              <p style={{ margin: '6px 0 0 0', fontSize: '1.3rem', fontWeight: '700', color: 'rgb(59, 130, 246)' }}>
                {result.statistics.affectedArea.toLocaleString()}
                <span style={{ fontSize: '0.8rem', marginLeft: '4px', color: 'rgba(255, 255, 255, 0.7)' }}>cells</span>
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '10px', flexDirection: 'column', marginTop: 'auto' }}>
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              style={{
                width: '100%',
                padding: '10px',
                background: 'var(--primary)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <DownloadIcon style={{ fontSize: '18px' }} />
              Export Results
            </button>

            {showExportMenu && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '45px',
                  right: 0,
                  background: 'white',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  zIndex: 1000,
                  minWidth: '150px',
                }}
              >
                {[
                  { label: 'Export as PDF', format: 'html' as const },
                  { label: 'Export as JSON', format: 'json' as const },
                  { label: 'Export as CSV', format: 'csv' as const },
                ].map((option) => (
                  <button
                    key={option.format}
                    onClick={() => handleExport(option.format)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: 'none',
                      background: 'transparent',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontSize: '0.85rem',
                      borderBottom: '1px solid var(--border)',
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => {
              const url = window.location.href
              if (navigator.share) {
                navigator.share({
                  title: 'TerraSim Results',
                  text: `Check out this analysis result`,
                  url: url,
                }).catch(() => {})
              } else {
                const text = `TerraSim Analysis Results: ${url}`
                navigator.clipboard.writeText(text).then(() => {
                  alert('Link copied to clipboard')
                })
              }
            }}
            style={{
              padding: '10px',
              background: '#666',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            <ShareIcon style={{ fontSize: '18px' }} />
            Share Results
          </button>
        </div>
      </div>
    </div>
  )
}
