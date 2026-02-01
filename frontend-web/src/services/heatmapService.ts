/**
 * Heatmap and Visualization Service
 * Generates heatmaps, contours, and various visualization outputs
 */

export interface HeatmapData {
  values: Float32Array
  colorMap: string
  min: number
  max: number
  title: string
}

export interface ContourData {
  levels: number[]
  geometries: ContourGeometry[]
}

export interface ContourGeometry {
  level: number
  coordinates: [number, number][]
}

/**
 * Generate heatmap visualization data from elevation or erosion map
 */
export function generateHeatmap(
  data: Float32Array,
  colorMap: 'viridis' | 'plasma' | 'terrain' | 'jet' = 'viridis',
  title: string = 'Heatmap'
): HeatmapData {
  const min = Math.min(...data)
  const max = Math.max(...data)

  return {
    values: data,
    colorMap,
    min,
    max,
    title,
  }
}

/**
 * Generate contour lines from data
 */
export function generateContours(
  data: Float32Array,
  size: number,
  numLevels: number = 10
): ContourData {
  const min = Math.min(...data)
  const max = Math.max(...data)
  const levels: number[] = []

  for (let i = 0; i < numLevels; i++) {
    levels.push(min + ((max - min) / numLevels) * i)
  }

  const geometries: ContourGeometry[] = []

  for (const level of levels) {
    const coords: [number, number][] = []

    for (let i = 0; i < size; i++) {
      for (let j = 0; j < size; j++) {
        const idx = i * size + j
        const val = data[idx]

        // Simple contour detection
        if (Math.abs(val - level) < (max - min) / (numLevels * 10)) {
          coords.push([i, j])
        }
      }
    }

    if (coords.length > 0) {
      geometries.push({ level, coordinates: coords })
    }
  }

  return { levels, geometries }
}

/**
 * Generate slope map
 */
export function generateSlopeMap(dem: Float32Array, size: number): Float32Array {
  const slope = new Float32Array(dem.length)

  for (let i = 1; i < size - 1; i++) {
    for (let j = 1; j < size - 1; j++) {
      const idx = i * size + j

      const north = dem[(i - 1) * size + j]
      const south = dem[(i + 1) * size + j]
      const east = dem[i * size + (j + 1)]
      const west = dem[i * size + (j - 1)]

      const slopeX = (east - west) / 2
      const slopeY = (south - north) / 2
      const slopeMag = Math.sqrt(slopeX * slopeX + slopeY * slopeY)

      slope[idx] = Math.atan(slopeMag) * (180 / Math.PI) // Convert to degrees
    }
  }

  return slope
}

/**
 * Generate aspect map (direction of steepest descent)
 */
export function generateAspectMap(dem: Float32Array, size: number): Float32Array {
  const aspect = new Float32Array(dem.length)

  for (let i = 1; i < size - 1; i++) {
    for (let j = 1; j < size - 1; j++) {
      const idx = i * size + j

      const north = dem[(i - 1) * size + j]
      const south = dem[(i + 1) * size + j]
      const east = dem[i * size + (j + 1)]
      const west = dem[i * size + (j - 1)]

      const slopeX = (east - west) / 2
      const slopeY = (south - north) / 2

      let aspectVal = Math.atan2(slopeX, slopeY) * (180 / Math.PI)
      if (aspectVal < 0) {
        aspectVal += 360
      }

      aspect[idx] = aspectVal
    }
  }

  return aspect
}

/**
 * Generate hillshade from DEM
 */
export function generateHillshade(
  dem: Float32Array,
  size: number,
  azimuth: number = 315,
  elevation: number = 45
): Float32Array {
  const hillshade = new Float32Array(dem.length)
  const azRad = (azimuth * Math.PI) / 180
  const elRad = (elevation * Math.PI) / 180

  for (let i = 1; i < size - 1; i++) {
    for (let j = 1; j < size - 1; j++) {
      const idx = i * size + j

      const center = dem[idx]
      const north = dem[(i - 1) * size + j]
      const east = dem[i * size + (j + 1)]

      const slopeX = Math.atan((east - center) / 1)
      const slopeY = Math.atan((north - center) / 1)

      const aspect = Math.atan2(slopeY, slopeX)
      const slope = Math.sqrt(slopeX * slopeX + slopeY * slopeY)

      const shading = Math.sin(elRad) * Math.cos(slope) +
        Math.cos(elRad) * Math.sin(slope) * Math.cos(azRad - aspect - Math.PI / 2)

      hillshade[idx] = (shading + 1) / 2 // Normalize to 0-1
    }
  }

  return hillshade
}

/**
 * Generate flow direction map
 */
export function generateFlowDirectionMap(dem: Float32Array, size: number): Float32Array {
  const flow = new Float32Array(dem.length)

  for (let i = 1; i < size - 1; i++) {
    for (let j = 1; j < size - 1; j++) {
      const idx = i * size + j
      const center = dem[idx]

      // 8-directional flow
      const directions = [
        { di: -1, dj: 0, value: 1 }, // N
        { di: -1, dj: 1, value: 2 }, // NE
        { di: 0, dj: 1, value: 4 }, // E
        { di: 1, dj: 1, value: 8 }, // SE
        { di: 1, dj: 0, value: 16 }, // S
        { di: 1, dj: -1, value: 32 }, // SW
        { di: 0, dj: -1, value: 64 }, // W
        { di: -1, dj: -1, value: 128 }, // NW
      ]

      let maxSlope = 0
      let flowDir = 0

      for (const dir of directions) {
        const ni = i + dir.di
        const nj = j + dir.dj
        const neighbor = dem[ni * size + nj]
        const slope = (center - neighbor) / Math.sqrt(dir.di * dir.di + dir.dj * dir.dj)

        if (slope > maxSlope) {
          maxSlope = slope
          flowDir = dir.value
        }
      }

      flow[idx] = flowDir
    }
  }

  return flow
}

/**
 * Generate color map visualization
 */
export function mapValueToColor(
  value: number,
  min: number,
  max: number,
  colorMap: string
): [number, number, number, number] {
  const normalized = (value - min) / (max - min)
  const clamped = Math.max(0, Math.min(1, normalized))

  // Define some common colormaps
  const colormaps: Record<string, (t: number) => [number, number, number, number]> = {
    viridis: (t) => [
      Math.round(68 + (t * (69 - 68)) * 10),
      Math.round(1 + (t * (184 - 1)) * 10),
      Math.round(84 + (t * (216 - 84)) * 10),
      255,
    ] as [number, number, number, number],

    plasma: (t) => [
      Math.round(13 + t * (255 - 13)),
      Math.round(8 + t * (255 - 8)),
      Math.round(135 + t * (50 - 135)),
      255,
    ] as [number, number, number, number],

    terrain: (t) => {
      if (t < 0.25) {
        const c = t / 0.25
        return [Math.round(0 + c * 100), Math.round(100 + c * 50), Math.round(200), 255]
      } else if (t < 0.5) {
        const c = (t - 0.25) / 0.25
        return [Math.round(100 + c * 100), Math.round(150 + c * 50), Math.round(200 - c * 100), 255]
      } else if (t < 0.75) {
        const c = (t - 0.5) / 0.25
        return [Math.round(200 + c * 50), Math.round(200 - c * 100), Math.round(100 - c * 50), 255]
      } else {
        const c = (t - 0.75) / 0.25
        return [Math.round(250 - c * 50), Math.round(100 - c * 50), Math.round(50 - c * 50), 255]
      }
    },

    jet: (t) => {
      let r, g, b
      if (t < 0.125) {
        r = 0
        g = 0
        b = Math.round(255 * (0.5 + 0.5 * (t / 0.125)))
      } else if (t < 0.375) {
        r = 0
        g = Math.round(255 * ((t - 0.125) / 0.25))
        b = 255
      } else if (t < 0.625) {
        r = Math.round(255 * ((t - 0.375) / 0.25))
        g = 255
        b = Math.round(255 * (1 - (t - 0.375) / 0.25))
      } else if (t < 0.875) {
        r = 255
        g = Math.round(255 * (1 - (t - 0.625) / 0.25))
        b = 0
      } else {
        r = Math.round(255 * (1 - (t - 0.875) / 0.125))
        g = 0
        b = 0
      }
      return [r, g, b, 255]
    },
  }

  const mapFunc = colormaps[colorMap] || colormaps.viridis
  return mapFunc(clamped)
}

export default {
  generateHeatmap,
  generateContours,
  generateSlopeMap,
  generateAspectMap,
  generateHillshade,
  generateFlowDirectionMap,
  mapValueToColor,
}
