/**
 * TerraSim Toolbar Component
 * Main application toolbar with tools and controls
 */

import { EventBus } from '../utils/EventBus';

interface Tool {
  id: string;
  name: string;
  icon: string;
  category: string;
  active: boolean;
  disabled?: boolean;
}

interface ToolCategory {
  id: string;
  name: string;
  tools: Tool[];
}

export class Toolbar {
  private container!: HTMLElement;
  private eventBus: EventBus;
  private tools: Map<string, Tool>;
  private categories: ToolCategory[];
  private activeTool: string | null;

  constructor(eventBus: EventBus) {
    this.eventBus = eventBus;
    this.tools = new Map();
    this.activeTool = null;
    this.categories = this.initializeCategories();
    this.initializeTools();
  }

  private initializeCategories(): ToolCategory[] {
    return [
      {
        id: 'navigation',
        name: 'Navigation',
        tools: []
      },
      {
        id: 'selection',
        name: 'Selection',
        tools: []
      },
      {
        id: 'drawing',
        name: 'Drawing',
        tools: []
      },
      {
        id: 'measurement',
        name: 'Measurement',
        tools: []
      },
      {
        id: 'analysis',
        name: 'Analysis',
        tools: []
      },
      {
        id: 'data',
        name: 'Data',
        tools: []
      }
    ];
  }

  private initializeTools(): void {
    const allTools: Tool[] = [
      // Navigation tools
      { id: 'pan', name: 'Pan', icon: '✋', category: 'navigation', active: false },
      { id: 'zoom-in', name: 'Zoom In', icon: '🔍+', category: 'navigation', active: false },
      { id: 'zoom-out', name: 'Zoom Out', icon: '🔍-', category: 'navigation', active: false },
      { id: 'zoom-extent', name: 'Full Extent', icon: '⛶', category: 'navigation', active: false },
      { id: 'zoom-previous', name: 'Previous Extent', icon: '◀', category: 'navigation', active: false },
      { id: 'zoom-next', name: 'Next Extent', icon: '▶', category: 'navigation', active: false },

      // Selection tools
      { id: 'select-features', name: 'Select Features', icon: '⬚', category: 'selection', active: false },
      { id: 'select-by-rectangle', name: 'Select by Rectangle', icon: '⬜', category: 'selection', active: false },
      { id: 'select-by-polygon', name: 'Select by Polygon', icon: '⬟', category: 'selection', active: false },
      { id: 'select-by-circle', name: 'Select by Circle', icon: '⭕', category: 'selection', active: false },
      { id: 'clear-selection', name: 'Clear Selection', icon: '❌', category: 'selection', active: false },

      // Drawing tools
      { id: 'draw-point', name: 'Draw Point', icon: '📍', category: 'drawing', active: false },
      { id: 'draw-line', name: 'Draw Line', icon: '📏', category: 'drawing', active: false },
      { id: 'draw-polygon', name: 'Draw Polygon', icon: '⬟', category: 'drawing', active: false },
      { id: 'draw-rectangle', name: 'Draw Rectangle', icon: '⬜', category: 'drawing', active: false },
      { id: 'draw-circle', name: 'Draw Circle', icon: '⭕', category: 'drawing', active: false },
      { id: 'draw-text', name: 'Draw Text', icon: '📝', category: 'drawing', active: false },

      // Measurement tools
      { id: 'measure-distance', name: 'Measure Distance', icon: '📏', category: 'measurement', active: false },
      { id: 'measure-area', name: 'Measure Area', icon: '📐', category: 'measurement', active: false },
      { id: 'measure-angle', name: 'Measure Angle', icon: '📐', category: 'measurement', active: false },
      { id: 'measure-coordinate', name: 'Get Coordinates', icon: '📍', category: 'measurement', active: false },

      // Analysis tools
      { id: 'erosion-analysis', name: 'Erosion Analysis', icon: '🌊', category: 'analysis', active: false },
      { id: 'slope-analysis', name: 'Slope Analysis', icon: '⛰️', category: 'analysis', active: false },
      { id: 'watershed', name: 'Watershed', icon: '💧', category: 'analysis', active: false },
      { id: 'viewshed', name: 'Viewshed', icon: '👁️', category: 'analysis', active: false },
      { id: 'buffer', name: 'Buffer', icon: '⭕', category: 'analysis', active: false },
      { id: 'intersect', name: 'Intersect', icon: '✖️', category: 'analysis', active: false },

      // Data tools
      { id: 'add-layer', name: 'Add Layer', icon: '➕', category: 'data', active: false },
      { id: 'layer-properties', name: 'Layer Properties', icon: '⚙️', category: 'data', active: false },
      { id: 'attribute-table', name: 'Attribute Table', icon: '📋', category: 'data', active: false },
      { id: 'export-data', name: 'Export Data', icon: '💾', category: 'data', active: false }
    ];

    allTools.forEach(tool => {
      this.tools.set(tool.id, tool);
    });

    // Organize tools by category
    this.categories.forEach(category => {
      category.tools = allTools.filter(tool => tool.category === category.id);
    });
  }

  public mount(selector: string): void {
    const container = document.querySelector(selector) as HTMLElement;
    if (!container) {
      throw new Error(`Toolbar container ${selector} not found`);
    }

    this.container = container;
    this.render();
    this.setupEventListeners();
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="toolbar">
        <div class="toolbar-section">
          <div class="toolbar-group">
            <button class="tool-btn ${this.activeTool === 'pan' ? 'active' : ''}" 
                    data-tool="pan" title="Pan">
              <span class="tool-icon">✋</span>
              <span class="tool-name">Pan</span>
            </button>
          </div>
          
          <div class="toolbar-group">
            <button class="tool-btn" data-tool="zoom-in" title="Zoom In">
              <span class="tool-icon">🔍+</span>
            </button>
            <button class="tool-btn" data-tool="zoom-out" title="Zoom Out">
              <span class="tool-icon">🔍-</span>
            </button>
            <button class="tool-btn" data-tool="zoom-extent" title="Full Extent">
              <span class="tool-icon">⛶</span>
            </button>
          </div>
        </div>

        <div class="toolbar-section">
          <div class="toolbar-group">
            <button class="tool-btn" data-tool="select-features" title="Select Features">
              <span class="tool-icon">⬚</span>
            </button>
            <button class="tool-btn" data-tool="select-by-rectangle" title="Select by Rectangle">
              <span class="tool-icon">⬜</span>
            </button>
            <button class="tool-btn" data-tool="clear-selection" title="Clear Selection">
              <span class="tool-icon">❌</span>
            </button>
          </div>
          
          <div class="toolbar-group">
            <button class="tool-btn" data-tool="draw-point" title="Draw Point">
              <span class="tool-icon">📍</span>
            </button>
            <button class="tool-btn" data-tool="draw-line" title="Draw Line">
              <span class="tool-icon">📏</span>
            </button>
            <button class="tool-btn" data-tool="draw-polygon" title="Draw Polygon">
              <span class="tool-icon">⬟</span>
            </button>
          </div>
        </div>

        <div class="toolbar-section">
          <div class="toolbar-group">
            <button class="tool-btn" data-tool="measure-distance" title="Measure Distance">
              <span class="tool-icon">📏</span>
            </button>
            <button class="tool-btn" data-tool="measure-area" title="Measure Area">
              <span class="tool-icon">📐</span>
            </button>
          </div>
          
          <div class="toolbar-group">
            <button class="tool-btn" data-tool="erosion-analysis" title="Erosion Analysis">
              <span class="tool-icon">🌊</span>
            </button>
            <button class="tool-btn" data-tool="slope-analysis" title="Slope Analysis">
              <span class="tool-icon">⛰️</span>
            </button>
            <button class="tool-btn" data-tool="watershed" title="Watershed">
              <span class="tool-icon">💧</span>
            </button>
          </div>
        </div>

        <div class="toolbar-section">
          <div class="toolbar-group">
            <button class="tool-btn" data-tool="add-layer" title="Add Layer">
              <span class="tool-icon">➕</span>
            </button>
            <button class="tool-btn" data-tool="layer-properties" title="Layer Properties">
              <span class="tool-icon">⚙️</span>
            </button>
            <button class="tool-btn" data-tool="attribute-table" title="Attribute Table">
              <span class="tool-icon">📋</span>
            </button>
          </div>
        </div>

        <div class="toolbar-section toolbar-actions">
          <button class="tool-btn" id="undo-btn" title="Undo" disabled>
            <span class="tool-icon">↶</span>
          </button>
          <button class="tool-btn" id="redo-btn" title="Redo" disabled>
            <span class="tool-icon">↷</span>
          </button>
          <button class="tool-btn" id="help-btn" title="Help">
            <span class="tool-icon">❓</span>
          </button>
        </div>
      </div>
    `;
  }

  private setupEventListeners(): void {
    // Tool button clicks
    this.container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      const toolBtn = target.closest('.tool-btn') as HTMLElement;
      
      if (toolBtn && toolBtn.dataset.tool) {
        this.selectTool(toolBtn.dataset.tool);
      }

      // Special button handlers
      if (toolBtn?.id === 'undo-btn') {
        this.eventBus.emit('toolbar:undo');
      }
      
      if (toolBtn?.id === 'redo-btn') {
        this.eventBus.emit('toolbar:redo');
      }
      
      if (toolBtn?.id === 'help-btn') {
        this.showHelp();
      }
    });

    // Listen for tool selection events
    this.eventBus.on('tool:selected', (toolId: string) => {
      this.selectTool(toolId);
    });

    // Listen for undo/redo state changes
    this.eventBus.on('history:changed', (canUndo: boolean, canRedo: boolean) => {
      this.updateUndoRedoButtons(canUndo, canRedo);
    });
  }

  private selectTool(toolId: string): void {
    const tool = this.tools.get(toolId);
    if (!tool || tool.disabled) return;

    // Remove active class from all tools
    this.container.querySelectorAll('.tool-btn').forEach(btn => {
      btn.classList.remove('active');
    });

    // Add active class to selected tool
    const toolBtn = this.container.querySelector(`[data-tool="${toolId}"]`) as HTMLElement;
    if (toolBtn) {
      toolBtn.classList.add('active');
    }

    // Update active tool
    this.activeTool = toolId;
    tool.active = true;

    // Deactivate previous tool
    this.tools.forEach(t => {
      if (t.id !== toolId) {
        t.active = false;
      }
    });

    // Emit tool selection event
    this.eventBus.emit('tool:selected', toolId);
    this.eventBus.emit('tool:changed', tool);
  }

  private updateUndoRedoButtons(canUndo: boolean, canRedo: boolean): void {
    const undoBtn = this.container.querySelector('#undo-btn') as HTMLButtonElement;
    const redoBtn = this.container.querySelector('#redo-btn') as HTMLButtonElement;

    if (undoBtn) {
      undoBtn.disabled = !canUndo;
    }
    
    if (redoBtn) {
      redoBtn.disabled = !canRedo;
    }
  }

  private showHelp(): void {
    this.eventBus.emit('help:show', {
      title: 'Toolbar Help',
      content: `
        <h4>Navigation Tools</h4>
        <ul>
          <li><strong>Pan:</strong> Move the map</li>
          <li><strong>Zoom In/Out:</strong> Zoom in and out</li>
          <li><strong>Full Extent:</strong> Zoom to full extent</li>
        </ul>
        
        <h4>Selection Tools</h4>
        <ul>
          <li><strong>Select Features:</strong> Click to select features</li>
          <li><strong>Select by Rectangle:</strong> Draw rectangle to select</li>
          <li><strong>Clear Selection:</strong> Clear all selections</li>
        </ul>
        
        <h4>Drawing Tools</h4>
        <ul>
          <li><strong>Draw Point:</strong> Click to add points</li>
          <li><strong>Draw Line:</strong> Click to draw lines</li>
          <li><strong>Draw Polygon:</strong> Click to draw polygons</li>
        </ul>
        
        <h4>Measurement Tools</h4>
        <ul>
          <li><strong>Measure Distance:</strong> Click to measure distances</li>
          <li><strong>Measure Area:</strong> Click to measure areas</li>
        </ul>
        
        <h4>Analysis Tools</h4>
        <ul>
          <li><strong>Erosion Analysis:</strong> Run erosion analysis</li>
          <li><strong>Slope Analysis:</strong> Analyze slope</li>
          <li><strong>Watershed:</strong> Delineate watershed</li>
        </ul>
      `
    });
  }

  public getActiveTool(): Tool | null {
    return this.activeTool ? this.tools.get(this.activeTool) || null : null;
  }

  public getTool(toolId: string): Tool | undefined {
    return this.tools.get(toolId);
  }

  public getAllTools(): Tool[] {
    return Array.from(this.tools.values());
  }

  public getToolsByCategory(categoryId: string): Tool[] {
    return Array.from(this.tools.values()).filter(tool => tool.category === categoryId);
  }

  public enableTool(toolId: string): void {
    const tool = this.tools.get(toolId);
    if (tool) {
      tool.disabled = false;
      const toolBtn = this.container.querySelector(`[data-tool="${toolId}"]`) as HTMLButtonElement;
      if (toolBtn) {
        (toolBtn as HTMLButtonElement).disabled = false;
      }
    }
  }

  public disableTool(toolId: string): void {
    const tool = this.tools.get(toolId);
    if (tool) {
      tool.disabled = true;
      const toolBtn = this.container.querySelector(`[data-tool="${toolId}"]`) as HTMLButtonElement;
      if (toolBtn) {
        (toolBtn as HTMLButtonElement).disabled = true;
      }
    }
  }

  public setToolIcon(toolId: string, icon: string): void {
    const tool = this.tools.get(toolId);
    if (tool) {
      tool.icon = icon;
      const toolBtn = this.container.querySelector(`[data-tool="${toolId}"] .tool-icon`) as HTMLElement;
      if (toolBtn) {
        toolBtn.textContent = icon;
      }
    }
  }

  public destroy(): void {
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}
