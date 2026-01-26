# TerraSim Quick Start Guide

## GET STARTED IN 5 MINUTES

### Windows Users

**Option 1: Batch File (Easiest)**
```bash
setup_database.bat
```

**Option 2: PowerShell**
```powershell
.\setup_database.ps1
```

**Option 3: Manual**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python setup_database.py
```

### Mac/Linux Users

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup_database.py
```

---

## VERIFY INSTALLATION

After setup completes, you should see:

```
[OK] Database setup completed successfully!
```

### Test API Connection
```bash
# Start the backend
python backend/main.py

# In a new terminal, test the API
curl http://localhost:8000/api/v1/projects/
```

---

## PROJECT STRUCTURE AFTER SETUP

```
TerraSim/
├── venv/                    # Virtual environment (auto-created)
├── backend/
│   ├── api/                 # API endpoints
│   ├── models/              # Database models
│   ├── schemas/             # Data validation
│   ├── db/
│   │   ├── session.py       # Database connection
│   │   └── init_db.py       # Initialization
│   ├── services/            # Business logic
│   └── main.py              # Entry point
├── frontend/                # React UI
├── setup_database.py        # Database setup script
├── setup_database.bat       # Windows executable
├── setup_database.ps1       # PowerShell script
├── requirements.txt         # Python dependencies
├── SETUP_INSTRUCTIONS.md    # Detailed guide
├── DATABASE_SCHEMA.md       # Schema reference
└── test.db                  # SQLite database (if using SQLite)
```

---

## 🗄️ Database Files

### SQLite (Development - Default)
- File: `test.db` (created in project root)
- Size: ~1-5 MB
- No additional setup required

### PostgreSQL (Production - Optional)
- Connection: `postgresql://user:password@localhost/terrasim`
- Requires: `setup_database.py` configuration

---

## 🔐 Default Credentials

**Admin User:**
- Email: `admin@example.com`
- Password: Check `.env` file (default: `changeme`)

**Change after first login!**

---

## 🌐 Access Points

Once backend is running:

- **API Docs (Swagger):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **API Root:** http://localhost:8000/api/v1
- **Health Check:** http://localhost:8000/health

---

## COMMON COMMANDS

```bash
# Activate virtual environment
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Start backend server
python backend/main.py

# Run tests
pytest backend/tests/

# Start frontend dev server
cd frontend && npm start

# Reset database (careful - deletes data!)
python -c "from backend.db.session import engine; from backend.models.base import Base; Base.metadata.drop_all(bind=engine)"
```

---

## 🆘 Troubleshooting

### Python not found
```bash
# Check Python is installed
python --version

# If not, download from: https://www.python.org/downloads/
# Make sure "Add Python to PATH" is checked during installation
```

### Permission denied (PowerShell)
```powershell
# Run as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Virtual environment won't activate
```bash
# Delete and recreate
rmdir venv /s /q  # Windows
rm -rf venv       # Mac/Linux

# Recreate
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### Database connection error
```bash
# If using PostgreSQL, verify it's running
# Windows: Check Services
# Mac: brew services list
# Linux: sudo systemctl status postgresql

# For development, use SQLite (default)
```

### Tables already exist error
```bash
# Delete existing database and retry
rm test.db

# Or reset database:
python setup_database.py --reset
```

---

## WHAT WAS INSTALLED

**Database Tables:**
- `users` - Authentication
- `projects` - Research projects
- `analyses` - Analysis sessions
- `erosion_results` - USPED simulation outputs ⭐
- `analysis_metrics` - Analysis results ⭐
- `jobs` - Background tasks
- `pointclouds` - LiDAR data
- `rasters` - Raster data

**Python Packages:**
- FastAPI - Web framework
- SQLAlchemy - ORM
- Pydantic - Data validation
- Alembic - Database migrations
- NumPy/SciPy - Scientific computing
- GDAL - Geospatial processing

---

## CONFIGURATION

Create `.env` file in project root:

```env
# Database
DATABASE_URL=sqlite:///./test.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Default Admin
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changeme
```

---

## NEXT STEPS

1. **Start Backend**
   ```bash
   python backend/main.py
   ```

2. **Review API Documentation**
   - Open http://localhost:8000/docs

3. **Explore Database**
   - Use DATABASE_SCHEMA.md for full reference

4. **Start Frontend Development**
   ```bash
   cd frontend
   npm install
   npm start
   ```

5. **Create Custom Endpoints** (optional)
   - See backend/api/v1/endpoints/

---

## 💡 Tips

- Keep virtual environment activated while developing
- Use `.env` for sensitive configuration (don't commit to git)
- Database file (`test.db`) is local - each dev has their own
- API docs are auto-generated from code
- All models include timestamps (created_at, updated_at)

---

## ❓ Need Help?

1. Check [SETUP_INSTRUCTIONS.md](./SETUP_INSTRUCTIONS.md) for detailed guide
2. Check [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for database reference
3. Check console output for error messages
4. Review [MASTER_DOCUMENTATION.md](./MASTER_DOCUMENTATION.md) for full project info

---

**Happy developing!**
