# TerraSim Setup Guide

## 🚀 Complete Setup Instructions

### System Requirements

**Minimum Requirements:**
- Python 3.8+
- Node.js 16+
- 8GB RAM
- 2GB free disk space

**Recommended:**
- Python 3.10+
- Node.js 18+
- 16GB RAM
- 5GB free disk space

**Supported Platforms:**
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, CentOS 8+)

---

## 📦 Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/terrasim/terrasim.git
cd terrasim
```

### 2. Python Environment Setup

#### Option A: Using venv (Recommended)
```bash
# Create virtual environment
python -m venv terrasim-env

# Activate environment
# Windows:
terrasim-env\Scripts\activate

# macOS/Linux:
source terrasim-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Using conda
```bash
# Create conda environment
conda create -n terrasim python=3.10

# Activate environment
conda activate terrasim

# Install dependencies
pip install -r requirements.txt
```

### 3. Node.js Setup

#### Install Node.js dependencies
```bash
npm install
```

#### Verify installation
```bash
node --version  # Should be 16+
npm --version   # Should be 8+
```

### 4. Database Setup (Optional)

#### PostgreSQL with PostGIS
```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql postgresql-contrib

# Install PostGIS extension
# Windows: Use Stack Builder
# macOS: brew install postgis
# Linux: sudo apt-get install postgis

# Create database
createdb terrasim
psql terrasim -c "CREATE EXTENSION postgis;"
```

#### SQLite (Default)
```bash
# No setup required - uses file-based database
```

---

## 🏃‍♂️ Running TerraSim

### Web Application

#### Method 1: Development Mode
```bash
# Terminal 1: Start Python backend
python backend/main.py

# Terminal 2: Start frontend development server
npm run dev

# Open browser to http://localhost:3000
```

#### Method 2: Production Mode
```bash
# Build frontend
npm run build

# Start backend with production settings
python backend/main.py --prod

# Open browser to http://localhost:8000
```

### Desktop Applications

#### Electron App (Cross-platform)
```bash
# Install Electron dependencies
npm install

# Run in development
npm run electron:dev

# Build for production
npm run electron:build

# Run built application
npm run electron:start
```

#### PyQt5 App (Native Python)
```bash
# Install PyQt5 dependencies
pip install PyQt5 PyQtWebEngine matplotlib plotly

# Run desktop application
python desktop/main.py
```

### Mobile Application (React Native)

#### Setup
```bash
cd mobile

# Install dependencies
npm install

# iOS setup
cd ios && pod install && cd ..

# Android setup
# Follow React Native Android setup guide
```

#### Run
```bash
# iOS
npm run ios

# Android
npm run android
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in root directory:

```bash
# Backend Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/terrasim
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-here
DEBUG=true

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAPBOX_TOKEN=your-mapbox-token
REACT_APP_DEFAULT_LAT=9.8
REACT_APP_DEFAULT_LNG=118.5

# GIS Configuration
GDAL_DATA=/path/to/gdal/data
PROJ_LIB=/path/to/proj/data
```

### Map Provider Setup

#### Mapbox (Recommended)
1. Sign up at [mapbox.com](https://mapbox.com)
2. Create access token
3. Add to environment variables:
```bash
REACT_APP_MAPBOX_TOKEN=pk.your-token-here
```

#### OpenStreetMap (Free)
```bash
REACT_APP_MAP_PROVIDER=osm
```

---

## 🧪 Testing Setup

### Backend Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest backend/tests/

# Run with coverage
pytest --cov=backend backend/tests/
```

### Frontend Tests
```bash
# Install test dependencies
npm install --save-dev jest @testing-library/react

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### Integration Tests
```bash
# Run full test suite
npm run test:all

# Run specific test types
npm run test:unit
npm run test:integration
npm run test:e2e
```

---

## 🐛 Troubleshooting

### Common Issues

#### Python Issues
```bash
# ModuleNotFoundError
pip install -r requirements.txt

# GDAL errors
# Windows: Install GDAL from OSGeo4W
# macOS: brew install gdal
# Linux: sudo apt-get install gdal-bin libgdal-dev

# Permission denied
# Use virtual environment or run with appropriate permissions
```

#### Node.js Issues
```bash
# Node version too old
# Install Node.js 16+ from nodejs.org

# npm install fails
# Clear cache: npm cache clean --force
# Delete node_modules: rm -rf node_modules
# Reinstall: npm install

# Port already in use
# Kill process: lsof -ti:8000 | xargs kill -9
# Or use different port: PORT=3001 npm start
```

#### Database Issues
```bash
# PostgreSQL connection failed
# Check if PostgreSQL is running: pg_ctl status
# Check connection string
# Verify PostGIS extension: psql -d terrasim -c "SELECT PostGIS_Version();"

# SQLite permission denied
# Check file permissions
# Use different database path
```

#### Desktop App Issues
```bash
# Electron won't start
# Check Node.js version
# Rebuild native modules: npm rebuild

# PyQt5 import error
# Install PyQt5: pip install PyQt5 PyQtWebEngine
# Check Python version compatibility
```

### Performance Issues

#### Slow Backend
```bash
# Enable caching
# Use PostgreSQL instead of SQLite
# Optimize database queries
# Enable Redis for session storage
```

#### Slow Frontend
```bash
# Enable production mode
# Use code splitting
# Optimize bundle size
# Enable service worker
```

#### Memory Issues
```bash
# Increase Node.js memory limit
node --max-old-space-size=4096 backend/main.py

# Monitor memory usage
npm run monitor
```

---

## 📊 Monitoring & Logging

### Backend Monitoring
```bash
# Enable logging
export LOG_LEVEL=INFO

# View logs
tail -f logs/terrasim.log

# Monitor performance
npm run monitor:backend
```

### Frontend Monitoring
```bash
# Enable React DevTools
# Use browser developer tools
# Monitor network requests
# Check console errors
```

### Database Monitoring
```bash
# PostgreSQL
psql -d terrasim -c "SELECT * FROM pg_stat_activity;"

# SQLite
sqlite3 terrasim.db ".schema"
```

---

## 🔄 Updates & Maintenance

### Update Dependencies
```bash
# Python dependencies
pip install --upgrade -r requirements.txt

# Node.js dependencies
npm update
npm audit fix
```

### Database Maintenance
```bash
# PostgreSQL
VACUUM ANALYZE;

# SQLite
sqlite3 terrasim.db "VACUUM;"
```

### Backup Data
```bash
# PostgreSQL
pg_dump terrasim > backup.sql

# SQLite
cp terrasim.db backup.db
```

---

## 🚀 Deployment

### Docker Deployment
```bash
# Build Docker image
docker build -t terrasim .

# Run container
docker run -p 8000:8000 terrasim
```

### Cloud Deployment
```bash
# AWS
# Use AWS Elastic Beanstalk or ECS

# Google Cloud
# Use Google Cloud Run or App Engine

# Azure
# Use Azure App Service or Container Instances
```

### Production Checklist
- [ ] Set environment variables
- [ ] Configure HTTPS
- [ ] Set up reverse proxy
- [ ] Enable logging
- [ ] Configure monitoring
- [ ] Set up backups
- [ ] Test all features
- [ ] Performance testing
- [ ] Security audit

---

## 📞 Support

### Get Help
- **Documentation**: [https://terrasim.docs.com](https://terrasim.docs.com)
- **Issues**: [GitHub Issues](https://github.com/terrasim/terrasim/issues)
- **Discussions**: [GitHub Discussions](https://github.com/terrasim/terrasim/discussions)
- **Email**: support@terrasim.com

### Contributing
1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

---

**Happy Modeling with TerraSim!** 🌍
