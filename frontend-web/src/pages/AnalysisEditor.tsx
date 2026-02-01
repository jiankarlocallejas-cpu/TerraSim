import React, { useState } from 'react'
import {
  Settings as SettingsIcon,
  PlayArrow as PlayArrowIcon,
  Save as SaveIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material'
import { CesiumViewer } from '../components/CesiumViewer'
import * as Cesium from 'cesium'
import {
  SimulationParameters,
  runSimulation,
  calculateSimulationStatistics,
} from '../services/simulationEngine'
import { extractDEMData, calculateDEMStatistics } from '../services/mapDataExtractor'

interface AnalysisConfig extends SimulationParameters {
  extent: { north: number; south: number; east: number; west: number } | null
  rainIntensity: number
  infiltrationRate: number
  vegetation: number
  slope: number
  timeStepDays: number
}

export const AnalysisEditor: React.FC = () => {
  const [config, setConfig] = useState<AnalysisConfig>({
    name: 'New Analysis',
    type: 'erosion',
    extent: null,
    resolution: 30,
    timeSteps: 100,
    rainIntensity: 10,
    infiltrationRate: 0.5,
    vegetation: 30,
    slope: 15,
    timeStepDays: 1,
  })
  const [viewer, setViewer] = useState<Cesium.Viewer | null>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [demFile, setDemFile] = useState<File | null>(null)

  const handleViewerReady = (cesiumViewer: Cesium.Viewer) => {
    setViewer(cesiumViewer)
  }

  const handleDrawRectangle = () => {
    if (!viewer) return

    setIsDrawing(true)
    let positions: Cesium.Cartesian3[] = []

    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas)

    handler.setInputAction((click: Cesium.ScreenSpaceEventHandlerOptions) => {
      const pickedObject = viewer.scene.pick(click.position)
      if (Cesium.defined(pickedObject)) {
        const cartesian = viewer.scene.pickPosition(click.position)
        if (cartesian) {
          positions.push(cartesian)
        }
      }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK)

    handler.setInputAction(() => {
      handler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK)
      handler.removeInputAction(Cesium.ScreenSpaceEventType.RIGHT_CLICK)
      setIsDrawing(false)

      if (positions.length >= 2) {
        const cartographics = positions.map((pos) =>
          Cesium.Cartographic.fromCartesian(pos),
        )
        const extent = {
          north: Math.max(...cartographics.map((c) => Cesium.Math.toDegrees(c.latitude))),
          south: Math.min(...cartographics.map((c) => Cesium.Math.toDegrees(c.latitude))),
          east: Math.max(...cartographics.map((c) => Cesium.Math.toDegrees(c.longitude))),
          west: Math.min(...cartographics.map((c) => Cesium.Math.toDegrees(c.longitude))),
        }
        setConfig({ ...config, extent })
      }
    }, Cesium.ScreenSpaceEventType.RIGHT_CLICK)
  }

  const handleDEMUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setDemFile(file)
      try {
        const result = await extractDEMData(file)
        const stats = calculateDEMStatistics(result.data)
        console.log('DEM loaded:', stats)
      } catch (error) {
        alert('Error loading DEM file')
      }
    }
  }

  const handleRunAnalysis = async () => {
    if (!config.extent) {
      alert('Please define an analysis extent on the map')
      return
    }

    setIsRunning(true)
    setProgress(0)

    try {
      const simConfig = {
        ...config,
        extent: config.extent!,
      }

      const result = await runSimulation(simConfig, (step, total) => {
        setProgress((step / total) * 100)
      })

      alert(
        `Analysis completed!\n\nTotal Erosion: ${result.statistics.totalErosion.toFixed(2)}\nPeak Erosion: ${result.statistics.peakErosion.toFixed(2)}`
      )
    } catch (error) {
      console.error('Error running analysis:', error)
      alert('Failed to run analysis')
    } finally {
      setIsRunning(false)
      setProgress(0)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100%', gap: '24px', padding: '32px', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.5) 0%, rgba(30, 41, 59, 0.5) 100%)' }}>
      {/* 3D Viewer */}
      <div style={{ flex: 1, borderRadius: '16px', overflow: 'hidden', boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)' }}>
        <CesiumViewer
          terrain={true}
          enableDragging={true}
          enableZoom={true}
          onReady={handleViewerReady}
          initialLocation={{ longitude: 0, latitude: 45, height: 5000000 }}
        />
      </div>

      {/* Configuration Panel */}
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
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.1)',
          overflow: 'auto',
          backdropFilter: 'blur(10px)',
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: '1.5rem', fontWeight: '700', background: 'linear-gradient(135deg, #00d4ff 0%, #0ea5e9 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>⚙️ Configuration</h2>

        {/* DEM Upload */}
        <div>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: '700', color: 'rgba(255, 255, 255, 0.95)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            📁 Load DEM File
          </label>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              padding: '16px',
              border: '2px dashed rgba(0, 212, 255, 0.5)',
              borderRadius: '10px',
              cursor: 'pointer',
              backgroundColor: 'rgba(0, 212, 255, 0.08)',
              transition: 'all 0.2s ease',
              backdropFilter: 'blur(4px)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(0, 212, 255, 0.12)'
              e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.7)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(0, 212, 255, 0.08)'
              e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.5)'
            }}
          >
            <CloudUploadIcon style={{ fontSize: '22px', color: 'rgb(0, 212, 255)' }} />
            <span style={{ color: demFile ? 'rgb(0, 212, 255)' : 'rgba(255, 255, 255, 0.7)', fontWeight: demFile ? '600' : '500' }}>
              {demFile ? demFile.name : 'Click or drag DEM file'}
            </span>
            <input
              type="file"
              onChange={handleDEMUpload}
              accept=".tif,.tiff,.asc,.xyz"
              style={{ display: 'none' }}
            />
          </label>
        </div>

        {/* Analysis Name */}
        <div>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: '700', color: 'rgba(255, 255, 255, 0.95)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            📝 Analysis Name
          </label>
          <input
            type="text"
            value={config.name}
            onChange={(e) => setConfig({ ...config, name: e.target.value })}
            style={{
              width: '100%',
              padding: '12px 14px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontFamily: 'inherit',
              background: 'rgba(255, 255, 255, 0.08)',
              color: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(4px)',
              transition: 'all 0.2s ease',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.5)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
            }}
            placeholder="e.g., Mountain Erosion Study"
          />
        </div>

        {/* Analysis Type */}
        <div>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: '700', color: 'rgba(255, 255, 255, 0.95)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            🔍 Analysis Type
          </label>
          <select
            value={config.type}
            onChange={(e) =>
              setConfig({
                ...config,
                type: e.target.value as AnalysisConfig['type'],
              })
            }
            style={{
              width: '100%',
              padding: '12px 14px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '8px',
              fontSize: '0.9rem',
              fontFamily: 'inherit',
              background: 'rgba(255, 255, 255, 0.08)',
              color: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(4px)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = 'rgba(0, 212, 255, 0.5)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
            }}
          >
            <option value="erosion">Erosion Modeling</option>
            <option value="deposition">Deposition Analysis</option>
            <option value="flow">Flow Direction</option>
            <option value="slope">Slope Analysis</option>
          </select>
        </div>

        {/* Physical Parameters */}
        <div style={{ paddingTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '0.95rem' }}>Physical Parameters</h3>

          <div style={{ display: 'grid', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Rain Intensity: {config.rainIntensity} mm/hr
              </label>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={config.rainIntensity}
                onChange={(e) =>
                  setConfig({ ...config, rainIntensity: parseFloat(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Vegetation Cover: {config.vegetation} %
              </label>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={config.vegetation}
                onChange={(e) =>
                  setConfig({ ...config, vegetation: parseFloat(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Infiltration Rate: {config.infiltrationRate.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.infiltrationRate}
                onChange={(e) =>
                  setConfig({ ...config, infiltrationRate: parseFloat(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Slope: {config.slope} °
              </label>
              <input
                type="range"
                min="0"
                max="90"
                step="1"
                value={config.slope}
                onChange={(e) =>
                  setConfig({ ...config, slope: parseFloat(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        {/* Simulation Parameters */}
        <div style={{ paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '0.95rem' }}>Simulation Setup</h3>

          <div style={{ display: 'grid', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Time Steps: {config.timeSteps}
              </label>
              <input
                type="range"
                min="10"
                max="1000"
                step="10"
                value={config.timeSteps}
                onChange={(e) =>
                  setConfig({ ...config, timeSteps: parseInt(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Time Step: {config.timeStepDays} days
              </label>
              <input
                type="range"
                min="0.1"
                max="365"
                step="0.1"
                value={config.timeStepDays}
                onChange={(e) =>
                  setConfig({ ...config, timeStepDays: parseFloat(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem' }}>
                Resolution: {config.resolution} m
              </label>
              <input
                type="range"
                min="10"
                max="500"
                step="10"
                value={config.resolution}
                onChange={(e) =>
                  setConfig({ ...config, resolution: parseInt(e.target.value) })
                }
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        {/* Extent Display */}
        {config.extent && (
          <div
            style={{
              padding: '12px',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '6px',
              fontSize: '0.85rem',
            }}
          >
            <p style={{ margin: '0 0 8px 0', fontWeight: '600' }}>✓ Extent Defined</p>
            <p style={{ margin: '4px 0' }}>
              N: {config.extent.north.toFixed(2)}° S: {config.extent.south.toFixed(2)}°
            </p>
            <p style={{ margin: '4px 0' }}>
              E: {config.extent.east.toFixed(2)}° W: {config.extent.west.toFixed(2)}°
            </p>
          </div>
        )}

        {/* Progress Bar */}
        {isRunning && (
          <div
            style={{
              padding: '14px',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '10px',
              backdropFilter: 'blur(4px)',
            }}
          >
            <p style={{ margin: '0 0 10px 0', fontWeight: '700', color: 'rgb(59, 130, 246)', fontSize: '0.9rem' }}>
              ⚡ Running Analysis: {Math.round(progress)}%
            </p>
            <div
              style={{
                width: '100%',
                height: '8px',
                background: 'rgba(59, 130, 246, 0.15)',
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${progress}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, rgb(59, 130, 246), rgb(0, 212, 255))',
                  transition: 'width 0.3s',
                }}
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', flexDirection: 'column', marginTop: 'auto' }}>
          <button
            onClick={handleDrawRectangle}
            disabled={isDrawing || isRunning}
            style={{
              padding: '12px 16px',
              background: isDrawing || isRunning ? 'rgba(156, 163, 175, 0.5)' : 'linear-gradient(135deg, rgb(59, 130, 246) 0%, rgb(37, 99, 235) 100%)',
              color: 'white',
              border: '1px solid ' + (isDrawing || isRunning ? 'rgba(156, 163, 175, 0.3)' : 'rgba(59, 130, 246, 0.4)'),
              borderRadius: '10px',
              cursor: isDrawing || isRunning ? 'not-allowed' : 'pointer',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '0.95rem',
              transition: 'all 0.2s ease',
              opacity: isDrawing || isRunning ? 0.6 : 1,
            }}
          >
            <SettingsIcon style={{ fontSize: '18px' }} />
            {isDrawing ? 'Click Map to Define' : 'Define Extent on Map'}
          </button>

          <button
            onClick={handleRunAnalysis}
            disabled={isRunning}
            style={{
              padding: '12px 16px',
              background: isRunning ? 'rgba(156, 163, 175, 0.5)' : 'linear-gradient(135deg, rgb(16, 185, 129) 0%, rgb(5, 150, 105) 100%)',
              color: 'white',
              border: '1px solid ' + (isRunning ? 'rgba(156, 163, 175, 0.3)' : 'rgba(16, 185, 129, 0.4)'),
              borderRadius: '6px',
              cursor: isRunning ? 'not-allowed' : 'pointer',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '0.95rem',
              transition: 'all 0.2s ease',
              opacity: isRunning ? 0.6 : 1,
            }}
          >
            <PlayArrowIcon style={{ fontSize: '18px' }} />
            {isRunning ? 'Running...' : 'Run Analysis'}
          </button>

          <button
            style={{
              padding: '12px 16px',
              background: 'linear-gradient(135deg, rgba(156, 163, 175, 0.4) 0%, rgba(107, 114, 128, 0.3) 100%)',
              color: 'rgba(255, 255, 255, 0.9)',
              border: '1px solid rgba(156, 163, 175, 0.3)',
              borderRadius: '10px',
              cursor: 'pointer',
              fontWeight: '700',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              fontSize: '0.95rem',
              transition: 'all 0.2s ease',
            }}
          >
            <SaveIcon style={{ fontSize: '18px' }} />
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  )
}

