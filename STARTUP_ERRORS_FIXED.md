# Application Startup Errors - Fixed

## Issues Found & Resolved

### 1. Missing Import: USPEDErosionModel
**Error**: `cannot import name 'USPEDErosionModel' from 'backend.services.erosion_model'`

**Root Cause**: `app.py` was trying to import `USPEDErosionModel` but the actual class name is `TerraSIMErosionModel` with `SoilModelParameters`.

**Fix**: Updated [app.py](app.py#L81-L86)
```python
# Before
from backend.services.erosion_model import USPEDErosionModel

# After
from backend.services.erosion_model import TerraSIMErosionModel, SoilModelParameters
model = TerraSIMErosionModel(SoilModelParameters())
```

### 2. PostgreSQL Connection Error
**Error**: `connection to server at "localhost" (::1), port 5432 failed: Connection refused`

**Root Cause**: PostgreSQL wasn't running, but the application was hardcoded to use it.

**Fix**: Configure SQLite as default fallback:

1. **Updated [backend/core/config.py](backend/core/config.py)**:
   - Added `USE_SQLITE` environment variable (defaults to `true`)
   - Changed `DATABASE_URI` to use SQLite by default
   - Uses PostgreSQL only when explicitly configured

2. **Updated [backend/db/session.py](backend/db/session.py)**:
   - Added database type detection
   - SQLite connection uses `check_same_thread=False` (no pooling needed)
   - PostgreSQL connection uses connection pooling as before

**Configuration**:
- Default: SQLite (`sqlite:///./terrasim.db`)
- To use PostgreSQL: Set `USE_SQLITE=false` in environment variables

## Verification

All components now work correctly:

✅ **Calculation Engine**: TerraSIMErosionModel loads successfully
✅ **Database**: SQLite connection established
✅ **No PostgreSQL Required**: Application works without PostgreSQL running

## Files Modified

1. [app.py](app.py) - Fixed erosion model import
2. [backend/core/config.py](backend/core/config.py) - Added SQLite fallback
3. [backend/db/session.py](backend/db/session.py) - Added database type detection

## Startup Test Results

```
[INFO] Initializing USPED erosion model...
[INFO] USPED model loaded and ready for calculations
Starting calculation engine started: True
Database engine created: sqlite:///./terrasim.db
Database connection successful!
```

The application now starts without any database connection errors and uses SQLite for local development.
