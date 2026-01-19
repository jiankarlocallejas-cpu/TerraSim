# TerraSim v2.0.0

Advanced GIS Erosion Modeling Platform built with modern cross-platform technologies.

## 🌟 Features

- **Advanced Erosion Modeling**: TerraSim proprietary model with ML enhancement
- **RUSLE Integration**: Standard RUSLE calculations for comparison
- **Real-time GIS Processing**: Support for vector and raster data
- **Cross-platform**: Web, Desktop (Windows/Mac/Linux), and Mobile
- **Modern Tech Stack**: Python backend, TypeScript frontend, Electron desktop wrapper

## 🏗️ Architecture

### Backend (Python)
- **FastAPI**: High-performance async web framework
- **GeoPandas**: Geospatial data processing
- **Rasterio**: Raster data manipulation
- **NumPy/SciPy**: Scientific computing
- **Scikit-learn**: Machine learning for enhanced predictions
- **PostgreSQL/PostGIS**: Spatial database (optional)

### Frontend (TypeScript/JavaScript)
- **Leaflet**: Interactive web mapping
- **Mapbox GL**: Advanced 3D visualization
- **OpenLayers**: Enterprise GIS capabilities
- **React**: Component-based UI framework
- **WebSocket**: Real-time communication

### Desktop Applications
- **Electron**: Cross-platform desktop wrapper
- **PyQt5**: Native Python desktop application
- **System Integration**: File dialogs, notifications, system APIs

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/terrasim/terrasim.git
cd terrasim
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Node.js dependencies**
```bash
npm install
```

4. **Start the application**

**Web Application:**
```bash
# Terminal 1: Start backend
python backend/main.py

# Terminal 2: Start frontend
npm run dev
```

**Desktop Application:**
```bash
# Electron desktop app
npm run electron

# PyQt5 desktop app
python desktop/main.py
```

## 📁 Project Structure

```
terrasim/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Main application server
│   ├── models/             # Data models
│   ├── services/           # Business logic
│   └── utils/              # Utilities
├── frontend/               # TypeScript web frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── utils/          # Frontend utilities
│   │   └── styles/         # CSS/SCSS
│   ├── dist/               # Build output
│   └── public/             # Static assets
├── desktop/                # PyQt5 desktop application
│   ├── main.py             # Desktop app entry point
│   ├── components/         # Desktop UI components
│   └── resources/          # Desktop resources
├── electron/               # Electron desktop wrapper
│   ├── main.js             # Electron main process
│   ├── preload.js          # Preload script
│   └── assets/             # Electron assets
├── mobile/                 # React Native mobile app
│   ├── src/
│   ├── android/
│   └── ios/
├── docs/                   # Documentation
├── tests/                  # Test suites
└── scripts/                # Build/deployment scripts
```

## 🛠️ Development

### Backend Development
```bash
# Start Python backend with hot reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Desktop Development
```bash
# Electron development
npm run electron:dev

# PyQt5 development
python desktop/main.py
```

### Mobile Development
```bash
# React Native
cd mobile
npm install
npm run android  # or npm run ios
```

## 📊 API Documentation

### Erosion Calculation
```python
POST /api/erosion/calculate
{
  "rainfall": 1800,
  "slope": 15,
  "slope_length": 100,
  "soil_type": "loam",
  "vegetation_cover": 60,
  "support_practices": 50,
  "land_use": "agriculture",
  "area": 10,
  "seasonality": "wet"
}
```

### GIS Data Upload
```python
POST /api/gis/upload
{
  "data_type": "vector",
  "file_path": "/path/to/shapefile.shp",
  "metadata": {}
}
```

## 🧪 Testing

### Backend Tests
```bash
# Run Python tests
pytest backend/tests/

# Coverage report
pytest --cov=backend backend/tests/
```

### Frontend Tests
```bash
# Run JavaScript tests
npm test

# E2E tests
npm run test:e2e
```

### Integration Tests
```bash
# Full integration test suite
npm run test:integration
```

## 📦 Deployment

### Web Deployment
```bash
# Build frontend
npm run build

# Deploy to production
docker-compose up -d
```

### Desktop Deployment
```bash
# Build Electron apps
npm run build:electron

# Build installers
npm run dist:electron
```

### Mobile Deployment
```bash
# Android
cd mobile
npm run build:android

# iOS
cd mobile
npm run build:ios
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/terrasim
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAPBOX_TOKEN=your_token_here
```

### Database Setup
```bash
# PostgreSQL with PostGIS
createdb terrasim
psql terrasim -c "CREATE EXTENSION postgis;"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Leaflet** - Open-source JavaScript library for mobile-friendly interactive maps
- **GeoPandas** - Python project to make working with geospatial data easier
- **FastAPI** - Modern, fast web framework for building APIs with Python
- **Electron** - Build cross-platform desktop apps with JavaScript, HTML, and CSS
- **PyQt5** - Python binding for the Qt cross-platform application framework

## 📞 Support

- **Documentation**: [https://terrasim.docs.com](https://terrasim.docs.com)
- **Issues**: [GitHub Issues](https://github.com/terrasim/terrasim/issues)
- **Discussions**: [GitHub Discussions](https://github.com/terrasim/terrasim/discussions)
- **Email**: support@terrasim.com

---

**TerraSim v2.0.0** - Advanced GIS Erosion Modeling Platform
