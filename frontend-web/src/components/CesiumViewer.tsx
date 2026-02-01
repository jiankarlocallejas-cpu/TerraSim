import React, { useEffect, useRef } from 'react'
import * as Cesium from 'cesium'
import './CesiumViewer.css'

interface CesiumViewerProps {
  terrain?: boolean
  enableDragging?: boolean
  enableZoom?: boolean
  initialLocation?: { longitude: number; latitude: number; height: number }
  onReady?: (viewer: Cesium.Viewer) => void
  children?: React.ReactNode
}

export const CesiumViewer: React.FC<CesiumViewerProps> = ({
  terrain = true,
  enableDragging = true,
  enableZoom = true,
  initialLocation = { longitude: 0, latitude: 0, height: 25000000 },
  onReady,
  children,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<Cesium.Viewer | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Set Cesium token - can be obtained from https://cesium.com/ion
    Cesium.Ion.defaultAccessToken =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyM2ZkNWFkMC1mODg1LTQ1Y2ItOTJjYi1jMTQwMTJhMTZkMjYiLCJpZCI6MjU4LCJpYXQiOjE3MzAzNTA4NDEsInNjb3BlIjpbImFzbCIsImFzdyIsImFzciIsImdjIl0sImlhdCI6MTczMDM1MDg0MSwiZXhwIjoyMzg1NzUwODQxfQ.SBWtP-1J9l2QZLKwKQZ3PYJz3JzKQCULQqmwxBhZQF8'

    const initializeViewer = async () => {
      try {
        let terrainProvider: Cesium.TerrainProvider
        if (terrain) {
          terrainProvider = await Cesium.createWorldTerrainAsync()
        } else {
          terrainProvider = new Cesium.EllipsoidTerrainProvider()
        }

        const viewer = new Cesium.Viewer(containerRef.current!, {
          // Base layers
          baseLayerPicker: true,
          geocoder: true,
          homeButton: true,
          sceneModePicker: true,
          navigationHelpButton: true,
          fullscreenButton: true,
          vrButton: false,
          animation: true,
          timeline: true,
          
          // Scene settings
          scene3DOnly: true,
          terrainProvider: terrainProvider,

          // Camera and interaction
          infoBox: true,
          selectionIndicator: true,
          shouldAnimate: true,
        })

        // Configure viewer properties
        viewer.scene.globe.depthTestAgainstTerrain = true

        // Set initial camera position
        viewer.camera.setView({
          destination: Cesium.Cartesian3.fromDegrees(
            initialLocation.longitude,
            initialLocation.latitude,
            initialLocation.height,
          ),
          orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-90),
            roll: 0,
          },
        })

        // Handle mouse wheel zoom
        if (!enableZoom) {
          viewer.scene.screenSpaceCameraController.enableZoom = false
        }

        viewerRef.current = viewer

        // Trigger callback when viewer is ready
        if (onReady) {
          onReady(viewer)
        }
      } catch (error) {
        console.error('Failed to initialize Cesium viewer:', error)
      }
    }

    initializeViewer()

    return () => {
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy()
      }
    }
  }, [terrain, enableDragging, enableZoom, initialLocation, onReady])

  return (
    <div className="cesium-viewer-container">
      <div ref={containerRef} className="cesium-viewer" />
      {children && <div className="cesium-overlay">{children}</div>}
    </div>
  )
}

export default CesiumViewer
