import React, { useState } from 'react'
import { Card } from '@/components/Common'
import './ErosionAnalysis.css'

interface ErosionResults {
  total_erosion: number
  num_steps: number
  initial_elevation: number
  final_elevation: number
}

interface Props {
  results: ErosionResults
  onVisualize?: (data: any) => void
}

export const ErosionAnalysis: React.FC<Props> = ({ results, onVisualize }) => {
  const [showDetails, setShowDetails] = useState(false)

  const elevationChange = results.initial_elevation - results.final_elevation
  const percentChange = (elevationChange / results.initial_elevation) * 100

  return (
    <Card className="erosion-analysis">
      <h2>Erosion Analysis Results</h2>
      
      <div className="results-summary">
        <div className="result-item">
          <span className="label">Total Erosion</span>
          <span className="value">{results.total_erosion.toFixed(2)} m³</span>
        </div>
        
        <div className="result-item">
          <span className="label">Simulation Steps</span>
          <span className="value">{results.num_steps}</span>
        </div>
        
        <div className="result-item">
          <span className="label">Initial Elevation</span>
          <span className="value">{results.initial_elevation.toFixed(2)} m</span>
        </div>
        
        <div className="result-item">
          <span className="label">Final Elevation</span>
          <span className="value">{results.final_elevation.toFixed(2)} m</span>
        </div>
        
        <div className="result-item highlight">
          <span className="label">Elevation Change</span>
          <span className="value">{elevationChange.toFixed(2)} m ({percentChange.toFixed(2)}%)</span>
        </div>
      </div>

      <div className="actions">
        <button
          className="btn btn-secondary"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? 'Hide' : 'Show'} Details
        </button>
        {onVisualize && (
          <button className="btn btn-primary" onClick={() => onVisualize(results)}>
            Visualize Results
          </button>
        )}
      </div>

      {showDetails && (
        <div className="details">
          <h3>Detailed Analysis</h3>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </Card>
  )
}
