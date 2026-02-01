/**
 * Map Data Extraction Service
 * Handles loading, processing, and extracting geospatial data
 */

export interface MapDataType {
  dem?: Float32Array
  vector?: GeoJSONFeature[]
  pointCloud?: Point3D[]
  metadata?: MapMetadata
}

export interface GeoJSONFeature {
  type: 'Feature'
  geometry: {
    type: 'Point' | 'LineString' | 'Polygon'
    coordinates: number[] | number[][] | number[][][]
  }
  properties: Record<string, any>
}

export interface Point3D {
  x: number
  y: number
  z: number
  intensity?: number
}

export interface MapMetadata {
  extent: [number, number, number, number] // [minX, minY, maxX, maxY]
  crs: string
  resolution: number
  noDataValue: number
  minValue: number
  maxValue: number
}

/**
 * Extract DEM data from various sources
 */
export async function extractDEMData(
  source: File | string
): Promise<{ data: Float32Array; metadata: MapMetadata }> {
  try {
    let data: Float32Array
    let metadata: MapMetadata

    if (typeof source === 'string') {
      // Cloud-based extraction (e.g., Copernicus, USGS)
      const response = await fetch(source)
      const buffer = await response.arrayBuffer()
      data = new Float32Array(buffer)
      metadata = {
        extent: [0, 0, 100, 100],
        crs: 'EPSG:4326',
        resolution: 30,
        noDataValue: -9999,
        minValue: Math.min(...data),
        maxValue: Math.max(...data),
      }
    } else {
      // Local file processing
      const arrayBuffer = await source.arrayBuffer()
      data = new Float32Array(arrayBuffer)
      metadata = {
        extent: [0, 0, 100, 100],
        crs: 'EPSG:4326',
        resolution: 30,
        noDataValue: -9999,
        minValue: Math.min(...data),
        maxValue: Math.max(...data),
      }
    }

    return { data, metadata }
  } catch (error) {
    console.error('Error extracting DEM data:', error)
    throw error
  }
}

/**
 * Extract vector layer data (shapefiles, GeoJSON)
 */
export async function extractVectorData(source: File | string): Promise<GeoJSONFeature[]> {
  try {
    let features: GeoJSONFeature[] = []

    if (typeof source === 'string') {
      const response = await fetch(source)
      const geojson = await response.json()
      features = geojson.features || []
    } else {
      const text = await source.text()
      const geojson = JSON.parse(text)
      features = geojson.features || []
    }

    return features
  } catch (error) {
    console.error('Error extracting vector data:', error)
    throw error
  }
}

/**
 * Extract point cloud data (LAS, XYZ formats)
 */
export async function extractPointCloudData(source: File): Promise<Point3D[]> {
  try {
    const arrayBuffer = await source.arrayBuffer()
    const view = new DataView(arrayBuffer)
    const points: Point3D[] = []

    // Simple XYZ format parsing (12 bytes per point: 3x float32)
    const pointCount = arrayBuffer.byteLength / 12
    for (let i = 0; i < pointCount; i++) {
      const offset = i * 12
      const x = view.getFloat32(offset, true)
      const y = view.getFloat32(offset + 4, true)
      const z = view.getFloat32(offset + 8, true)
      points.push({ x, y, z })
    }

    return points
  } catch (error) {
    console.error('Error extracting point cloud:', error)
    throw error
  }
}

/**
 * Resample DEM to different resolution
 */
export function resampleDEM(
  data: Float32Array,
  originalSize: number,
  targetResolution: number
): Float32Array {
  const scale = targetResolution / 100 // Default resolution is 100m
  const newSize = Math.floor(originalSize / scale)
  const resampled = new Float32Array(newSize * newSize)

  for (let i = 0; i < newSize; i++) {
    for (let j = 0; j < newSize; j++) {
      const origI = Math.floor(i * scale)
      const origJ = Math.floor(j * scale)
      const origIdx = origI * originalSize + origJ
      resampled[i * newSize + j] = data[origIdx] || 0
    }
  }

  return resampled
}

/**
 * Calculate statistics from DEM
 */
export function calculateDEMStatistics(data: Float32Array): {
  min: number
  max: number
  mean: number
  stdDev: number
  noDataCount: number
} {
  let min = Infinity
  let max = -Infinity
  let sum = 0
  let count = 0
  let noDataCount = 0
  const noDataValue = -9999

  for (const value of data) {
    if (value === noDataValue) {
      noDataCount++
      continue
    }
    min = Math.min(min, value)
    max = Math.max(max, value)
    sum += value
    count++
  }

  const mean = count > 0 ? sum / count : 0
  let variance = 0

  for (const value of data) {
    if (value !== noDataValue) {
      variance += Math.pow(value - mean, 2)
    }
  }

  const stdDev = count > 0 ? Math.sqrt(variance / count) : 0

  return { min, max, mean, stdDev, noDataCount }
}

export default {
  extractDEMData,
  extractVectorData,
  extractPointCloudData,
  resampleDEM,
  calculateDEMStatistics,
}
