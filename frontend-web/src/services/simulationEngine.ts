/**
 * Simulation Engine Service
 * Handles erosion simulation, terrain modification, and analysis
 */

export interface SimulationParameters {
  name: string
  type: 'erosion' | 'deposition' | 'flow' | 'slope'
  extent: {
    north: number
    south: number
    east: number
    west: number
  }
  resolution: number
  timeSteps: number
  timeStepDays: number
  rainIntensity: number
  infiltrationRate: number
  vegetation: number
  slope: number
}

export interface SimulationResult {
  id: string
  name: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'error'
  completedAt?: string
  elevationData: Float32Array
  erosionMap: Float32Array
  statistics: SimulationStatistics
  metadata: {
    extent: string
    resolution: number
    dataPoints: number
    processingTime: string
  }
}

export interface SimulationStatistics {
  totalErosion: number
  peakErosion: number
  meanErosion: number
  cumulativeMass: number
  affectedArea: number
  averageDepth: number
}

/**
 * Initialize a new simulation
 */
export function initializeSimulation(params: SimulationParameters): {
  id: string
  elevationData: Float32Array
  erosionMap: Float32Array
} {
  const id = `sim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  const dataSize = Math.ceil(params.resolution)
  const elevationData = new Float32Array(dataSize * dataSize)
  const erosionMap = new Float32Array(dataSize * dataSize)

  // Initialize with simple height gradient
  for (let i = 0; i < dataSize; i++) {
    for (let j = 0; j < dataSize; j++) {
      const idx = i * dataSize + j
      elevationData[idx] = 100 + (i + j) * 0.1 // Gradual slope
      erosionMap[idx] = 0
    }
  }

  return { id, elevationData, erosionMap }
}

/**
 * Execute single simulation step (erosion calculation)
 */
export function simulateErosionStep(
  dem: Float32Array,
  erosionMap: Float32Array,
  params: SimulationParameters
): { dem: Float32Array; erosion: Float32Array } {
  const size = Math.sqrt(dem.length)
  const newDEM = new Float32Array(dem)
  const newErosion = new Float32Array(erosionMap)

  // Simple erosion simulation
  for (let i = 1; i < size - 1; i++) {
    for (let j = 1; j < size - 1; j++) {
      const idx = i * size + j

      // Calculate local slope
      const north = dem[(i - 1) * size + j]
      const south = dem[(i + 1) * size + j]
      const east = dem[i * size + (j + 1)]
      const west = dem[i * size + (j - 1)]

      const slopeX = (east - west) / 2
      const slopeY = (south - north) / 2
      const slopeMagnitude = Math.sqrt(slopeX * slopeX + slopeY * slopeY)

      // Erosion amount based on slope and rain
      const erosionAmount =
        (params.rainIntensity * slopeMagnitude * (1 - params.vegetation / 100)) /
        (1 + params.infiltrationRate)

      newErosion[idx] += erosionAmount
      newDEM[idx] -= erosionAmount * 0.1 // Scale down for stability
    }
  }

  return { dem: newDEM, erosion: newErosion }
}

/**
 * Run full simulation from parameters
 */
export async function runSimulation(
  params: SimulationParameters,
  onProgress?: (step: number, total: number) => void
): Promise<SimulationResult> {
  const startTime = Date.now()
  const { id, elevationData, erosionMap } = initializeSimulation(params)

  let currentDEM = elevationData
  let currentErosion = erosionMap

  for (let step = 0; step < params.timeSteps; step++) {
    const result = simulateErosionStep(currentDEM, currentErosion, params, step)
    currentDEM = result.dem
    currentErosion = result.erosion

    if (onProgress) {
      onProgress(step + 1, params.timeSteps)
    }

    // Small delay to allow UI updates
    await new Promise((resolve) => setTimeout(resolve, 0))
  }

  const processingTime = ((Date.now() - startTime) / 1000).toFixed(2)
  const stats = calculateSimulationStatistics(currentErosion)

  return {
    id,
    name: params.name,
    type: params.type,
    status: 'completed',
    completedAt: new Date().toISOString(),
    elevationData: currentDEM,
    erosionMap: currentErosion,
    statistics: stats,
    metadata: {
      extent: `[${params.extent.west}, ${params.extent.south}] to [${params.extent.east}, ${params.extent.north}]`,
      resolution: params.resolution,
      dataPoints: currentDEM.length,
      processingTime: `${processingTime}s`,
    },
  }
}

/**
 * Calculate statistics from erosion/elevation data
 */
export function calculateSimulationStatistics(erosionMap: Float32Array): SimulationStatistics {
  let totalErosion = 0
  let peakErosion = 0
  let count = 0
  let affectedArea = 0

  for (const value of erosionMap) {
    totalErosion += value
    peakErosion = Math.max(peakErosion, value)
    if (value > 0) {
      affectedArea++
      count++
    }
  }

  const meanErosion = count > 0 ? totalErosion / count : 0

  return {
    totalErosion,
    peakErosion,
    meanErosion,
    cumulativeMass: totalErosion, // Simplified
    affectedArea,
    averageDepth: meanErosion,
  }
}

/**
 * Export simulation results
 */
export async function exportSimulationResults(
  result: SimulationResult,
  format: 'geotiff' | 'csv' | 'json'
): Promise<Blob> {
  let blob: Blob

  if (format === 'json') {
    const data = {
      id: result.id,
      name: result.name,
      type: result.type,
      completedAt: result.completedAt,
      statistics: result.statistics,
      metadata: result.metadata,
    }
    blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  } else if (format === 'csv') {
    const lines = [
      'Statistic,Value',
      `Total Erosion,${result.statistics.totalErosion.toFixed(4)}`,
      `Peak Erosion,${result.statistics.peakErosion.toFixed(4)}`,
      `Mean Erosion,${result.statistics.meanErosion.toFixed(4)}`,
      `Affected Area,${result.statistics.affectedArea}`,
    ]
    blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  } else {
    // GeoTIFF format (simplified)
    blob = new Blob([result.erosionMap.buffer as ArrayBuffer], { type: 'image/tiff' })
  }

  return blob
}

export default {
  initializeSimulation,
  simulateErosionStep,
  runSimulation,
  calculateSimulationStatistics,
  exportSimulationResults,
}
