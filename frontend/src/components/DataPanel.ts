/**
 * TerraSim Data Panel Component
 * GIS data management and layer control
 */

import { EventBus } from '../utils/EventBus';
import { ApiService } from '../services/ApiService';

interface LayerConfig {
  id: string;
  name: string;
  type: 'vector' | 'raster';
  source: string;
  visible: boolean;
  opacity: number;
  style?: any;
  metadata?: Record<string, any>;
  bounds?: [number, number, number, number];
}

interface DataStats {
  features?: number;
  columns?: string[];
  width?: number;
  height?: number;
  bands?: number;
  crs?: string;
}

export class DataPanel {
  private container!: HTMLElement;
  private eventBus: EventBus;
  private apiService: ApiService;
  private layers: Map<string, LayerConfig>;
  private selectedLayer: string | null;

  constructor(eventBus: EventBus, apiService: ApiService) {
    this.eventBus = eventBus;
    this.apiService = apiService;
    this.layers = new Map();
    this.selectedLayer = null;
  }

  public mount(selector: string): void {
    const container = document.querySelector(selector) as HTMLElement;
    if (!container) {
      throw new Error(`Data panel container ${selector} not found`);
    }

    this.container = container;
    this.render();
    this.setupEventListeners();
    this.loadSavedLayers();
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="data-panel">
        <div class="panel-header">
          <h3>Data Layers</h3>
          <button id="toggle-data-panel" class="toggle-btn">−</button>
        </div>
        
        <div class="panel-content">
          <div class="data-actions">
            <button id="add-vector-btn" class="btn btn-primary btn-sm">
              <span class="icon">📁</span> Add Vector
            </button>
            <button id="add-raster-btn" class="btn btn-primary btn-sm">
              <span class="icon">🗺️</span> Add Raster
            </button>
            <button id="add-wms-btn" class="btn btn-outline btn-sm">
              <span class="icon">🌐</span> Add WMS
            </button>
          </div>
          
          <div class="layer-search">
            <input type="text" id="layer-search" placeholder="Search layers..." />
          </div>
          
          <div class="layer-categories">
            <div class="category">
              <h4>Base Layers</h4>
              <div id="base-layers" class="layer-list">
                <div class="layer-item" data-layer-id="osm">
                  <div class="layer-info">
                    <input type="checkbox" id="osm-visible" checked />
                    <label for="osm-visible">OpenStreetMap</label>
                  </div>
                  <div class="layer-controls">
                    <button class="btn-icon" title="Layer properties">⚙️</button>
                  </div>
                </div>
                
                <div class="layer-item" data-layer-id="satellite">
                  <div class="layer-info">
                    <input type="checkbox" id="satellite-visible" />
                    <label for="satellite-visible">Satellite Imagery</label>
                  </div>
                  <div class="layer-controls">
                    <button class="btn-icon" title="Layer properties">⚙️</button>
                  </div>
                </div>
                
                <div class="layer-item" data-layer-id="terrain">
                  <div class="layer-info">
                    <input type="checkbox" id="terrain-visible" />
                    <label for="terrain-visible">Terrain</label>
                  </div>
                  <div class="layer-controls">
                    <button class="btn-icon" title="Layer properties">⚙️</button>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="category">
              <h4>Data Layers</h4>
              <div id="data-layers" class="layer-list">
                <!-- Dynamic layers will be added here -->
              </div>
            </div>
            
            <div class="category">
              <h4>Analysis Layers</h4>
              <div id="analysis-layers" class="layer-list">
                <!-- Analysis results will be added here -->
              </div>
            </div>
          </div>
          
          <div id="layer-properties" class="layer-properties hidden">
            <h4>Layer Properties</h4>
            <div id="properties-content"></div>
          </div>
        </div>
      </div>
    `;
  }

  private setupEventListeners(): void {
    // Panel toggle
    const toggleBtn = this.container.querySelector('#toggle-data-panel') as HTMLButtonElement;
    const panelContent = this.container.querySelector('.panel-content') as HTMLElement;
    
    toggleBtn.addEventListener('click', () => {
      panelContent.classList.toggle('hidden');
      toggleBtn.textContent = panelContent.classList.contains('hidden') ? '+' : '−';
    });

    // Add data buttons
    const addVectorBtn = this.container.querySelector('#add-vector-btn') as HTMLButtonElement;
    const addRasterBtn = this.container.querySelector('#add-raster-btn') as HTMLButtonElement;
    const addWMSBtn = this.container.querySelector('#add-wms-btn') as HTMLButtonElement;

    addVectorBtn.addEventListener('click', () => this.addVectorLayer());
    addRasterBtn.addEventListener('click', () => this.addRasterLayer());
    addWMSBtn.addEventListener('click', () => this.addWMSLayer());

    // Layer search
    const searchInput = this.container.querySelector('#layer-search') as HTMLInputElement;
    searchInput.addEventListener('input', (e) => {
      this.filterLayers((e.target as HTMLInputElement).value);
    });

    // Base layer toggles
    this.setupBaseLayerListeners();

    // Setup event listeners for dynamic layers
    this.container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      
      if (target.classList.contains('layer-visibility')) {
        this.toggleLayerVisibility(target.dataset.layerId!);
      }
      
      if (target.classList.contains('layer-opacity')) {
        this.updateLayerOpacity(target.dataset.layerId!, parseFloat((target as HTMLInputElement).value));
      }
      
      if (target.classList.contains('layer-remove')) {
        this.removeLayer(target.dataset.layerId!);
      }
      
      if (target.classList.contains('layer-properties-btn')) {
        this.showLayerProperties(target.dataset.layerId!);
      }
    });

    // Listen for layer events
    this.eventBus.on('layer:added', (layer: LayerConfig) => {
      this.addLayerToList(layer);
    });

    this.eventBus.on('layer:removed', (layerId: string) => {
      this.removeLayerFromList(layerId);
    });

    this.eventBus.on('layer:updated', (layer: LayerConfig) => {
      this.updateLayerInList(layer);
    });
  }

  private setupBaseLayerListeners(): void {
    const baseLayers = ['osm', 'satellite', 'terrain'];
    
    baseLayers.forEach(layerId => {
      const checkbox = this.container.querySelector(`#${layerId}-visible`) as HTMLInputElement;
      if (checkbox) {
        checkbox.addEventListener('change', (e) => {
          const target = e.target as HTMLInputElement;
          this.eventBus.emit('base-layer:toggle', {
            id: layerId,
            visible: target.checked
          });
        });
      }
    });
  }

  private async addVectorLayer(): Promise<void> {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.shp,.geojson,.kml,.gpkg,.csv';
    
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', 'vector');

        const response = await this.apiService.post('/api/gis/upload', formData);
        
        if (response.success) {
          const layer: LayerConfig = {
            id: `vector_${Date.now()}`,
            name: file.name.replace(/\.[^/.]+$/, ''),
            type: 'vector',
            source: 'file',
            visible: true,
            opacity: 1.0,
            metadata: response.data
          };

          this.layers.set(layer.id, layer);
          this.addLayerToList(layer);
          this.eventBus.emit('layer:added', layer);
          
          this.eventBus.emit('notification:show', {
            type: 'success',
            message: `Vector layer "${layer.name}" added successfully`
          });
        } else {
          throw new Error(response.error || 'Upload failed');
        }
      } catch (error) {
        console.error('Vector layer upload error:', error);
        this.eventBus.emit('notification:show', {
          type: 'error',
          message: 'Failed to upload vector layer'
        });
      }
    };

    input.click();
  }

  private async addRasterLayer(): Promise<void> {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.tif,.tiff,.img,.dem,.jpg,.png';
    
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', 'raster');

        const response = await this.apiService.post('/api/gis/upload', formData);
        
        if (response.success) {
          const layer: LayerConfig = {
            id: `raster_${Date.now()}`,
            name: file.name.replace(/\.[^/.]+$/, ''),
            type: 'raster',
            source: 'file',
            visible: true,
            opacity: 0.8,
            metadata: response.data,
            bounds: response.data.bounds
          };

          this.layers.set(layer.id, layer);
          this.addLayerToList(layer);
          this.eventBus.emit('layer:added', layer);
          
          this.eventBus.emit('notification:show', {
            type: 'success',
            message: `Raster layer "${layer.name}" added successfully`
          });
        } else {
          throw new Error(response.error || 'Upload failed');
        }
      } catch (error) {
        console.error('Raster layer upload error:', error);
        this.eventBus.emit('notification:show', {
          type: 'error',
          message: 'Failed to upload raster layer'
        });
      }
    };

    input.click();
  }

  private addWMSLayer(): void {
    // Create WMS dialog
    const dialog = document.createElement('div');
    dialog.className = 'modal';
    dialog.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h3>Add WMS Layer</h3>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="wms-name">Layer Name</label>
            <input type="text" id="wms-name" placeholder="Enter layer name" />
          </div>
          <div class="form-group">
            <label for="wms-url">WMS URL</label>
            <input type="url" id="wms-url" placeholder="https://example.com/geoserver/wms" />
          </div>
          <div class="form-group">
            <label for="wms-layers">Layer Names</label>
            <input type="text" id="wms-layers" placeholder="layer1,layer2,layer3" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" id="wms-cancel">Cancel</button>
          <button class="btn btn-primary" id="wms-add">Add Layer</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    // Setup dialog handlers
    const closeBtn = dialog.querySelector('.modal-close') as HTMLButtonElement;
    const cancelBtn = dialog.querySelector('#wms-cancel') as HTMLButtonElement;
    const addBtn = dialog.querySelector('#wms-add') as HTMLButtonElement;

    const closeDialog = () => {
      document.body.removeChild(dialog);
    };

    closeBtn.addEventListener('click', closeDialog);
    cancelBtn.addEventListener('click', closeDialog);

    addBtn.addEventListener('click', () => {
      const name = (dialog.querySelector('#wms-name') as HTMLInputElement).value;
      const url = (dialog.querySelector('#wms-url') as HTMLInputElement).value;
      const layers = (dialog.querySelector('#wms-layers') as HTMLInputElement).value;

      if (!name || !url || !layers) {
        this.eventBus.emit('notification:show', {
          type: 'error',
          message: 'Please fill in all fields'
        });
        return;
      }

      const wmsLayer: LayerConfig = {
        id: `wms_${Date.now()}`,
        name: name,
        type: 'raster',
        source: 'wms',
        visible: true,
        opacity: 1.0,
        metadata: { url, layers }
      };

      this.layers.set(wmsLayer.id, wmsLayer);
      this.addLayerToList(wmsLayer);
      this.eventBus.emit('layer:added', wmsLayer);
      
      this.eventBus.emit('notification:show', {
        type: 'success',
        message: `WMS layer "${name}" added successfully`
      });

      closeDialog();
    });
  }

  private addLayerToList(layer: LayerConfig): void {
    const dataLayersList = this.container.querySelector('#data-layers') as HTMLElement;
    
    const layerElement = document.createElement('div');
    layerElement.className = 'layer-item';
    layerElement.dataset.layerId = layer.id;
    
    layerElement.innerHTML = `
      <div class="layer-info">
        <input type="checkbox" class="layer-visibility" data-layer-id="${layer.id}" 
               ${layer.visible ? 'checked' : ''} />
        <label for="${layer.id}-visible">${layer.name}</label>
        <span class="layer-type">${layer.type}</span>
      </div>
      <div class="layer-controls">
        <input type="range" class="layer-opacity" data-layer-id="${layer.id}" 
               min="0" max="1" step="0.1" value="${layer.opacity}" 
               title="Opacity" />
        <button class="btn-icon layer-properties-btn" data-layer-id="${layer.id}" 
                title="Properties">⚙️</button>
        <button class="btn-icon layer-remove" data-layer-id="${layer.id}" 
                title="Remove layer">🗑️</button>
      </div>
    `;
    
    dataLayersList.appendChild(layerElement);
  }

  private removeLayerFromList(layerId: string): void {
    const layerElement = this.container.querySelector(`[data-layer-id="${layerId}"]`);
    if (layerElement) {
      layerElement.remove();
    }
  }

  private updateLayerInList(layer: LayerConfig): void {
    const layerElement = this.container.querySelector(`[data-layer-id="${layer.id}"]`);
    if (layerElement) {
      const checkbox = layerElement.querySelector('.layer-visibility') as HTMLInputElement;
      const opacitySlider = layerElement.querySelector('.layer-opacity') as HTMLInputElement;
      
      if (checkbox) checkbox.checked = layer.visible;
      if (opacitySlider) opacitySlider.value = layer.opacity.toString();
    }
  }

  private toggleLayerVisibility(layerId: string): void {
    const layer = this.layers.get(layerId);
    if (layer) {
      layer.visible = !layer.visible;
      this.eventBus.emit('layer:visibility:changed', layer);
    }
  }

  private updateLayerOpacity(layerId: string, opacity: number): void {
    const layer = this.layers.get(layerId);
    if (layer) {
      layer.opacity = opacity;
      this.eventBus.emit('layer:opacity:changed', layer);
    }
  }

  private removeLayer(layerId: string): void {
    if (confirm('Are you sure you want to remove this layer?')) {
      this.layers.delete(layerId);
      this.removeLayerFromList(layerId);
      this.eventBus.emit('layer:removed', layerId);
      
      this.eventBus.emit('notification:show', {
        type: 'info',
        message: 'Layer removed'
      });
    }
  }

  private showLayerProperties(layerId: string): void {
    const layer = this.layers.get(layerId);
    if (!layer) return;

    const propertiesDiv = this.container.querySelector('#layer-properties') as HTMLElement;
    const propertiesContent = this.container.querySelector('#properties-content') as HTMLElement;
    
    propertiesContent.innerHTML = `
      <div class="property-group">
        <h5>Basic Information</h5>
        <div class="property">
          <span class="property-name">Name:</span>
          <span class="property-value">${layer.name}</span>
        </div>
        <div class="property">
          <span class="property-name">Type:</span>
          <span class="property-value">${layer.type}</span>
        </div>
        <div class="property">
          <span class="property-name">Source:</span>
          <span class="property-value">${layer.source}</span>
        </div>
      </div>
      
      ${layer.metadata ? `
        <div class="property-group">
          <h5>Metadata</h5>
          ${Object.entries(layer.metadata).map(([key, value]) => `
            <div class="property">
              <span class="property-name">${key}:</span>
              <span class="property-value">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}
      
      <div class="property-actions">
        <button class="btn btn-outline" id="zoom-to-layer-btn">Zoom to Layer</button>
        <button class="btn btn-outline" id="export-layer-btn">Export Layer</button>
      </div>
    `;

    propertiesDiv.classList.remove('hidden');

    // Setup property actions
    const zoomBtn = propertiesContent.querySelector('#zoom-to-layer-btn') as HTMLButtonElement;
    const exportBtn = propertiesContent.querySelector('#export-layer-btn') as HTMLButtonElement;

    zoomBtn.addEventListener('click', () => {
      this.eventBus.emit('layer:zoom-to', layer);
    });

    exportBtn.addEventListener('click', () => {
      this.exportLayer(layer);
    });
  }

  private exportLayer(layer: LayerConfig): void {
    const exportData = {
      id: layer.id,
      name: layer.name,
      type: layer.type,
      source: layer.source,
      metadata: layer.metadata,
      timestamp: new Date().toISOString()
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${layer.name}-metadata.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  }

  private filterLayers(searchTerm: string): void {
    const layerItems = this.container.querySelectorAll('.layer-item');
    const term = searchTerm.toLowerCase();

    layerItems.forEach(item => {
      const layerName = item.querySelector('label')?.textContent?.toLowerCase() || '';
      const shouldShow = layerName.includes(term);
      (item as HTMLElement).style.display = shouldShow ? 'block' : 'none';
    });
  }

  private loadSavedLayers(): void {
    // Load layers from localStorage
    const savedLayers = localStorage.getItem('terrasim-layers');
    if (savedLayers) {
      try {
        const layers = JSON.parse(savedLayers);
        layers.forEach((layer: LayerConfig) => {
          this.layers.set(layer.id, layer);
          this.addLayerToList(layer);
        });
      } catch (error) {
        console.error('Failed to load saved layers:', error);
      }
    }
  }

  public getLayers(): LayerConfig[] {
    return Array.from(this.layers.values());
  }

  public getLayer(id: string): LayerConfig | undefined {
    return this.layers.get(id);
  }

  public destroy(): void {
    // Save layers to localStorage
    const layers = Array.from(this.layers.values());
    localStorage.setItem('terrasim-layers', JSON.stringify(layers));

    // Cleanup
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}
