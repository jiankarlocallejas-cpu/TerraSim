/**
 * TerraSim API Service
 * HTTP client for backend communication
 */

interface ApiResponse {
  success: boolean;
  data?: any;
  error?: string;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
}

export class ApiService {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  /**
   * Make HTTP request
   * @param endpoint - API endpoint
   * @param options - Request options
   */
  private async request(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      method: options.method || 'GET',
      headers: { ...this.defaultHeaders, ...(options.headers as Record<string, string>) },
      signal: AbortSignal.timeout(options.timeout || 30000)
    };

    if (options.body && options.method !== 'GET') {
      if (options.body instanceof FormData) {
        // Don't set Content-Type for FormData (browser sets it with boundary)
        const headers = config.headers as Record<string, string>;
        delete headers['Content-Type'];
        config.body = options.body;
      } else {
        config.body = JSON.stringify(options.body);
      }
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          success: false,
          error: errorData.error || `HTTP ${response.status}: ${response.statusText}`
        };
      }

      const data = await response.json();
      return {
        success: true,
        data
      };
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return {
            success: false,
            error: 'Request timeout'
          };
        }
        return {
          success: false,
          error: error.message
        };
      }
      return {
        success: false,
        error: 'Unknown error occurred'
      };
    }
  }

  /**
   * GET request
   * @param endpoint - API endpoint
   * @param params - Query parameters
   */
  public async get(endpoint: string, params?: Record<string, any>): Promise<ApiResponse> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, value.toString());
      });
      url += `?${searchParams.toString()}`;
    }
    return this.request(url);
  }

  /**
   * POST request
   * @param endpoint - API endpoint
   * @param data - Request body
   */
  public async post(endpoint: string, data?: any): Promise<ApiResponse> {
    return this.request(endpoint, {
      method: 'POST',
      body: data
    });
  }

  /**
   * PUT request
   * @param endpoint - API endpoint
   * @param data - Request body
   */
  public async put(endpoint: string, data?: any): Promise<ApiResponse> {
    return this.request(endpoint, {
      method: 'PUT',
      body: data
    });
  }

  /**
   * DELETE request
   * @param endpoint - API endpoint
   */
  public async delete(endpoint: string): Promise<ApiResponse> {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }

  /**
   * Upload file
   * @param endpoint - API endpoint
   * @param file - File to upload
   * @param metadata - Additional metadata
   */
  public async upload(endpoint: string, file: File, metadata?: Record<string, any>): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata) {
      Object.entries(metadata).forEach(([key, value]) => {
        formData.append(key, JSON.stringify(value));
      });
    }

    return this.request(endpoint, {
      method: 'POST',
      body: formData
    });
  }

  /**
   * Download file
   * @param endpoint - API endpoint
   * @param filename - Suggested filename
   */
  public async download(endpoint: string, filename: string): Promise<void> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.click();
      
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      throw new Error(`Download failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Check API health
   */
  public async healthCheck(): Promise<ApiResponse> {
    return this.get('/api/health');
  }

  /**
   * Set base URL
   * @param baseUrl - New base URL
   */
  public setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
  }

  /**
   * Set default header
   * @param key - Header key
   * @param value - Header value
   */
  public setDefaultHeader(key: string, value: string): void {
    this.defaultHeaders[key] = value;
  }

  /**
   * Remove default header
   * @param key - Header key
   */
  public removeDefaultHeader(key: string): void {
    delete this.defaultHeaders[key];
  }

  /**
   * Get base URL
   */
  public getBaseUrl(): string {
    return this.baseUrl;
  }
}
