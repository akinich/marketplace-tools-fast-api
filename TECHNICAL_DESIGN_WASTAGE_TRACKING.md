# TECHNICAL DESIGN: WASTAGE TRACKING MODULE (2.3)

**Module:** Inventory > Wastage Tracking & Analytics
**Module Key:** `wastage_tracking`
**Priority:** CRITICAL - Foundation Module (Build Second)
**Estimated Duration:** 5-7 days
**Version:** 1.0.0
**Created:** 2024-12-04

---

## 1. OVERVIEW

### 1.1 Purpose
Centralized wastage data aggregation, cost tracking, and analytics across the entire supply chain from farm to customer. Provides photo documentation, cost allocation (Farm vs Us), and repacking workflow for damaged items.

### 1.2 Dependencies
**Required:**
- Batch Tracking (Module 2.2) - Batch numbers
- Supabase Storage - Photo uploads
- User Authentication

**Used By:**
- GRN Management (Module 1.2) - Receiving damage/reject
- Grading & Sorting (Module 1.3) - QC wastage
- Packing (Module 1.4) - Overfill wastage
- Inventory (Module 2.1) - Cold storage damage
- B2B Tickets (Module 7.1) - Customer claims
- B2C Tickets (Module 7.2) - Customer claims
- Reporting Module (Module 8) - Analytics

---

## 2. DATABASE SCHEMA

### 2.1 Tables

#### **wastage_events**
Primary table for all wastage events across the supply chain.

```sql
CREATE TABLE IF NOT EXISTS wastage_events (
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE DEFAULT gen_random_uuid(), -- Unique event identifier

    -- Batch & Stage
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL, -- receiving, grading, packing, cold_storage, customer
    wastage_type VARCHAR(100) NOT NULL, -- damage, reject, qc, overfill, partial_damage, full_loss, customer_claim

    -- Wastage Details
    item_id INTEGER, -- Link to items table (when implemented)
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL, -- Quantity wasted (kg, pcs, etc.)
    unit VARCHAR(50) NOT NULL, -- kg, pcs, boxes, etc.

    -- Cost Allocation
    cost_allocation VARCHAR(20) NOT NULL, -- 'farm' or 'us'
    estimated_cost DECIMAL(10, 2), -- Estimated cost of wastage (INR)

    -- Reason & Notes
    reason TEXT, -- Brief reason (dropdown selection)
    notes TEXT, -- Additional notes

    -- Location
    location VARCHAR(100), -- receiving_area, processing_area, cold_storage, vehicle, etc.

    -- Related Documents
    po_id INTEGER, -- Link to purchase_orders (when implemented)
    grn_id INTEGER, -- Link to grns (when implemented)
    so_id INTEGER, -- Link to sales_orders (when implemented)
    ticket_id INTEGER, -- Link to tickets (customer claims)

    -- Timestamps & User
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_cost_allocation CHECK (cost_allocation IN ('farm', 'us')),
    CONSTRAINT check_quantity_positive CHECK (quantity > 0)
);

CREATE INDEX idx_wastage_events_batch_id ON wastage_events(batch_id);
CREATE INDEX idx_wastage_events_stage ON wastage_events(stage);
CREATE INDEX idx_wastage_events_wastage_type ON wastage_events(wastage_type);
CREATE INDEX idx_wastage_events_cost_allocation ON wastage_events(cost_allocation);
CREATE INDEX idx_wastage_events_created_at ON wastage_events(created_at DESC);
CREATE INDEX idx_wastage_events_item_name ON wastage_events(item_name);

COMMENT ON TABLE wastage_events IS 'Centralized log of all wastage events across supply chain';
COMMENT ON COLUMN wastage_events.cost_allocation IS 'Who bears the cost: farm (deducted from invoice) or us (absorbed)';
COMMENT ON COLUMN wastage_events.estimated_cost IS 'Estimated cost impact in INR';
```

---

#### **wastage_photos**
Photos documenting wastage events (mandatory for all wastage).

```sql
CREATE TABLE IF NOT EXISTS wastage_photos (
    id SERIAL PRIMARY KEY,
    wastage_event_id INTEGER NOT NULL REFERENCES wastage_events(id) ON DELETE CASCADE,

    -- Photo Details
    photo_url TEXT NOT NULL, -- Supabase Storage URL
    photo_path VARCHAR(500) NOT NULL, -- Path in Supabase bucket
    file_name VARCHAR(255) NOT NULL,
    file_size_kb INTEGER,

    -- Metadata
    gps_latitude DECIMAL(10, 8), -- GPS coordinates (if available from mobile)
    gps_longitude DECIMAL(11, 8),
    device_info VARCHAR(255), -- Camera/device used

    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_photo_url_not_empty CHECK (photo_url != '')
);

CREATE INDEX idx_wastage_photos_event_id ON wastage_photos(wastage_event_id);
CREATE INDEX idx_wastage_photos_uploaded_at ON wastage_photos(uploaded_at DESC);

COMMENT ON TABLE wastage_photos IS 'Photo documentation for all wastage events (mandatory)';
```

---

#### **wastage_repacking**
Tracks repacking events when damaged items are consolidated.

```sql
CREATE TABLE IF NOT EXISTS wastage_repacking (
    id SERIAL PRIMARY KEY,

    -- Parent & Child Batches
    parent_batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    child_batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Repacking Details
    wastage_event_id INTEGER REFERENCES wastage_events(id) ON DELETE SET NULL, -- Original damage event
    damaged_quantity DECIMAL(10, 2) NOT NULL,
    repacked_quantity DECIMAL(10, 2) NOT NULL,
    wastage_in_repacking DECIMAL(10, 2) DEFAULT 0, -- Additional wastage during repacking

    -- Reason & Notes
    reason TEXT NOT NULL,
    notes TEXT,

    -- Timestamps & User
    repacked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    repacked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_damaged_quantity_positive CHECK (damaged_quantity > 0),
    CONSTRAINT check_repacked_quantity_positive CHECK (repacked_quantity > 0),
    CONSTRAINT check_wastage_calculation CHECK (repacked_quantity <= damaged_quantity)
);

CREATE INDEX idx_wastage_repacking_parent_batch ON wastage_repacking(parent_batch_id);
CREATE INDEX idx_wastage_repacking_child_batch ON wastage_repacking(child_batch_id);
CREATE INDEX idx_wastage_repacking_wastage_event ON wastage_repacking(wastage_event_id);

COMMENT ON TABLE wastage_repacking IS 'Tracks repacking of damaged items into new batches';
COMMENT ON COLUMN wastage_repacking.wastage_in_repacking IS 'Additional wastage that occurred during repacking process';
```

---

#### **wastage_categories**
Predefined wastage categories and reasons for dropdown selection.

```sql
CREATE TABLE IF NOT EXISTS wastage_categories (
    id SERIAL PRIMARY KEY,
    stage VARCHAR(50) NOT NULL, -- receiving, grading, packing, cold_storage, customer
    wastage_type VARCHAR(100) NOT NULL, -- damage, reject, qc, overfill, etc.
    reason VARCHAR(255) NOT NULL, -- "Transport damage", "Quality below spec", etc.
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_wastage_categories_stage ON wastage_categories(stage);
CREATE INDEX idx_wastage_categories_wastage_type ON wastage_categories(wastage_type);

COMMENT ON TABLE wastage_categories IS 'Predefined wastage reasons for consistent categorization';

-- Insert default categories
INSERT INTO wastage_categories (stage, wastage_type, reason, description, display_order) VALUES
-- Receiving stage
('receiving', 'damage', 'Transport damage', 'Damaged during transportation from farm', 10),
('receiving', 'damage', 'Handling damage', 'Damaged during unloading/handling', 20),
('receiving', 'damage', 'Packaging damage', 'Damaged packaging leading to produce damage', 30),
('receiving', 'reject', 'Below quality spec', 'Quality does not meet minimum standards', 40),
('receiving', 'reject', 'Wrong variety', 'Farm sent wrong variety/type', 50),
('receiving', 'reject', 'Overripe', 'Produce is overripe and unsellable', 60),
('receiving', 'reject', 'Underripe', 'Produce is underripe and needs more time', 70),

-- Grading stage
('grading', 'qc', 'Size out of spec', 'Size does not meet customer requirements', 80),
('grading', 'qc', 'Color out of spec', 'Color not acceptable', 90),
('grading', 'qc', 'Blemishes', 'Surface blemishes/defects', 100),
('grading', 'qc', 'Internal damage', 'Damage found during inspection', 110),

-- Packing stage
('packing', 'overfill', 'Weight overfill', 'Packs weigh more than target (yield loss)', 120),
('packing', 'damage', 'Packing damage', 'Damaged during packing process', 130),

-- Cold storage stage
('cold_storage', 'partial_damage', 'Condensation damage', 'Moisture damage in storage', 140),
('cold_storage', 'partial_damage', 'Temperature fluctuation', 'Quality degradation due to temp issues', 150),
('cold_storage', 'partial_damage', 'Age degradation', 'Natural aging/shelf life expiry', 160),
('cold_storage', 'full_loss', 'Complete spoilage', 'Entire batch/pack spoiled', 170),
('cold_storage', 'full_loss', 'Contamination', 'Cross-contamination or pest damage', 180),

-- Customer stage
('customer', 'customer_claim', 'Arrived damaged', 'Customer received damaged goods', 190),
('customer', 'customer_claim', 'Quality complaint', 'Customer complaint about quality', 200),
('customer', 'customer_claim', 'Short shelf life', 'Produce expired too quickly', 210);
```

---

#### **wastage_thresholds**
Configurable thresholds for wastage alerts (admin-configurable).

```sql
CREATE TABLE IF NOT EXISTS wastage_thresholds (
    id SERIAL PRIMARY KEY,

    -- Threshold Scope
    scope_type VARCHAR(50) NOT NULL, -- 'global', 'stage', 'farm', 'item'
    scope_value VARCHAR(255), -- NULL for global, farm name, item name, etc.

    -- Threshold Details
    stage VARCHAR(50), -- NULL for global, specific stage otherwise
    threshold_percentage DECIMAL(5, 2) NOT NULL, -- e.g., 5.00 = 5%
    alert_level VARCHAR(20) NOT NULL, -- 'critical', 'warning', 'info'

    -- Active/Inactive
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_threshold_positive CHECK (threshold_percentage > 0),
    CONSTRAINT check_alert_level CHECK (alert_level IN ('critical', 'warning', 'info'))
);

CREATE INDEX idx_wastage_thresholds_scope ON wastage_thresholds(scope_type, scope_value);
CREATE INDEX idx_wastage_thresholds_stage ON wastage_thresholds(stage);

COMMENT ON TABLE wastage_thresholds IS 'Configurable wastage thresholds for automated alerts';

-- Insert default thresholds
INSERT INTO wastage_thresholds (scope_type, stage, threshold_percentage, alert_level) VALUES
('global', 'receiving', 5.00, 'warning'),
('global', 'receiving', 10.00, 'critical'),
('global', 'grading', 10.00, 'warning'),
('global', 'grading', 15.00, 'critical'),
('global', 'packing', 5.00, 'warning'),
('global', 'cold_storage', 8.00, 'warning'),
('global', 'cold_storage', 12.00, 'critical');
```

---

## 3. BACKEND API

### 3.1 Routes (`app/routes/wastage_tracking.py`)

#### **POST /api/wastage/log**
Log a new wastage event (called by all modules).

**Request:**
```json
{
  "batch_number": "B001",
  "stage": "receiving",
  "wastage_type": "damage",
  "item_name": "Tomatoes",
  "quantity": 10.5,
  "unit": "kg",
  "cost_allocation": "farm",
  "estimated_cost": 525.00,
  "reason": "Transport damage",
  "notes": "Damaged during heavy rain",
  "location": "receiving_area",
  "po_id": 123,
  "grn_id": 456,
  "photos": [
    {
      "file": "base64_encoded_or_file_upload",
      "filename": "damage1.jpg"
    }
  ]
}
```

**Response:**
```json
{
  "wastage_event_id": 789,
  "event_id": "uuid-here",
  "batch_number": "B001",
  "photos_uploaded": 1,
  "created_at": "2024-12-04T10:00:00Z"
}
```

**Authentication:** Required
**Permission:** User with module access
**Validation:** Minimum 1 photo required

---

#### **GET /api/wastage/by-batch/{batch_number}**
Get all wastage events for a specific batch.

**Response:**
```json
{
  "batch_number": "B001",
  "total_wastage_events": 3,
  "total_quantity_wasted": 25.5,
  "total_estimated_cost": 1275.00,
  "cost_breakdown": {
    "farm": 850.00,
    "us": 425.00
  },
  "events": [
    {
      "event_id": "uuid-1",
      "stage": "receiving",
      "wastage_type": "damage",
      "quantity": 10.5,
      "unit": "kg",
      "cost_allocation": "farm",
      "estimated_cost": 525.00,
      "reason": "Transport damage",
      "photos": ["url1", "url2"],
      "created_at": "2024-12-04T10:00:00Z",
      "created_by": "John Doe"
    }
  ]
}
```

**Authentication:** Required
**Permission:** Any authenticated user

---

#### **GET /api/wastage/analytics/by-farm**
Wastage analytics by farm.

**Query Params:**
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)
- `farm_id`: Optional farm filter

**Response:**
```json
{
  "date_range": {
    "from": "2024-12-01",
    "to": "2024-12-31"
  },
  "farms": [
    {
      "farm_name": "Farm A",
      "total_wastage_kg": 150.5,
      "total_cost": 7525.00,
      "wastage_percentage": 8.5,
      "breakdown_by_type": {
        "damage": 100.0,
        "reject": 50.5
      },
      "breakdown_by_stage": {
        "receiving": 120.0,
        "grading": 30.5
      }
    }
  ]
}
```

**Authentication:** Required
**Permission:** Admin or Manager

---

#### **GET /api/wastage/analytics/by-stage**
Wastage analytics by stage.

**Query Params:**
- `date_from`: Start date
- `date_to`: End date

**Response:**
```json
{
  "stages": [
    {
      "stage": "receiving",
      "stage_name": "Receiving",
      "total_wastage_kg": 200.0,
      "total_cost": 10000.00,
      "percentage_of_total": 45.0,
      "event_count": 25,
      "avg_wastage_per_event": 8.0,
      "top_reasons": [
        {"reason": "Transport damage", "count": 15},
        {"reason": "Below quality spec", "count": 10}
      ]
    }
  ]
}
```

**Authentication:** Required
**Permission:** Admin or Manager

---

#### **GET /api/wastage/analytics/by-product**
Wastage analytics by product/item.

**Query Params:**
- `date_from`: Start date
- `date_to`: End date
- `item_name`: Optional item filter

**Response:**
```json
{
  "products": [
    {
      "item_name": "Tomatoes",
      "total_wastage_kg": 180.0,
      "total_cost": 9000.00,
      "wastage_percentage": 6.5,
      "problematic_stages": [
        {"stage": "grading", "wastage_kg": 100.0},
        {"stage": "receiving", "wastage_kg": 80.0}
      ]
    }
  ]
}
```

**Authentication:** Required
**Permission:** Admin or Manager

---

#### **GET /api/wastage/analytics/trends**
Wastage trends over time (daily/weekly/monthly).

**Query Params:**
- `date_from`: Start date
- `date_to`: End date
- `granularity`: 'daily', 'weekly', 'monthly'

**Response:**
```json
{
  "granularity": "daily",
  "data_points": [
    {
      "date": "2024-12-01",
      "total_wastage_kg": 25.5,
      "total_cost": 1275.00,
      "event_count": 5
    },
    {
      "date": "2024-12-02",
      "total_wastage_kg": 18.0,
      "total_cost": 900.00,
      "event_count": 3
    }
  ]
}
```

**Authentication:** Required
**Permission:** Admin or Manager

---

#### **POST /api/wastage/repack**
Initiate repacking workflow for damaged items.

**Request:**
```json
{
  "parent_batch_number": "B001",
  "wastage_event_id": 789,
  "damaged_quantity": 20.0,
  "repacked_quantity": 18.0,
  "wastage_in_repacking": 2.0,
  "reason": "Cold storage condensation damage",
  "notes": "Repacked into smaller portions",
  "photos": [...]
}
```

**Response:**
```json
{
  "parent_batch": "B001",
  "new_batch_number": "B001R",
  "new_batch_id": 2,
  "repacking_id": 123,
  "repacked_quantity": 18.0,
  "created_at": "2024-12-04T10:00:00Z"
}
```

**Authentication:** Required
**Permission:** User with packing/inventory access
**Validation:**
- Parent batch cannot already have a repacked child
- Repacked quantity must be <= damaged quantity

---

#### **GET /api/wastage/categories**
Get all wastage categories for dropdowns.

**Query Params:**
- `stage`: Filter by stage (optional)

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "stage": "receiving",
      "wastage_type": "damage",
      "reason": "Transport damage",
      "description": "Damaged during transportation from farm"
    }
  ]
}
```

**Authentication:** Required
**Permission:** Any authenticated user

---

#### **GET /api/wastage/thresholds**
Get configured wastage thresholds.

**Response:**
```json
{
  "thresholds": [
    {
      "id": 1,
      "scope_type": "global",
      "stage": "receiving",
      "threshold_percentage": 5.00,
      "alert_level": "warning"
    }
  ]
}
```

**Authentication:** Required
**Permission:** Admin only

---

#### **PUT /api/wastage/thresholds/{id}**
Update wastage threshold (admin only).

**Request:**
```json
{
  "threshold_percentage": 7.00,
  "alert_level": "warning",
  "is_active": true
}
```

**Authentication:** Required
**Permission:** Admin only

---

#### **GET /api/wastage/alerts**
Get current wastage alerts (based on thresholds).

**Response:**
```json
{
  "alerts": [
    {
      "alert_level": "critical",
      "message": "Receiving wastage for Farm A exceeded 10% threshold",
      "farm": "Farm A",
      "stage": "receiving",
      "current_percentage": 12.5,
      "threshold": 10.0,
      "period": "last_7_days"
    }
  ]
}
```

**Authentication:** Required
**Permission:** Admin or Manager

---

### 3.2 Service Layer (`app/services/wastage_tracking_service.py`)

**Key Functions:**
- `log_wastage_event(event_data)` - Create wastage event with photos
- `upload_wastage_photos(event_id, photos)` - Upload to Supabase Storage
- `get_wastage_by_batch(batch_number)` - All wastage for batch
- `get_wastage_analytics_by_farm(date_from, date_to)` - Farm performance
- `get_wastage_analytics_by_stage(date_from, date_to)` - Stage analysis
- `get_wastage_analytics_by_product(date_from, date_to)` - Product analysis
- `get_wastage_trends(date_from, date_to, granularity)` - Time series
- `initiate_repacking(repack_data)` - Create repacked batch
- `get_wastage_categories(stage)` - Dropdown options
- `check_threshold_alerts()` - Evaluate current wastage vs thresholds
- `calculate_cost_impact(batch_number)` - Total cost for batch

---

### 3.3 Schemas (`app/schemas/wastage_tracking.py`)

**Request Models:**
- `LogWastageRequest`
- `PhotoUploadRequest`
- `RepackRequest`
- `UpdateThresholdRequest`

**Response Models:**
- `WastageEventResponse`
- `WastageByBatchResponse`
- `WastageAnalyticsByFarm`
- `WastageAnalyticsByStage`
- `WastageAnalyticsByProduct`
- `WastageTrendsResponse`
- `WastageCategoryResponse`
- `WastageThresholdResponse`
- `WastageAlertResponse`

**Enums:**
- `WastageStage` - receiving, grading, packing, cold_storage, customer
- `WastageType` - damage, reject, qc, overfill, partial_damage, full_loss, customer_claim
- `CostAllocation` - farm, us
- `AlertLevel` - critical, warning, info

---

## 4. FRONTEND

### 4.1 Pages

#### **WastageTrackingPage.jsx** (`frontend/src/pages/WastageTracking/WastageTrackingPage.jsx`)
Main wastage tracking dashboard with analytics.

**Features:**
- Summary cards (total wastage this month, cost impact, alerts)
- Charts: Wastage by stage, by farm, trends
- Recent wastage events list
- Quick filters (date range, stage, farm)

---

#### **WastageLogForm.jsx** (`frontend/src/pages/WastageTracking/WastageLogForm.jsx`)
Form to log wastage event (usually embedded in other modules).

**Features:**
- Batch number input (auto-complete)
- Stage & type selection
- Item and quantity inputs
- Cost allocation toggle (Farm/Us)
- Reason dropdown (from categories)
- Photo upload (drag & drop, camera on mobile)
- Notes field
- Submit button

---

#### **WastageAnalyticsPage.jsx** (`frontend/src/pages/WastageTracking/WastageAnalyticsPage.jsx`)
Detailed analytics and reports.

**Features:**
- Date range selector
- Multiple analytics views:
  - By Farm (table + chart)
  - By Stage (pie chart + table)
  - By Product (bar chart + table)
  - Trends (line chart)
- Export to CSV/Excel
- Print-friendly view

---

#### **WastageAlertsPage.jsx** (`frontend/src/pages/WastageTracking/WastageAlertsPage.jsx`)
Alert management and threshold configuration.

**Features:**
- Current alerts list (color-coded)
- Threshold configuration table (admin only)
- Edit thresholds modal
- Alert history

---

### 4.2 Components

#### **WastageLogModal.jsx**
Modal for logging wastage (reusable across modules).

**Props:**
- `batchNumber`: Pre-filled batch
- `stage`: Pre-filled stage
- `onSuccess`: Callback after successful log

**Features:**
- Full wastage form
- Photo upload with preview
- Cost allocation toggle
- Category dropdown

---

#### **PhotoUpload.jsx**
Photo upload component with camera support.

**Props:**
- `onUpload`: Callback with uploaded files
- `maxPhotos`: Maximum photos allowed
- `required`: Whether photos are mandatory

**Features:**
- Drag & drop
- File browser
- Camera capture (mobile)
- Preview thumbnails
- Delete uploaded photos
- Validation (file size, type)

---

#### **CostAllocationToggle.jsx**
Toggle switch for Farm/Us cost allocation.

**Props:**
- `value`: 'farm' or 'us'
- `onChange`: Callback with new value

**Features:**
- Visual toggle (red for Farm, blue for Us)
- Labels
- Tooltip explaining impact

---

#### **WastageChart.jsx**
Reusable chart component for analytics.

**Props:**
- `type`: 'bar', 'pie', 'line'
- `data`: Chart data
- `title`: Chart title

**Features:**
- Responsive design
- Interactive tooltips
- Legend
- Export chart as image

---

#### **RepackingWorkflow.jsx**
Repacking workflow component.

**Props:**
- `parentBatch`: Original batch
- `wastageEventId`: Associated wastage event
- `onRepack`: Callback on success

**Features:**
- Damaged/repacked quantity inputs
- Photo upload
- Reason/notes
- Preview of new batch number (B###R)
- Validation

---

### 4.3 API Client (`frontend/src/api/wastageTracking.js`)

```javascript
import { apiClient } from './client';

export const wastageTrackingAPI = {
  // Log wastage
  logWastage: (data) => apiClient.post('/wastage/log', data),

  // Get wastage by batch
  getWastageByBatch: (batchNumber) => apiClient.get(`/wastage/by-batch/${batchNumber}`),

  // Analytics
  getAnalyticsByFarm: (params) => apiClient.get('/wastage/analytics/by-farm', { params }),
  getAnalyticsByStage: (params) => apiClient.get('/wastage/analytics/by-stage', { params }),
  getAnalyticsByProduct: (params) => apiClient.get('/wastage/analytics/by-product', { params }),
  getTrends: (params) => apiClient.get('/wastage/analytics/trends', { params }),

  // Repacking
  initiateRepack: (data) => apiClient.post('/wastage/repack', data),

  // Categories & Thresholds
  getCategories: (stage) => apiClient.get('/wastage/categories', { params: { stage } }),
  getThresholds: () => apiClient.get('/wastage/thresholds'),
  updateThreshold: (id, data) => apiClient.put(`/wastage/thresholds/${id}`, data),

  // Alerts
  getAlerts: () => apiClient.get('/wastage/alerts'),
};
```

---

## 5. BUSINESS LOGIC

### 5.1 Wastage Event Logging

**Process:**
1. User fills wastage form (batch, stage, type, quantity, cost allocation, photos)
2. Validate batch exists and is active
3. Validate minimum 1 photo uploaded
4. Upload photos to Supabase Storage
5. Insert wastage event record
6. Link photos to event
7. Update batch history (log wastage event)
8. Check thresholds and create alerts if exceeded
9. Return success response

**Photo Upload:**
- Target bucket: `wastage-photos`
- Path structure: `{batch_number}/{event_id}/{filename}`
- Max file size: 5MB per photo
- Allowed types: jpg, jpeg, png
- Store URL in database

---

### 5.2 Cost Allocation

**Farm Responsibility:**
- Receiving damage/reject (if farm's fault)
- Deducted from farm invoice (Zoho export)
- Flagged in PO export

**Us Responsibility:**
- Grading QC wastage (our quality standards)
- Packing overfill
- Cold storage damage
- Customer claims (unless proven farm issue)
- Absorbed in our costs

**Toggle Decision:**
- Default to "Farm" for receiving stage
- Default to "Us" for all other stages
- User can override with justification

---

### 5.3 Repacking Workflow

**Trigger:** Cold storage partial damage

**Process:**
1. User logs wastage event (cold storage damage)
2. User initiates repacking from wastage event
3. System checks:
   - Parent batch exists
   - Parent batch not already repacked
   - Quantities valid (repacked <= damaged)
4. Create new batch (B###R) via Batch Tracking API
5. Link child to parent
6. Log repacking record
7. Update inventory (reduce parent, add child)
8. Child batch gets FIFO priority

**Same-Batch Consolidation:**
- Multiple damaged packs (same batch) → Consolidated
- Retains B### with repack flag

**Mixed-Batch:**
- Parked for future (complex traceability)

---

### 5.4 Threshold Alerts

**Evaluation Logic:**
1. Scheduled job runs every hour
2. Calculate wastage % for each scope (global, farm, stage, product)
3. Compare against thresholds
4. If exceeded, create alert record
5. Send notification (in-app, email)
6. Alert persists until wastage drops below threshold

**Calculation Example:**
```
Wastage % = (Total Wastage Qty / Total Received Qty) * 100

For Farm A, Receiving stage, Last 7 days:
Total Received: 1000 kg
Total Wastage: 125 kg
Wastage % = 12.5%

Threshold: 10% (critical)
→ ALERT: "Farm A receiving wastage exceeded 10% threshold (12.5%)"
```

---

### 5.5 Analytics Calculations

**By Farm:**
- Total wastage quantity (sum across all batches from farm)
- Total cost (sum of estimated_cost where cost_allocation = 'farm')
- Wastage % (wastage / total received from farm)
- Breakdown by type and stage

**By Stage:**
- Total wastage quantity per stage
- Percentage of total wastage
- Average wastage per event
- Top reasons (most frequent)

**By Product:**
- Total wastage quantity per product
- Wastage % (wastage / total received for product)
- Problematic stages (highest wastage)

**Trends:**
- Time series data (daily/weekly/monthly)
- Total wastage, cost, event count per period
- Compare periods (growth/decline)

---

## 6. INTEGRATION POINTS

### 6.1 Called By (Other Modules)

**GRN Management (1.2):**
- Logs receiving damage/reject
- Uploads photos of damaged goods

**Grading & Sorting (1.3):**
- Logs QC wastage
- Uploads photos of quality issues

**Packing (1.4):**
- Logs overfill wastage
- Logs packing damage

**Inventory (2.1):**
- Logs cold storage damage
- Initiates repacking workflow

**B2B/B2C Tickets (7.1, 7.2):**
- Logs customer damage claims
- Links customer photos to wastage

---

### 6.2 Calls (Dependencies)

**Batch Tracking (2.2):**
- Links all wastage events to batch
- Creates repacked batch (B###R)
- Queries batch details

**Supabase Storage:**
- Uploads wastage photos
- Generates signed URLs for viewing

**Notification System:**
- Sends alerts when thresholds exceeded

---

## 7. TESTING CHECKLIST

### 7.1 Unit Tests
- [ ] Log wastage with photos (validation)
- [ ] Cost allocation logic
- [ ] Photo upload to Supabase
- [ ] Repacking validation (one per batch)
- [ ] Threshold evaluation logic
- [ ] Analytics calculations (farm, stage, product)

### 7.2 Integration Tests
- [ ] Log wastage from GRN module
- [ ] Log wastage from grading module
- [ ] Log wastage from packing module
- [ ] Query wastage by batch
- [ ] Generate analytics reports
- [ ] Initiate repacking workflow
- [ ] Threshold alerts trigger correctly

### 7.3 Performance Tests
- [ ] Photo upload (multiple large files)
- [ ] Analytics queries with 1000+ events
- [ ] Threshold evaluation with many farms/items
- [ ] Concurrent wastage logging

---

## 8. DEPLOYMENT

### 8.1 Migration Order
1. Run `016_wastage_tracking.sql` to create tables
2. Run `017_wastage_tracking_module.sql` to register module
3. Create Supabase Storage bucket: `wastage-photos`
4. Deploy backend code
5. Deploy frontend code

### 8.2 Module Registration

```sql
-- Register Wastage Tracking Module
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'wastage_tracking',
    'Wastage Tracking & Analytics',
    'Centralized wastage tracking with photo documentation and cost analysis',
    'AssessmentOutlined',
    (SELECT id FROM modules WHERE module_key = 'inventory'),
    true,
    20
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Wastage Tracking & Analytics',
    description = 'Centralized wastage tracking with photo documentation and cost analysis',
    display_order = 20;
```

### 8.3 Supabase Storage Setup

```sql
-- Create storage bucket for wastage photos
INSERT INTO storage.buckets (id, name, public)
VALUES ('wastage-photos', 'wastage-photos', true);

-- Set storage policies (authenticated users can upload)
CREATE POLICY "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'wastage-photos');

CREATE POLICY "Allow public read access"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'wastage-photos');
```

### 8.4 Scheduled Jobs

Add to `app/scheduler.py`:

```python
# Check wastage thresholds (hourly)
scheduler.add_job(
    wastage_tracking_service.check_threshold_alerts,
    trigger='cron',
    minute=0,  # Top of every hour
    id='check_wastage_thresholds'
)
```

---

## 9. SECURITY CONSIDERATIONS

### 9.1 Access Control
- All authenticated users can log wastage
- Only users with module access can view analytics
- Admin only: Configure thresholds
- Photos publicly viewable (with URL)
- No deletion of wastage events (audit trail)

### 9.2 Data Integrity
- Wastage events immutable (no edit after creation)
- Photos required for all wastage
- Cost allocation validated
- Quantities must be positive
- Repacking validation (one per batch)

### 9.3 Photo Storage
- Max file size enforced (5MB)
- File type validation
- Virus scanning (future enhancement)
- Retention policy (parked for discussion)

---

## 10. FUTURE ENHANCEMENTS

### 10.1 Phase 2 (Post-Launch)
- AI-powered photo analysis (damage classification)
- OCR for extracting data from photos
- Predictive analytics (wastage forecasting)
- Integration with IoT sensors (temperature, humidity)
- Mobile app for on-site wastage logging
- Photo retention policy (legal compliance)
- Insurance claim integration
- Supplier scorecards (wastage-based)
- Advanced cost analysis (profitability per batch)
- Mixed-batch consolidation (complex traceability)

---

**End of Technical Design: Wastage Tracking Module**
