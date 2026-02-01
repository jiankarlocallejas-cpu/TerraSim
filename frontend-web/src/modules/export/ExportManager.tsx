import React, { useState } from 'react'
import { Card } from '@/components/Common'
import './ExportManager.css'

type ExportFormat = 'json' | 'csv' | 'geotiff' | 'html'

interface Props {
  analysisId: string
  onExport?: (format: ExportFormat) => void
  isExporting?: boolean
}

export const ExportManager: React.FC<Props> = ({
  analysisId,
  onExport,
  isExporting = false,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('json')

  const formats: { value: ExportFormat; label: string; description: string }[] = [
    { value: 'json', label: 'JSON', description: 'Complete analysis data' },
    { value: 'csv', label: 'CSV', description: 'Spreadsheet format' },
    { value: 'geotiff', label: 'GeoTIFF', description: 'Georeferenced image' },
    { value: 'html', label: 'HTML Report', description: 'Interactive report' },
  ]

  const handleExport = () => {
    if (onExport) {
      onExport(selectedFormat)
    }
  }

  return (
    <Card className="export-manager">
      <h2>Export Results</h2>
      
      <div className="format-selector">
        {formats.map((format) => (
          <label key={format.value} className="format-option">
            <input
              type="radio"
              name="export-format"
              value={format.value}
              checked={selectedFormat === format.value}
              onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
              disabled={isExporting}
            />
            <div className="format-info">
              <strong>{format.label}</strong>
              <p>{format.description}</p>
            </div>
          </label>
        ))}
      </div>

      <button
        className="btn btn-primary"
        onClick={handleExport}
        disabled={isExporting}
      >
        {isExporting ? 'Exporting...' : 'Export Results'}
      </button>
    </Card>
  )
}
