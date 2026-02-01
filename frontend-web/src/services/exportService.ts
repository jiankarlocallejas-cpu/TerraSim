/**
 * Export and Report Generation Service
 * Handles generating reports and exporting analysis results
 */

import { SimulationResult } from './simulationEngine'

export interface ExportOptions {
  format: 'pdf' | 'geotiff' | 'csv' | 'json' | 'shapefile'
  includeMetadata: boolean
  includeMaps: boolean
  includeStatistics: boolean
  resolution: number
}

export interface ReportData {
  title: string
  date: string
  summary: string
  statistics: Record<string, number | string>
  metrics: Array<{ label: string; value: number | string }>
  parameters: Record<string, any>
}

/**
 * Generate a report from simulation results
 */
export function generateReport(result: SimulationResult): ReportData {
  return {
    title: `TerraSim Analysis Report: ${result.name}`,
    date: new Date().toLocaleDateString(),
    summary: `Analysis completed on ${result.completedAt}. Type: ${result.type}. Status: ${result.status}.`,
    statistics: {
      'Total Erosion': result.statistics.totalErosion.toFixed(4),
      'Peak Erosion': result.statistics.peakErosion.toFixed(4),
      'Mean Erosion': result.statistics.meanErosion.toFixed(4),
      'Cumulative Mass': result.statistics.cumulativeMass.toFixed(4),
      'Affected Area': result.statistics.affectedArea,
      'Average Depth': result.statistics.averageDepth.toFixed(4),
    },
    metrics: [
      { label: 'Total Erosion Volume', value: `${result.statistics.totalErosion.toFixed(2)} m³` },
      { label: 'Peak Erosion Depth', value: `${result.statistics.peakErosion.toFixed(2)} m` },
      { label: 'Mean Erosion Depth', value: `${result.statistics.meanErosion.toFixed(2)} m` },
      { label: 'Affected Area', value: `${result.statistics.affectedArea} cells` },
      { label: 'Processing Time', value: result.metadata.processingTime },
      { label: 'Data Resolution', value: `${result.metadata.resolution} m` },
    ],
    parameters: {
      extent: result.metadata.extent,
      resolution: result.metadata.resolution,
      dataPoints: result.metadata.dataPoints,
    },
  }
}

/**
 * Export results as JSON
 */
export function exportAsJSON(result: SimulationResult): Blob {
  const data = {
    id: result.id,
    name: result.name,
    type: result.type,
    status: result.status,
    completedAt: result.completedAt,
    statistics: result.statistics,
    metadata: result.metadata,
  }
  return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
}

/**
 * Export results as CSV
 */
export function exportAsCSV(result: SimulationResult): Blob {
  const lines = [
    'TerraSim Analysis Report',
    `Analysis Name,${result.name}`,
    `Type,${result.type}`,
    `Date,${new Date().toISOString()}`,
    '',
    'Statistics',
    `Total Erosion,${result.statistics.totalErosion.toFixed(4)}`,
    `Peak Erosion,${result.statistics.peakErosion.toFixed(4)}`,
    `Mean Erosion,${result.statistics.meanErosion.toFixed(4)}`,
    `Cumulative Mass,${result.statistics.cumulativeMass.toFixed(4)}`,
    `Affected Area,${result.statistics.affectedArea}`,
    `Average Depth,${result.statistics.averageDepth.toFixed(4)}`,
    '',
    'Metadata',
    `Extent,${result.metadata.extent}`,
    `Resolution,${result.metadata.resolution}`,
    `Data Points,${result.metadata.dataPoints}`,
    `Processing Time,${result.metadata.processingTime}`,
  ]

  return new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
}

/**
 * Export raster data as GeoTIFF (simplified)
 */
export function exportAsGeoTIFF(
  data: Float32Array
): Blob {
  // Simplified GeoTIFF export - in production, use a proper GeoTIFF library
  const header = new ArrayBuffer(256)
  const headerView = new Uint8Array(header)

  // TIFF header
  headerView[0] = 0x49 // Little endian marker
  headerView[1] = 0x49
  headerView[2] = 0x2a // TIFF version
  headerView[3] = 0x00
  headerView[4] = 0x08 // Offset to first IFD
  headerView[5] = 0x00
  headerView[6] = 0x00
  headerView[7] = 0x00

  // Combine header with data
  const blob = new Blob([header, data.buffer as ArrayBuffer], { type: 'image/tiff' })
  return blob
}

/**
 * Export as shapefile (simplified GeoJSON representation)
 */
export function exportAsShapefile(result: SimulationResult, eroded: boolean = false): Blob {
  const data = eroded ? result.erosionMap : result.elevationData
  const size = Math.sqrt(data.length)

  // Create GeoJSON polygons for each grid cell with erosion > threshold
  const features = []
  const threshold = result.statistics.meanErosion * 0.5

  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      const idx = i * size + j
      const value = data[idx]

      if (value > threshold) {
        const cellSize = 100 // meters
        const minX = i * cellSize
        const minY = j * cellSize
        const maxX = (i + 1) * cellSize
        const maxY = (j + 1) * cellSize

        features.push({
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [
              [
                [minX, minY],
                [maxX, minY],
                [maxX, maxY],
                [minX, maxY],
                [minX, minY],
              ],
            ],
          },
          properties: {
            value: value,
            cellId: idx,
          },
        })
      }
    }
  }

  const geojson = {
    type: 'FeatureCollection',
    features: features,
  }

  return new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/json' })
}

/**
 * Generate HTML report
 */
export function generateHTMLReport(result: SimulationResult): Blob {
  const report = generateReport(result)

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${report.title}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
    h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; }
    h2 { color: #2c3e50; margin-top: 30px; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
    th { background-color: #00d4ff; color: white; }
    tr:nth-child(even) { background-color: #f9f9f9; }
    .metric { margin: 10px 0; padding: 10px; background: #f0f0f0; border-left: 4px solid #00d4ff; }
  </style>
</head>
<body>
  <h1>${report.title}</h1>
  <p><strong>Date:</strong> ${report.date}</p>
  <p><strong>Summary:</strong> ${report.summary}</p>

  <h2>Key Metrics</h2>
  ${report.metrics.map((m) => `<div class="metric"><strong>${m.label}:</strong> ${m.value}</div>`).join('')}

  <h2>Statistics</h2>
  <table>
    <tr>
      <th>Statistic</th>
      <th>Value</th>
    </tr>
    ${Object.entries(report.statistics)
      .map(
        ([key, value]) => `
    <tr>
      <td>${key}</td>
      <td>${value}</td>
    </tr>
    `
      )
      .join('')}
  </table>

  <h2>Analysis Parameters</h2>
  <table>
    <tr>
      <th>Parameter</th>
      <th>Value</th>
    </tr>
    ${Object.entries(report.parameters)
      .map(
        ([key, value]) => `
    <tr>
      <td>${key}</td>
      <td>${JSON.stringify(value)}</td>
    </tr>
    `
      )
      .join('')}
  </table>

  <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px;">
    Generated by TerraSim on ${new Date().toLocaleString()}
  </footer>
</body>
</html>
  `

  return new Blob([html], { type: 'text/html;charset=utf-8;' })
}

/**
 * Download blob as file
 */
export function downloadFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export default {
  generateReport,
  exportAsJSON,
  exportAsCSV,
  exportAsGeoTIFF,
  exportAsShapefile,
  generateHTMLReport,
  downloadFile,
}
