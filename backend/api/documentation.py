"""
TerraSim API Documentation and Enhanced FastAPI Configuration
Provides comprehensive OpenAPI documentation and usage examples.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any


def get_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate enhanced OpenAPI schema for TerraSim API.
    
    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="TerraSim API",
        version="3.0.0",
        description="""
## TerraSim - Advanced Erosion Modeling Platform

Professional-grade soil erosion analysis system using USPED model with GPU-accelerated rendering.

### Features
- **USPED Modeling**: Unit Stream Power-based Erosion and Deposition model
- **Real-time Visualization**: GPU-accelerated 3D terrain rendering
- **Spatial Analysis**: Comprehensive GIS data processing
- **Batch Processing**: Handle multiple projects efficiently
- **REST API**: Complete API for programmatic access
- **Web UI**: Interactive web interface for analysis

### Quick Start

1. **Create a Project**
   ```bash
   POST /api/v1/projects
   {
       "name": "My Project",
       "description": "Erosion analysis",
       "location": "Area of interest",
       "crs": "EPSG:4326"
   }
   ```

2. **Upload Data**
   ```bash
   POST /api/v1/rasters
   # Upload DEM file (GeoTIFF)
   ```

3. **Run Analysis**
   ```bash
   POST /api/v1/analyses
   {
       "project_id": 1,
       "analysis_type": "usped",
       "parameters": {...}
   }
   ```

4. **Get Results**
   ```bash
   GET /api/v1/analyses/{analysis_id}/results
   ```

### Authentication

All endpoints (except public ones) require JWT authentication.
Include Bearer token in Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Data Formats

- **DEM**: GeoTIFF (.tif, .tiff)
- **Vector**: Shapefile (.shp), GeoJSON (.geojson)
- **Point Cloud**: LAS/LAZ (.las, .laz)
- **Raster**: GeoTIFF (.tif), NetCDF (.nc)

### Response Format

All responses follow a standard format:

**Success Response (2xx)**:
```json
{
    "data": {...},
    "message": "Operation successful",
    "timestamp": "2024-01-27T10:30:00",
    "request_id": "uuid"
}
```

**Error Response (4xx, 5xx)**:
```json
{
    "error": "ERROR_CODE",
    "message": "Human-readable message",
    "status_code": 400,
    "details": {...},
    "timestamp": "2024-01-27T10:30:00",
    "request_id": "uuid"
}
```

### Rate Limiting

API endpoints are rate limited to 100 requests per minute per IP.
Check response headers for rate limit info:

- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| VALIDATION_ERROR | 422 | Invalid input data |
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| CONFLICT | 409 | Resource conflict |
| PROCESSING_ERROR | 500 | Processing failed |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |

### Pagination

List endpoints support pagination:

```
GET /api/v1/projects?skip=0&limit=50&sort_by=name&sort_order=asc
```

Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 1000)
- `sort_by`: Field to sort by
- `sort_order`: Sort order (asc/desc)

### Webhooks

Receive notifications about long-running operations:

```
POST /api/v1/webhooks
{
    "url": "https://your-server.com/callback",
    "events": ["analysis.complete", "analysis.failed"],
    "secret": "your-secret-key"
}
```

### Example Requests

**Python**:
```python
import requests

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/projects",
    headers=headers
)
```

**JavaScript/TypeScript**:
```typescript
const response = await fetch('http://localhost:8000/api/v1/projects', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

**cURL**:
```bash
curl -H "Authorization: Bearer $TOKEN" \\
     http://localhost:8000/api/v1/projects
```

### Support & Issues

- **Documentation**: https://terrasim.readthedocs.io
- **Issues**: https://github.com/terrasim/terrasim/issues
- **Email**: support@terrasim.org

### License

MIT License - See LICENSE file for details
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Projects",
                "description": "Manage erosion analysis projects"
            },
            {
                "name": "Analyses",
                "description": "Run and manage erosion analyses"
            },
            {
                "name": "Data",
                "description": "Upload and manage GIS data"
            },
            {
                "name": "Results",
                "description": "Access analysis results"
            },
            {
                "name": "System",
                "description": "System health and monitoring"
            },
            {
                "name": "Authentication",
                "description": "User authentication and authorization"
            }
        ]
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://terrasim.org/logo.png",
        "altText": "TerraSim Logo"
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.terrasim.org",
            "description": "Production server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_documentation(app: FastAPI) -> None:
    """
    Setup comprehensive API documentation for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Set custom OpenAPI schema
    app.openapi = lambda: get_openapi_schema(app)
    
    # Configure Swagger UI
    app.swagger_ui_init_oauth = {
        "clientId": "terrasim-client",
        "appName": "TerraSim API Client",
        "scopes": {
            "write:projects": "Write projects",
            "read:projects": "Read projects",
            "write:analyses": "Write analyses",
            "read:analyses": "Read analyses"
        }
    }


# API Tags for endpoint categorization
API_TAGS = {
    "projects": {
        "name": "Projects",
        "description": "Create, read, update, and delete erosion analysis projects"
    },
    "analyses": {
        "name": "Analyses",
        "description": "Run and manage erosion model analyses"
    },
    "rasters": {
        "name": "Rasters",
        "description": "Upload and manage raster data (DEM, etc.)"
    },
    "pointclouds": {
        "name": "Point Clouds",
        "description": "Upload and manage LAS/LAZ point cloud data"
    },
    "results": {
        "name": "Results",
        "description": "Access and export analysis results"
    },
    "users": {
        "name": "Users",
        "description": "User management and authentication"
    },
    "health": {
        "name": "Health",
        "description": "System health checks and monitoring"
    }
}
