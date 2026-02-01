import React from 'react'
import { Card, Metric, MetricChange } from '@/components/Common'
import './TerrainAnalysis.css'

interface TerrainData {
  slope: {
    min: number
    max: number
    mean: number
  }
  aspect: {
    min: number
    max: number
    mean: number
  }
  elevation: {
    min: number
    max: number
    mean: number
    std: number
  }
}

interface Props {
  data: TerrainData
  loading?: boolean
}

export const TerrainAnalysis: React.FC<Props> = ({ data, loading = false }) => {
  if (loading) {
    return <div className="terrain-analysis loading">Loading terrain data...</div>
  }

  return (
    <div className="terrain-analysis">
      <h2>Terrain Analysis</h2>
      
      <div className="analysis-grid">
        {/* Slope Metrics */}
        <Card className="metric-card">
          <h3>Slope</h3>
          <div className="metrics">
            <Metric label="Min" value={data.slope.min.toFixed(2)} unit="°" />
            <Metric label="Max" value={data.slope.max.toFixed(2)} unit="°" />
            <Metric label="Mean" value={data.slope.mean.toFixed(2)} unit="°" />
          </div>
        </Card>

        {/* Aspect Metrics */}
        <Card className="metric-card">
          <h3>Aspect</h3>
          <div className="metrics">
            <Metric label="Min" value={data.aspect.min.toFixed(0)} unit="°" />
            <Metric label="Max" value={data.aspect.max.toFixed(0)} unit="°" />
            <Metric label="Mean" value={data.aspect.mean.toFixed(0)} unit="°" />
          </div>
        </Card>

        {/* Elevation Metrics */}
        <Card className="metric-card">
          <h3>Elevation</h3>
          <div className="metrics">
            <Metric label="Min" value={data.elevation.min.toFixed(0)} unit="m" />
            <Metric label="Max" value={data.elevation.max.toFixed(0)} unit="m" />
            <Metric label="Mean" value={data.elevation.mean.toFixed(0)} unit="m" />
            <Metric label="Std Dev" value={data.elevation.std.toFixed(2)} unit="m" />
          </div>
        </Card>
      </div>
    </div>
  )
}
