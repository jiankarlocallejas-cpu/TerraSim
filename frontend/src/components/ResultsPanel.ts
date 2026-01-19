/**
 * TerraSim Results Panel Component
 * Display and manage analysis results
 */

import { EventBus } from '../utils/EventBus';

interface AnalysisResult {
  id: string;
  name: string;
  type: 'erosion' | 'rusle' | 'slope' | 'watershed' | 'custom';
  timestamp: string;
  data: any;
  metadata?: Record<string, any>;
}

interface ResultVisualization {
  type: 'chart' | 'map' | 'table' | 'summary';
  data: any;
  config?: Record<string, any>;
}

export class ResultsPanel {
  private container!: HTMLElement;
  private eventBus: EventBus;
  private results: Map<string, AnalysisResult>;
  private activeResult: string | null;
  private visualizations: Map<string, ResultVisualization>;

  constructor(eventBus: EventBus) {
    this.eventBus = eventBus;
    this.results = new Map();
    this.activeResult = null;
    this.visualizations = new Map();
  }

  public mount(selector: string): void {
    const container = document.querySelector(selector) as HTMLElement;
    if (!container) {
      throw new Error(`Results panel container ${selector} not found`);
    }

    this.container = container;
    this.render();
    this.setupEventListeners();
    this.loadSavedResults();
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="results-panel">
        <div class="panel-header">
          <h3>Analysis Results</h3>
          <button id="toggle-results-panel" class="toggle-btn">−</button>
        </div>
        
        <div class="panel-content">
          <div class="results-actions">
            <button id="export-all-btn" class="btn btn-outline btn-sm">
              <span class="icon">💾</span> Export All
            </button>
            <button id="clear-all-btn" class="btn btn-outline btn-sm">
              <span class="icon">🗑️</span> Clear All
            </button>
            <button id="compare-btn" class="btn btn-primary btn-sm">
              <span class="icon">📊</span> Compare
            </button>
          </div>
          
          <div class="results-list">
            <div class="results-header">
              <h4>Recent Analyses</h4>
              <div class="results-filter">
                <select id="results-filter-select">
                  <option value="all">All Results</option>
                  <option value="erosion">Erosion Analysis</option>
                  <option value="rusle">RUSLE</option>
                  <option value="slope">Slope Analysis</option>
                  <option value="watershed">Watershed</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>
            
            <div id="results-items" class="results-items">
              <!-- Results will be added here dynamically -->
            </div>
          </div>
          
          <div id="result-details" class="result-details hidden">
            <div class="result-header">
              <h4 id="result-title">Result Details</h4>
              <div class="result-actions">
                <button id="result-export-btn" class="btn btn-outline btn-sm">Export</button>
                <button id="result-delete-btn" class="btn btn-outline btn-sm">Delete</button>
                <button id="result-close-btn" class="btn btn-outline btn-sm">✕</button>
              </div>
            </div>
            
            <div class="result-content">
              <div class="result-tabs">
                <button class="tab-btn active" data-tab="summary">Summary</button>
                <button class="tab-btn" data-tab="charts">Charts</button>
                <button class="tab-btn" data-tab="data">Raw Data</button>
                <button class="tab-btn" data-tab="metadata">Metadata</button>
              </div>
              
              <div class="tab-content">
                <div id="summary-tab" class="tab-pane active">
                  <div id="summary-content"></div>
                </div>
                
                <div id="charts-tab" class="tab-pane">
                  <div id="charts-content"></div>
                </div>
                
                <div id="data-tab" class="tab-pane">
                  <div id="data-content"></div>
                </div>
                
                <div id="metadata-tab" class="tab-pane">
                  <div id="metadata-content"></div>
                </div>
              </div>
            </div>
          </div>
          
          <div id="comparison-view" class="comparison-view hidden">
            <div class="comparison-header">
              <h4>Results Comparison</h4>
              <button id="comparison-close-btn" class="btn btn-outline btn-sm">✕</button>
            </div>
            
            <div class="comparison-content">
              <div id="comparison-charts"></div>
              <div id="comparison-table"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  private setupEventListeners(): void {
    // Panel toggle
    const toggleBtn = this.container.querySelector('#toggle-results-panel') as HTMLButtonElement;
    const panelContent = this.container.querySelector('.panel-content') as HTMLElement;
    
    toggleBtn.addEventListener('click', () => {
      panelContent.classList.toggle('hidden');
      toggleBtn.textContent = panelContent.classList.contains('hidden') ? '+' : '−';
    });

    // Action buttons
    const exportAllBtn = this.container.querySelector('#export-all-btn') as HTMLButtonElement;
    const clearAllBtn = this.container.querySelector('#clear-all-btn') as HTMLButtonElement;
    const compareBtn = this.container.querySelector('#compare-btn') as HTMLButtonElement;

    exportAllBtn.addEventListener('click', () => this.exportAllResults());
    clearAllBtn.addEventListener('click', () => this.clearAllResults());
    compareBtn.addEventListener('click', () => this.showComparison());

    // Filter
    const filterSelect = this.container.querySelector('#results-filter-select') as HTMLSelectElement;
    filterSelect.addEventListener('change', () => {
      this.filterResults(filterSelect.value);
    });

    // Result item clicks
    this.container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      
      if (target.closest('.result-item')) {
        const resultId = target.closest('.result-item')?.getAttribute('data-result-id');
        if (resultId) {
          this.showResultDetails(resultId);
        }
      }
      
      if (target.classList.contains('result-export-btn')) {
        this.exportCurrentResult();
      }
      
      if (target.classList.contains('result-delete-btn')) {
        this.deleteCurrentResult();
      }
      
      if (target.classList.contains('result-close-btn')) {
        this.hideResultDetails();
      }
      
      if (target.classList.contains('comparison-close-btn')) {
        this.hideComparison();
      }
    });

    // Tab switching
    this.container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      
      if (target.classList.contains('tab-btn')) {
        this.switchTab(target.getAttribute('data-tab')!);
      }
    });

    // Listen for result events
    this.eventBus.on('result:added', (result: AnalysisResult) => {
      this.addResult(result);
    });

    this.eventBus.on('erosion:calculated', (data: any) => {
      const result: AnalysisResult = {
        id: `erosion_${Date.now()}`,
        name: `Erosion Analysis - ${new Date().toLocaleString()}`,
        type: 'erosion',
        timestamp: new Date().toISOString(),
        data: data,
        metadata: {
          model: 'TerraSim',
          version: '2.0.0'
        }
      };
      this.addResult(result);
    });
  }

  private addResult(result: AnalysisResult): void {
    this.results.set(result.id, result);
    this.renderResultItem(result);
    this.saveResults();
  }

  private renderResultItem(result: AnalysisResult): void {
    const resultsItems = this.container.querySelector('#results-items') as HTMLElement;
    
    const resultElement = document.createElement('div');
    resultElement.className = 'result-item';
    resultElement.setAttribute('data-result-id', result.id);
    resultElement.setAttribute('data-result-type', result.type);
    
    const typeIcons = {
      'erosion': '🌊',
      'rusle': '📊',
      'slope': '⛰️',
      'watershed': '💧',
      'custom': '🔧'
    };

    const riskColors = {
      'Low': '#28a745',
      'Moderate': '#ffc107',
      'High': '#fd7e14',
      'Severe': '#dc3545'
    };

    let riskIndicator = '';
    if (result.type === 'erosion' && result.data.risk_category) {
      riskIndicator = `
        <span class="risk-indicator" style="background-color: ${riskColors[result.data.risk_category as keyof typeof riskColors]}">
          ${result.data.risk_category}
        </span>
      `;
    }

    resultElement.innerHTML = `
      <div class="result-item-header">
        <span class="result-icon">${typeIcons[result.type as keyof typeof typeIcons]}</span>
        <div class="result-info">
          <div class="result-name">${result.name}</div>
          <div class="result-meta">
            <span class="result-type">${result.type}</span>
            <span class="result-date">${new Date(result.timestamp).toLocaleDateString()}</span>
          </div>
        </div>
        ${riskIndicator}
      </div>
      <div class="result-preview">
        ${this.generateResultPreview(result)}
      </div>
    `;
    
    resultsItems.insertBefore(resultElement, resultsItems.firstChild);
  }

  private generateResultPreview(result: AnalysisResult): string {
    switch (result.type) {
      case 'erosion':
        return `
          <div class="preview-metrics">
            <div class="metric">
              <span class="metric-value">${result.data.mean_loss?.toFixed(2) || 'N/A'}</span>
              <span class="metric-unit">tons/ha/year</span>
            </div>
            <div class="metric">
              <span class="metric-value">${result.data.confidence ? (result.data.confidence * 100).toFixed(1) + '%' : 'N/A'}</span>
              <span class="metric-unit">confidence</span>
            </div>
          </div>
        `;
      
      case 'rusle':
        return `
          <div class="preview-metrics">
            <div class="metric">
              <span class="metric-value">${result.data.soil_loss?.toFixed(2) || 'N/A'}</span>
              <span class="metric-unit">tons/ha/year</span>
            </div>
          </div>
        `;
      
      default:
        return `<div class="preview-text">Analysis completed</div>`;
    }
  }

  private showResultDetails(resultId: string): void {
    const result = this.results.get(resultId);
    if (!result) return;

    this.activeResult = resultId;
    
    const detailsPanel = this.container.querySelector('#result-details') as HTMLElement;
    const titleElement = this.container.querySelector('#result-title') as HTMLElement;
    
    titleElement.textContent = result.name;
    detailsPanel.classList.remove('hidden');
    
    // Update all tabs
    this.updateSummaryTab(result);
    this.updateChartsTab(result);
    this.updateDataTab(result);
    this.updateMetadataTab(result);
    
    // Switch to summary tab
    this.switchTab('summary');
  }

  private updateSummaryTab(result: AnalysisResult): void {
    const summaryContent = this.container.querySelector('#summary-content') as HTMLElement;
    
    let summaryHtml = '';
    
    switch (result.type) {
      case 'erosion':
        summaryHtml = `
          <div class="result-summary">
            <div class="summary-section">
              <h5>Risk Assessment</h5>
              <div class="risk-summary">
                <div class="risk-level ${result.data.risk_category?.toLowerCase()}">
                  ${result.data.risk_category} Risk
                </div>
                <div class="confidence-level">
                  ${(result.data.confidence * 100).toFixed(1)}% Confidence
                </div>
              </div>
            </div>
            
            <div class="summary-section">
              <h5>Erosion Metrics</h5>
              <div class="metrics-grid">
                <div class="metric-item">
                  <span class="metric-label">Mean Loss:</span>
                  <span class="metric-value">${result.data.mean_loss?.toFixed(2)} tons/ha/year</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Peak Loss:</span>
                  <span class="metric-value">${result.data.peak_loss?.toFixed(2)} tons/ha/year</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Total Loss:</span>
                  <span class="metric-value">${result.data.total_soil_loss?.toFixed(2)} tons</span>
                </div>
              </div>
            </div>
            
            ${result.data.rusle_comparison ? `
              <div class="summary-section">
                <h5>RUSLE Comparison</h5>
                <div class="comparison-summary">
                  <div class="comparison-item">
                    <span>RUSLE Loss:</span>
                    <span>${result.data.rusle_comparison.soil_loss.toFixed(2)} tons/ha/year</span>
                  </div>
                  <div class="comparison-item">
                    <span>Difference:</span>
                    <span>${result.data.rusle_comparison.difference.toFixed(2)} tons/ha/year</span>
                  </div>
                  <div class="comparison-item">
                    <span>Percent Difference:</span>
                    <span>${result.data.rusle_comparison.percent_difference.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ` : ''}
          </div>
        `;
        break;
      
      default:
        summaryHtml = `
          <div class="result-summary">
            <div class="summary-section">
              <h5>Analysis Information</h5>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Type:</span>
                  <span class="info-value">${result.type}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Date:</span>
                  <span class="info-value">${new Date(result.timestamp).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        `;
    }
    
    summaryContent.innerHTML = summaryHtml;
  }

  private updateChartsTab(result: AnalysisResult): void {
    const chartsContent = this.container.querySelector('#charts-content') as HTMLElement;
    
    // This would integrate with a charting library like Chart.js or D3.js
    // For now, we'll show placeholder charts
    chartsContent.innerHTML = `
      <div class="charts-container">
        <div class="chart-placeholder">
          <h5>Erosion Factors</h5>
          <div class="chart-canvas" id="factors-chart"></div>
        </div>
        
        ${result.type === 'erosion' ? `
          <div class="chart-placeholder">
            <h5>Risk Distribution</h5>
            <div class="chart-canvas" id="risk-chart"></div>
          </div>
        ` : ''}
      </div>
    `;
    
    // Initialize charts (placeholder)
    this.initializeCharts(result);
  }

  private updateDataTab(result: AnalysisResult): void {
    const dataContent = this.container.querySelector('#data-content') as HTMLElement;
    
    const dataJson = JSON.stringify(result.data, null, 2);
    
    dataContent.innerHTML = `
      <div class="data-viewer">
        <div class="data-controls">
          <button class="btn btn-outline btn-sm" id="copy-data-btn">Copy JSON</button>
          <button class="btn btn-outline btn-sm" id="download-data-btn">Download</button>
        </div>
        <pre class="data-json">${dataJson}</pre>
      </div>
    `;
    
    // Setup data controls
    const copyBtn = dataContent.querySelector('#copy-data-btn') as HTMLButtonElement;
    const downloadBtn = dataContent.querySelector('#download-data-btn') as HTMLButtonElement;
    
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(dataJson);
      this.eventBus.emit('notification:show', { type: 'success', message: 'Data copied to clipboard' });
    });
    
    downloadBtn.addEventListener('click', () => {
      this.downloadData(result, 'json');
    });
  }

  private updateMetadataTab(result: AnalysisResult): void {
    const metadataContent = this.container.querySelector('#metadata-content') as HTMLElement;
    
    const metadata = {
      id: result.id,
      name: result.name,
      type: result.type,
      timestamp: result.timestamp,
      ...result.metadata
    };
    
    let metadataHtml = '';
    Object.entries(metadata).forEach(([key, value]) => {
      metadataHtml += `
        <div class="metadata-item">
          <span class="metadata-key">${key}:</span>
          <span class="metadata-value">${typeof value === 'object' ? JSON.stringify(value) : value}</span>
        </div>
      `;
    });
    
    metadataContent.innerHTML = `<div class="metadata-list">${metadataHtml}</div>`;
  }

  private switchTab(tabName: string): void {
    // Update tab buttons
    this.container.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    this.container.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    
    // Update tab panes
    this.container.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.remove('active');
    });
    this.container.querySelector(`#${tabName}-tab`)?.classList.add('active');
  }

  private hideResultDetails(): void {
    const detailsPanel = this.container.querySelector('#result-details') as HTMLElement;
    detailsPanel.classList.add('hidden');
    this.activeResult = null;
  }

  private exportCurrentResult(): void {
    if (!this.activeResult) return;
    
    const result = this.results.get(this.activeResult);
    if (result) {
      this.exportResult(result);
    }
  }

  private deleteCurrentResult(): void {
    if (!this.activeResult) return;
    
    if (confirm('Are you sure you want to delete this result?')) {
      this.results.delete(this.activeResult);
      
      // Remove from DOM
      const resultElement = this.container.querySelector(`[data-result-id="${this.activeResult}"]`);
      if (resultElement) {
        resultElement.remove();
      }
      
      this.hideResultDetails();
      this.saveResults();
      
      this.eventBus.emit('notification:show', { type: 'info', message: 'Result deleted' });
    }
  }

  private exportAllResults(): void {
    const allResults = Array.from(this.results.values());
    const exportData = {
      results: allResults,
      exportDate: new Date().toISOString(),
      version: '2.0.0'
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `terrasim-results-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    this.eventBus.emit('notification:show', { type: 'success', message: 'All results exported' });
  }

  private clearAllResults(): void {
    if (confirm('Are you sure you want to clear all results? This cannot be undone.')) {
      this.results.clear();
      
      // Clear DOM
      const resultsItems = this.container.querySelector('#results-items') as HTMLElement;
      resultsItems.innerHTML = '';
      
      this.hideResultDetails();
      this.saveResults();
      
      this.eventBus.emit('notification:show', { type: 'info', message: 'All results cleared' });
    }
  }

  private showComparison(): void {
    const comparisonView = this.container.querySelector('#comparison-view') as HTMLElement;
    comparisonView.classList.remove('hidden');
    
    // Load comparison data
    this.updateComparison();
  }

  private hideComparison(): void {
    const comparisonView = this.container.querySelector('#comparison-view') as HTMLElement;
    comparisonView.classList.add('hidden');
  }

  private updateComparison(): void {
    const comparisonCharts = this.container.querySelector('#comparison-charts') as HTMLElement;
    const comparisonTable = this.container.querySelector('#comparison-table') as HTMLElement;
    
    const erosionResults = Array.from(this.results.values()).filter(r => r.type === 'erosion');
    
    if (erosionResults.length === 0) {
      comparisonCharts.innerHTML = '<p>No erosion results available for comparison</p>';
      comparisonTable.innerHTML = '';
      return;
    }
    
    // Generate comparison table
    let tableHtml = `
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Date</th>
            <th>Mean Loss</th>
            <th>Risk Category</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
    `;
    
    erosionResults.forEach(result => {
      tableHtml += `
        <tr>
          <td>${result.name}</td>
          <td>${new Date(result.timestamp).toLocaleDateString()}</td>
          <td>${result.data.mean_loss?.toFixed(2) || 'N/A'}</td>
          <td>${result.data.risk_category || 'N/A'}</td>
          <td>${result.data.confidence ? (result.data.confidence * 100).toFixed(1) + '%' : 'N/A'}</td>
        </tr>
      `;
    });
    
    tableHtml += '</tbody></table>';
    comparisonTable.innerHTML = tableHtml;
    
    // Generate comparison charts (placeholder)
    comparisonCharts.innerHTML = `
      <div class="comparison-chart">
        <h5>Erosion Loss Comparison</h5>
        <div class="chart-canvas" id="comparison-loss-chart"></div>
      </div>
    `;
  }

  private filterResults(filterType: string): void {
    const resultItems = this.container.querySelectorAll('.result-item');
    
    resultItems.forEach(item => {
      const itemType = item.getAttribute('data-result-type');
      const shouldShow = filterType === 'all' || itemType === filterType;
      (item as HTMLElement).style.display = shouldShow ? 'block' : 'none';
    });
  }

  private exportResult(result: AnalysisResult): void {
    const exportData = {
      result: result,
      exportDate: new Date().toISOString(),
      version: '2.0.0'
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${result.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  }

  private downloadData(result: AnalysisResult, format: string): void {
    if (format === 'json') {
      this.exportResult(result);
    }
    // Add other formats (CSV, PDF) as needed
  }

  private initializeCharts(result: AnalysisResult): void {
    // This would integrate with a charting library
    // For now, we'll just show placeholders
    console.log('Charts would be initialized here for result:', result.id);
  }

  private saveResults(): void {
    const results = Array.from(this.results.values());
    localStorage.setItem('terrasim-results', JSON.stringify(results));
  }

  private loadSavedResults(): void {
    const savedResults = localStorage.getItem('terrasim-results');
    if (savedResults) {
      try {
        const results = JSON.parse(savedResults);
        results.forEach((result: AnalysisResult) => {
          this.results.set(result.id, result);
          this.renderResultItem(result);
        });
      } catch (error) {
        console.error('Failed to load saved results:', error);
      }
    }
  }

  public getResults(): AnalysisResult[] {
    return Array.from(this.results.values());
  }

  public getResult(id: string): AnalysisResult | undefined {
    return this.results.get(id);
  }

  public destroy(): void {
    this.saveResults();
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}
