/**
 * Custom React Hooks for TerraSim operations
 * Provides convenient wrappers around simulation and analysis services
 */

import { useState, useCallback } from 'react'
import { SimulationParameters, SimulationResult, runSimulation } from '../services/simulationEngine'
import { extractDEMData, calculateDEMStatistics } from '../services/mapDataExtractor'
import { generateHeatmap, generateContours, generateSlopeMap } from '../services/heatmapService'

/**
 * Hook for managing simulation state and execution
 */
export function useSimulation() {
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(
    async (config: SimulationParameters) => {
      setIsRunning(true)
      setError(null)
      setProgress(0)

      try {
        const simResult = await runSimulation(config, (step, total) => {
          setProgress((step / total) * 100)
        })
        setResult(simResult)
        return simResult
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setError(message)
        throw err
      } finally {
        setIsRunning(false)
      }
    },
    []
  )

  const reset = useCallback(() => {
    setResult(null)
    setProgress(0)
    setError(null)
  }, [])

  return { result, isRunning, progress, error, execute, reset }
}

/**
 * Hook for loading and processing DEM data
 */
export function useDEMLoader() {
  const [dem, setDEM] = useState<Float32Array | null>(null)
  const [metadata, setMetadata] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (file: File) => {
    setLoading(true)
    setError(null)

    try {
      const result = await extractDEMData(file, 'ascii')
      setDEM(result.data)
      setMetadata(result.metadata)

      const demStats = calculateDEMStatistics(result.data)
      setStats(demStats)

      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load DEM'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const clear = useCallback(() => {
    setDEM(null)
    setMetadata(null)
    setStats(null)
  }, [])

  return { dem, metadata, stats, loading, error, load, clear }
}

/**
 * Hook for generating visualization maps
 */
export function useVisualization() {
  const [heatmapData, setHeatmapData] = useState<any>(null)
  const [contours, setContours] = useState<any>(null)
  const [slopeMap, setSlopeMap] = useState<Float32Array | null>(null)

  const generateHeatmapViz = useCallback(
    (data: Float32Array, colorMap: string = 'viridis', title: string = 'Heatmap') => {
      try {
        const viz = generateHeatmap(data, colorMap as any, title)
        setHeatmapData(viz)
        return viz
      } catch (err) {
        console.error('Error generating heatmap:', err)
        throw err
      }
    },
    []
  )

  const generateContoursViz = useCallback(
    (data: Float32Array, size: number, numLevels: number = 10) => {
      try {
        const viz = generateContours(data, size, numLevels)
        setContours(viz)
        return viz
      } catch (err) {
        console.error('Error generating contours:', err)
        throw err
      }
    },
    []
  )

  const generateSlopeViz = useCallback((dem: Float32Array, size: number) => {
    try {
      const viz = generateSlopeMap(dem, size)
      setSlopeMap(viz)
      return viz
    } catch (err) {
      console.error('Error generating slope map:', err)
      throw err
    }
  }, [])

  const clear = useCallback(() => {
    setHeatmapData(null)
    setContours(null)
    setSlopeMap(null)
  }, [])

  return {
    heatmapData,
    contours,
    slopeMap,
    loading,
    generateHeatmapViz,
    generateContoursViz,
    generateSlopeViz,
    clear,
  }
}

/**
 * Hook for managing analysis history
 */
export function useAnalysisHistory() {
  const [history, setHistory] = useState<SimulationResult[]>([])

  const add = useCallback((result: SimulationResult) => {
    setHistory((prev) => [result, ...prev])
    // Save to localStorage
    try {
      const saved = JSON.stringify([result, ...history])
      localStorage.setItem('terrasim_history', saved)
    } catch (err) {
      console.warn('Could not save to localStorage:', err)
    }
  }, [history])

  const remove = useCallback((id: string) => {
    setHistory((prev) => prev.filter((r) => r.id !== id))
  }, [])

  const clear = useCallback(() => {
    setHistory([])
    localStorage.removeItem('terrasim_history')
  }, [])

  const load = useCallback(() => {
    try {
      const saved = localStorage.getItem('terrasim_history')
      if (saved) {
        setHistory(JSON.parse(saved))
      }
    } catch (err) {
      console.warn('Could not load from localStorage:', err)
    }
  }, [])

  return { history, add, remove, clear, load }
}

/**
 * Hook for form state management
 */
export function useAnalysisForm(initialValues: SimulationParameters) {
  const [values, setValues] = useState(initialValues)
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { name, value, type } = e.target
      const parsedValue = type === 'number' ? parseFloat(value) : value
      setValues((prev) => ({ ...prev, [name]: parsedValue }))
    },
    []
  )

  const handleBlur = useCallback((e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name } = e.target
    setTouched((prev) => ({ ...prev, [name]: true }))
  }, [])

  const validate = useCallback(() => {
    const newErrors: Record<string, string> = {}

    if (!values.name || values.name.trim() === '') {
      newErrors.name = 'Name is required'
    }

    if (!values.extent) {
      newErrors.extent = 'Analysis extent must be defined'
    }

    if (values.resolution < 10 || values.resolution > 500) {
      newErrors.resolution = 'Resolution must be between 10 and 500'
    }

    if (values.timeSteps < 10) {
      newErrors.timeSteps = 'Must have at least 10 time steps'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [values])

  const reset = useCallback(() => {
    setValues(initialValues)
    setTouched({})
    setErrors({})
  }, [initialValues])

  return { values, touched, errors, handleChange, handleBlur, validate, reset, setValues }
}

/**
 * Hook for async data fetching with caching
 */
export function useCachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: { ttl?: number }
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetch = useCallback(async () => {
    const cacheKey = `cache_${key}`

    // Check cache
    try {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        const { data: cachedData, timestamp } = JSON.parse(cached)
        const ttl = options?.ttl || 3600000 // 1 hour default
        if (Date.now() - timestamp < ttl) {
          setData(cachedData)
          return
        }
      }
    } catch (err) {
      console.warn('Cache read failed:', err)
    }

    setLoading(true)
    setError(null)

    try {
      const result = await fetcher()
      setData(result)

      // Save to cache
      try {
        localStorage.setItem(
          cacheKey,
          JSON.stringify({ data: result, timestamp: Date.now() })
        )
      } catch (err) {
        console.warn('Cache write failed:', err)
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }, [key, fetcher, options?.ttl])

  const clearCache = useCallback(() => {
    localStorage.removeItem(`cache_${key}`)
    setData(null)
  }, [key])

  return { data, loading, error, fetch, clearCache }
}

export default {
  useSimulation,
  useDEMLoader,
  useVisualization,
  useAnalysisHistory,
  useAnalysisForm,
  useCachedFetch,
}
