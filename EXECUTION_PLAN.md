# OBD2 Data Visualization Tool - Execution Plan

## 🚀 Phase 1: Foundation & Database Setup

### 1.1 Database Infrastructure ✅
**Status:** COMPLETED
- PostgreSQL Docker setup with `docker-compose.yml`
- Complete database schema with proper indexing
- pgAdmin for database management
- Views for common queries

**How to Start:**
```bash
docker-compose up -d
```
- Database: `postgresql://obd2_user:obd2_password@localhost:5432/obd2_data`
- Admin UI: http://localhost:5050 (admin@obd2.local / admin123)

### 1.2 Remove Obsolete Code ✅
**Status:** COMPLETED - Old files already removed
**Current Structure:**
- `src/obd2_main.py` → Entry point
- `src/obd2_viewer/` → Main package
  - `app/main_application.py` → Main app with file upload
  - `core/data_loader.py` → Data loading
  - `core/data_processor.py` → Data processing
  - `core/multi_channel_parser.py` → Multi-channel CSV parsing
  - `visualization/dashboard.py` → Dashboard UI
  - `utils/file_utils.py` → File utilities

### 1.3 Database Connection Layer ✅
**Status:** COMPLETED (Dec 2024)
**What Exists:**
- ✅ PostgreSQL Docker setup (`docker-compose.yml`)
- ✅ Database schema (`database/init.sql`)
- ✅ Python connection layer with SQLAlchemy 2.0

**Implemented Files:**
```
src/obd2_viewer/database/
├── __init__.py        # Module exports
├── config.py          # Environment-based configuration
├── connection.py      # DatabaseManager with connection pooling
├── models.py          # SQLAlchemy ORM models (ImportObject, ChannelData, VizSnapshot, etc.)
└── repository.py      # ImportRepository, SnapshotRepository for CRUD
```

**Usage:**
```python
from obd2_viewer.database import ImportRepository, DatabaseManager

# Test connection
db = DatabaseManager()
db.test_connection()  # Returns True if connected

# Save an import
repo = ImportRepository()
import_obj = repo.create_import(
    name="My Import",
    channels_data=channels_dict,  # Dict[str, pd.DataFrame]
    units_mapping=units_dict,     # Dict[str, str]
)

# Retrieve import data
channels, units = repo.get_import_channels(import_obj.id)
```

## 🏗️ Phase 2: Multi-Channel CSV Processing

### 2.1 Multi-Channel Parser ✅
**Status:** COMPLETED
**Location:** `src/obd2_viewer/core/multi_channel_parser.py`

**Implemented Features:**
- ✅ Detect multi-channel format by PID column presence
- ✅ Group rows by PID to create individual channels
- ✅ Interpolate to common timestamp grid (scipy.interpolate)
- ✅ Validate 10MB file size limit
- ✅ Handle up to 100 channels per import
- ✅ Sanitize channel names for component IDs
- ✅ Unit extraction per channel

### 2.2 Data Validation & Import ⚠️
**Status:** PARTIALLY IMPLEMENTED
**Implemented:**
- ✅ 10MB file size validation
- ✅ Required columns validation (SECONDS, PID, VALUE, UNITS)
- ✅ Channel name conflict detection (validate_import_compatibility)
- ❌ Processing status tracking in database (no DB connection)
- ⚠️ Basic error logging (Python logging)

### 2.3 Import Storage System 🔄
**Status:** NOT STARTED
**Priority:** HIGH
**Blocked By:** Database connection layer (1.3)
**Tasks:**
- Store parsed data in PostgreSQL as JSONB arrays
- Implement efficient data compression
- Create import metadata tracking
- Handle file deletion after successful import

## 🎨 Phase 3: New UI Architecture

### 3.1 Remove Group Logic ✅
**Status:** COMPLETED
**Notes:** Group logic exists in data_processor.py but is not used in the UI. Dashboard uses simple channel list without grouping.

### 3.2 Responsive Layout System 🔄
**Status:** NOT STARTED
**Priority:** MEDIUM
**Current State:** Fixed 4:8 column ratio (33%:67%)
**Tasks:**
- Implement drag-adjustable sidebar:graph ratio
- Add sidebar position toggle (left/top)
- Create scrollable graph area
- Responsive design for vertical screens
- Default 20:80 sidebar ratio for new visualizations

### 3.3 Individual Graph System 🔄
**Status:** NOT STARTED
**Priority:** MEDIUM
**Current State:** Uses Plotly subplots in single figure
**Tasks:**
- Replace subplot system with individual dcc.Graph components
- Add graph height controls per channel
- Implement independent graph scrolling
- Prevent graph overlap with proper CSS

## 📊 Phase 4: Multi-Import Support

### 4.1 Multi-Import Data Model 🔄
**Priority:** MEDIUM
**Tasks:**
- Extend data model to handle multiple imports
- Implement import color coding system
- Create channel availability matrix
- Handle time range unions across imports

### 4.2 Independent Time Controls 🔄
**Priority:** MEDIUM
**Tasks:**
- Create time controls per import
- Implement synchronized time window constraint
- Add navigation buttons (±0.1s, ±0.5s, ±1s, ±5s, ±15s, ±1min, ±5min)
- Time range union visualization

### 4.3 Channel Consolidation 🔄
**Priority:** MEDIUM
**Tasks:**
- Plot same channels from different imports on same graph
- Color-code by import with legend
- Handle channel intersection/union logic
- Colored tiles showing import availability per channel

## 🔧 Phase 5: Math Channel System

### 5.1 Expression Parser 🔄
**Priority:** MEDIUM
**Tasks:**
- Implement mathematical expression parser
- Support basic operations (+, -, *, /)
- Handle interpolation between channels
- Validate unit consistency

**Implementation:**
```python
# src/obd2_viewer/core/math_parser.py
class MathExpressionParser:
    def evaluate_expression(self, expression: str, channel_data: Dict) -> np.ndarray:
        # Parse mathematical expression
        # Handle interpolation for mismatched timestamps
        # Validate units
        # Return computed channel data
```

### 5.2 Math Channel UI 🔄
**Priority:** MEDIUM
**Tasks:**
- Create math channel creation modal
- Channel selection dropdowns
- Expression input with validation
- Apply to all imports functionality

## 💾 Phase 6: Visualization Snapshots

### 6.1 Snapshot System 🔄
**Priority:** MEDIUM
**Tasks:**
- Implement complete state serialization
- Store layout settings, time ranges, math channels
- Create snapshot management interface
- Add to home screen alongside imports

### 6.2 Home Page Redesign 🔄
**Priority:** MEDIUM
**Tasks:**
- List available imports on home screen
- List saved snapshots
- Add "New Visualization" button
- Import management (delete, rename)

## 🧪 Phase 7: Testing & Quality Assurance

### 7.1 Update Test Suite 🔄
**Priority:** ONGOING
**Tasks:**
- Update tests for new database layer
- Add multi-channel parsing tests
- Create integration tests for full workflow
- Performance tests for large datasets

### 7.2 Performance Optimization 🔄
**Priority:** MEDIUM
**Tasks:**
- Implement data downsampling for visualization
- Optimize database queries
- Add performance monitoring
- Handle 100+ channel scenarios

## 📋 Implementation Order

### **Week 1: Foundation** ✅ COMPLETE
1. ✅ Database setup (Docker + schema)
2. ✅ Remove obsolete code
3. 🔄 Database connection layer (NEXT PRIORITY)
4. ✅ Basic multi-channel parser

### **Week 2: Core Functionality** ⚠️ IN PROGRESS
5. ✅ Data validation and import (basic)
6. ✅ Remove group logic
7. 🔄 Responsive layout system
8. 🔄 Individual graph system

### **Week 3: Multi-Import**
9. 🔄 Multi-import data model
10. 🔄 Independent time controls
11. 🔄 Channel consolidation

### **Week 4: Advanced Features**
12. 🔄 Math channel system
13. 🔄 Snapshot functionality
14. 🔄 Home page redesign

### **Week 5: Polish & Testing**
15. 🔄 Performance optimization
16. ✅ Comprehensive testing (21 tests passing)
17. 🔄 Documentation updates
18. 🔄 Deployment preparation

## 🚨 Immediate Action Items

### **Right Now (Today):**
1. ✅ ~~Start Database: `docker-compose up -d`~~ (Docker setup exists)
2. ✅ ~~Remove Obsolete Files~~ (Done)
3. ✅ ~~Fix CSV Loading~~ (Multi-channel parser working)
4. ✅ ~~Fix Frontend Callbacks~~ (Fixed Dec 2024)

### **Next Priority:**
1. ✅ ~~Database Connection Layer~~ (DONE)
2. **Integrate DB with Main App** - Save/load imports from database
3. **Multi-Import UI** - Allow loading multiple imports, color-coded
4. **Multi-Import Visualization** - Same channels on same graph, different colors

### **Current Status:**
The application is **functional** for single-file visualization with database ready.
- ✅ Database connection layer complete
- ✅ Import/Snapshot repositories ready
- 🔄 Need to integrate DB into main application
- 🔄 Need multi-import UI and visualization

## 🔧 Development Commands

```bash
# Start development environment
docker-compose up -d

# Run tests
pytest test/ -v

# Start application
python src/obd2_main.py

# Database migrations (when implemented)
alembic upgrade head

# Code formatting
black src/ test/
```

## 📊 Success Metrics

- **CSV Loading:** Car_scanner_nov_4.csv loads and displays all channels
- **Performance:** Handles 100 channels within 5 seconds
- **Database:** All data persists after application restart
- **UI:** Responsive layout works on vertical screens
- **Multi-Import:** Can load and compare 2+ CSV files simultaneously

This plan prioritizes fixing the immediate issues (CSV loading) while building toward the full feature set you outlined.
