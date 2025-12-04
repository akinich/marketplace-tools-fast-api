# TECHNICAL DESIGN: BATCH TRACKING MODULE (2.2)

**Module:** Inventory > Batch Tracking
**Module Key:** `batch_tracking`
**Priority:** CRITICAL - Foundation Module (Build First)
**Estimated Duration:** 3-4 days
**Version:** 1.0.0
**Created:** 2024-12-04

---

## 1. OVERVIEW

### 1.1 Purpose
Complete traceability system from farm to customer using unique sequential batch numbers. Provides complete audit trail of batch journey through all stages of the supply chain.

### 1.2 Dependencies
**Required:**
- None (foundation module)

**Used By:**
- GRN Management (Module 1.2) - Generates batches
- Grading & Sorting (Module 1.3) - Tracks batch
- Packing (Module 1.4) - Tracks batch
- Inventory (Module 2.1) - Batch-wise inventory
- Wastage Tracking (Module 2.3) - Links wastage to batch
- Order Allocation (Module 3.2) - Allocates batches
- All reporting modules

---

## 2. DATABASE SCHEMA

### 2.1 Tables

#### **batches**
Primary table for batch tracking.

```sql
CREATE TABLE IF NOT EXISTS batches (
    id SERIAL PRIMARY KEY,
    batch_number VARCHAR(50) UNIQUE NOT NULL, -- B001, B002, B003, etc.

    -- Batch Type
    is_repacked BOOLEAN DEFAULT FALSE, -- TRUE if this is a repacked batch (B###R)
    parent_batch_id INTEGER REFERENCES batches(id) ON DELETE SET NULL, -- Link to original batch if repacked

    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'ordered', -- ordered, received, in_grading, in_packing, in_inventory, allocated, in_transit, delivered, archived

    -- Linked Documents
    po_id INTEGER, -- Link to purchase_orders table (when implemented)
    grn_id INTEGER, -- Link to grns table (when implemented)

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE, -- When batch moves to historical archive (3 days after delivery)

    -- Audit
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    CONSTRAINT check_repack_parent CHECK (
        (is_repacked = FALSE AND parent_batch_id IS NULL) OR
        (is_repacked = TRUE AND parent_batch_id IS NOT NULL)
    )
);

CREATE INDEX idx_batches_batch_number ON batches(batch_number);
CREATE INDEX idx_batches_status ON batches(status);
CREATE INDEX idx_batches_created_at ON batches(created_at DESC);
CREATE INDEX idx_batches_parent_batch ON batches(parent_batch_id);
CREATE INDEX idx_batches_is_repacked ON batches(is_repacked);

COMMENT ON TABLE batches IS 'Master table for batch tracking and traceability';
COMMENT ON COLUMN batches.batch_number IS 'Sequential batch number (B001, B002...) or repacked (B001R)';
COMMENT ON COLUMN batches.is_repacked IS 'TRUE if batch was created from repacking damaged items';
COMMENT ON COLUMN batches.parent_batch_id IS 'Original batch ID if this is a repacked batch';
```

#### **batch_history**
Audit trail of all events in batch lifecycle.

```sql
CREATE TABLE IF NOT EXISTS batch_history (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Event Details
    stage VARCHAR(50) NOT NULL, -- po, grn, grading, packing, inventory, allocation, delivery
    event_type VARCHAR(100) NOT NULL, -- created, received, graded, packed, allocated, delivered, status_changed, etc.
    event_details JSONB, -- Flexible storage for stage-specific data

    -- Status Change
    old_status VARCHAR(50),
    new_status VARCHAR(50),

    -- Timestamps & User
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- Location
    location VARCHAR(100) -- receiving_area, processing_area, packed_warehouse, vehicle, etc.
);

CREATE INDEX idx_batch_history_batch_id ON batch_history(batch_id);
CREATE INDEX idx_batch_history_stage ON batch_history(stage);
CREATE INDEX idx_batch_history_created_at ON batch_history(created_at DESC);

COMMENT ON TABLE batch_history IS 'Complete audit trail of batch journey through all stages';
COMMENT ON COLUMN batch_history.event_details IS 'JSON data specific to each stage (quantities, grades, allocations, etc.)';
```

#### **batch_documents**
Links batches to related documents (PO, GRN, SO, Invoices).

```sql
CREATE TABLE IF NOT EXISTS batch_documents (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,

    -- Document Type & ID
    document_type VARCHAR(50) NOT NULL, -- po, grn, so, invoice, packing_label
    document_id INTEGER NOT NULL, -- Foreign key to respective tables
    document_number VARCHAR(100), -- Human-readable reference (PO-001, GRN-001, etc.)

    -- Timestamps
    linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    linked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

CREATE INDEX idx_batch_documents_batch_id ON batch_documents(batch_id);
CREATE INDEX idx_batch_documents_document_type ON batch_documents(document_type);
CREATE INDEX idx_batch_documents_document_id ON batch_documents(document_type, document_id);

COMMENT ON TABLE batch_documents IS 'Links batches to all related documents for quick reference';
```

#### **batch_sequence**
Sequence counter for generating batch numbers.

```sql
CREATE TABLE IF NOT EXISTS batch_sequence (
    id SERIAL PRIMARY KEY,
    current_number INTEGER NOT NULL DEFAULT 0,
    prefix VARCHAR(10) DEFAULT 'B',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial record
INSERT INTO batch_sequence (current_number, prefix) VALUES (0, 'B')
ON CONFLICT DO NOTHING;

COMMENT ON TABLE batch_sequence IS 'Sequence generator for batch numbers';
```

---

## 3. BACKEND API

### 3.1 Routes (`app/routes/batch_tracking.py`)

#### **POST /api/batches/generate**
Generate new batch number (called by GRN module).

**Request:**
```json
{
  "po_id": 123,
  "grn_id": 456,
  "created_by": "user-uuid"
}
```

**Response:**
```json
{
  "batch_id": 1,
  "batch_number": "B001",
  "status": "ordered",
  "created_at": "2024-12-04T10:00:00Z"
}
```

**Authentication:** Required
**Permission:** User with GRN access

---

#### **GET /api/batches/{batch_number}**
Get complete batch details and history.

**Response:**
```json
{
  "batch_id": 1,
  "batch_number": "B001",
  "status": "delivered",
  "is_repacked": false,
  "parent_batch": null,
  "created_at": "2024-12-04T10:00:00Z",
  "archived_at": null,
  "documents": [
    {
      "document_type": "po",
      "document_number": "PO-001",
      "document_id": 123
    },
    {
      "document_type": "grn",
      "document_number": "GRN-001",
      "document_id": 456
    }
  ],
  "history": [
    {
      "stage": "po",
      "event_type": "created",
      "event_details": {"farm": "Farm A", "items": ["Tomatoes"]},
      "created_at": "2024-12-04T10:00:00Z",
      "created_by": "John Doe"
    }
  ]
}
```

**Authentication:** Required
**Permission:** Any authenticated user

---

#### **GET /api/batches/{batch_number}/timeline**
Get visual timeline of batch journey.

**Response:**
```json
{
  "batch_number": "B001",
  "timeline": [
    {
      "stage": "po",
      "stage_name": "Purchase Order",
      "timestamp": "2024-12-04T10:00:00Z",
      "status": "completed",
      "details": {
        "po_number": "PO-001",
        "farm": "Farm A"
      }
    },
    {
      "stage": "grn",
      "stage_name": "Goods Receipt",
      "timestamp": "2024-12-05T08:00:00Z",
      "status": "completed",
      "details": {
        "grn_number": "GRN-001",
        "received_qty": 100
      }
    }
  ]
}
```

**Authentication:** Required
**Permission:** Any authenticated user

---

#### **POST /api/batches/search**
Search batches by various criteria.

**Request:**
```json
{
  "batch_number": "B001",
  "po_number": "PO-001",
  "grn_number": "GRN-001",
  "so_number": "SO-001",
  "farm_name": "Farm A",
  "item_name": "Tomatoes",
  "customer_name": "Restaurant X",
  "status": "delivered",
  "date_from": "2024-12-01",
  "date_to": "2024-12-31",
  "is_archived": false,
  "page": 1,
  "limit": 50
}
```

**Response:**
```json
{
  "batches": [
    {
      "batch_id": 1,
      "batch_number": "B001",
      "status": "delivered",
      "is_repacked": false,
      "created_at": "2024-12-04T10:00:00Z",
      "farm": "Farm A",
      "current_location": "delivered"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**Authentication:** Required
**Permission:** Any authenticated user

---

#### **POST /api/batches/{batch_number}/repack**
Create repacked batch from damaged items.

**Request:**
```json
{
  "reason": "Cold storage damage",
  "damaged_quantity": 10,
  "repacked_quantity": 8,
  "photos": ["url1", "url2"],
  "notes": "Some packs had condensation damage"
}
```

**Response:**
```json
{
  "parent_batch": "B001",
  "new_batch_number": "B001R",
  "new_batch_id": 2,
  "status": "in_inventory",
  "created_at": "2024-12-06T10:00:00Z"
}
```

**Authentication:** Required
**Permission:** User with packing/inventory access

---

#### **GET /api/batches/active**
List all active batches (not archived).

**Query Params:**
- `status`: Filter by status
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)

**Response:**
```json
{
  "batches": [...],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

**Authentication:** Required
**Permission:** Any authenticated user

---

#### **POST /api/batches/{batch_number}/archive**
Archive batch (automatically triggered 3 days after delivery).

**Response:**
```json
{
  "batch_number": "B001",
  "archived_at": "2024-12-09T10:00:00Z",
  "status": "archived"
}
```

**Authentication:** System/Scheduled Job
**Permission:** System only

---

#### **POST /api/batches/{batch_number}/history**
Add event to batch history (called by other modules).

**Request:**
```json
{
  "stage": "grading",
  "event_type": "graded",
  "event_details": {
    "grade_a": 50,
    "grade_b": 30,
    "grade_c": 10,
    "wastage": 10
  },
  "new_status": "in_grading",
  "location": "processing_area"
}
```

**Response:**
```json
{
  "history_id": 123,
  "batch_number": "B001",
  "created_at": "2024-12-05T10:00:00Z"
}
```

**Authentication:** Required
**Permission:** User with module access

---

### 3.2 Service Layer (`app/services/batch_tracking_service.py`)

**Key Functions:**
- `generate_batch_number()` - Atomic batch number generation
- `get_batch_details(batch_number)` - Complete batch information
- `get_batch_timeline(batch_number)` - Visual timeline
- `search_batches(filters)` - Search with multiple criteria
- `create_repacked_batch(parent_batch, details)` - Repacking workflow
- `add_batch_history(batch_number, event)` - Log event
- `archive_old_batches()` - Auto-archive batches 3 days after delivery
- `link_document_to_batch(batch_number, document_type, document_id)` - Link documents
- `get_batch_wastage_summary(batch_number)` - All wastage for batch

---

### 3.3 Schemas (`app/schemas/batch_tracking.py`)

**Request Models:**
- `GenerateBatchRequest`
- `RepackBatchRequest`
- `AddBatchHistoryRequest`
- `SearchBatchesRequest`

**Response Models:**
- `BatchResponse`
- `BatchDetailResponse`
- `BatchTimelineResponse`
- `BatchHistoryEvent`
- `BatchDocumentLink`
- `BatchSearchResponse`

**Enums:**
- `BatchStatus` - ordered, received, in_grading, in_packing, in_inventory, allocated, in_transit, delivered, archived
- `BatchStage` - po, grn, grading, packing, inventory, allocation, delivery
- `BatchEventType` - created, received, graded, packed, allocated, delivered, status_changed, etc.

---

## 4. FRONTEND

### 4.1 Pages

#### **BatchTrackingPage.jsx** (`frontend/src/pages/BatchTracking/BatchTrackingPage.jsx`)
Main batch tracking interface with search and list.

**Features:**
- Search bar (batch number, PO, GRN, SO, farm, item, customer)
- Advanced filters (status, date range, archived)
- Batch list with key info
- Click to view batch details

---

#### **BatchDetailPage.jsx** (`frontend/src/pages/BatchTracking/BatchDetailPage.jsx`)
Detailed view of single batch with complete timeline.

**Features:**
- Batch overview card
- Visual timeline (stages with timestamps)
- Linked documents (PO, GRN, SO, invoices)
- Complete history table
- Wastage summary for batch
- Photos from all stages
- Repack button (if applicable)

---

### 4.2 Components

#### **BatchTimeline.jsx**
Visual timeline component showing batch journey.

**Props:**
- `batchNumber`: Batch number
- `timeline`: Array of timeline events

**Features:**
- Vertical timeline with stages
- Icons for each stage
- Timestamps
- Click to expand details
- Color-coded status (completed, in-progress, pending)

---

#### **BatchSearch.jsx**
Advanced search form for batches.

**Props:**
- `onSearch`: Callback with search filters

**Features:**
- Text search (batch, PO, GRN, SO)
- Dropdown filters (status, farm, item)
- Date range picker
- Reset filters button
- Active filters display

---

#### **RepackingModal.jsx**
Modal for creating repacked batch.

**Props:**
- `parentBatch`: Original batch number
- `onRepack`: Callback on successful repack

**Features:**
- Form for repack details
- Photo upload
- Quantity inputs
- Reason/notes
- Preview of new batch number (B###R)

---

### 4.3 API Client (`frontend/src/api/batchTracking.js`)

```javascript
import { apiClient } from './client';

export const batchTrackingAPI = {
  // Generate batch
  generateBatch: (data) => apiClient.post('/batches/generate', data),

  // Get batch details
  getBatchDetails: (batchNumber) => apiClient.get(`/batches/${batchNumber}`),

  // Get timeline
  getBatchTimeline: (batchNumber) => apiClient.get(`/batches/${batchNumber}/timeline`),

  // Search batches
  searchBatches: (filters) => apiClient.post('/batches/search', filters),

  // Create repacked batch
  repackBatch: (batchNumber, data) => apiClient.post(`/batches/${batchNumber}/repack`, data),

  // Get active batches
  getActiveBatches: (params) => apiClient.get('/batches/active', { params }),

  // Add history event
  addBatchHistory: (batchNumber, event) => apiClient.post(`/batches/${batchNumber}/history`, event),
};
```

---

## 5. BUSINESS LOGIC

### 5.1 Batch Number Generation

**Algorithm:**
1. Lock `batch_sequence` table row (FOR UPDATE)
2. Increment `current_number` by 1
3. Format: `{prefix}{padded_number}` → "B001", "B002", etc.
4. Create batch record
5. Return batch number

**Thread-Safe:** Uses database transaction lock

**Repacked Format:**
- Original: B001
- Repacked: B001R
- Only ONE repack allowed per batch

---

### 5.2 Status Workflow

```
ordered → received → in_grading → in_packing → in_inventory →
allocated → in_transit → delivered → archived
```

**Status Transitions:**
- Controlled by respective modules (GRN, Grading, Packing, etc.)
- Each transition logged in `batch_history`
- Status validation enforced

---

### 5.3 Active Tracking Period

**Duration:** From PO creation to 3 days after delivery

**Auto-Archive Logic:**
1. Scheduled job runs daily (APScheduler)
2. Query batches with `status = 'delivered'` AND `delivered_at < NOW() - INTERVAL '3 days'`
3. Update `status = 'archived'`, set `archived_at`
4. Still searchable, but excluded from active lists

---

### 5.4 Repacking Workflow

**Trigger:** Cold storage damage

**Process:**
1. User identifies damaged items from batch B001
2. Logs wastage event (links to batch)
3. Initiates repacking via API
4. System creates new batch: B001R
5. Links B001R as child of B001 (`parent_batch_id`)
6. B001R gets FIFO priority in inventory allocation
7. **Validation:** Cannot repack B001R (one repack max)

**Same-Batch Consolidation:**
- Multiple damaged packs (same batch) → Consolidated into fewer packs
- Retains original batch number with repack flag

---

## 6. INTEGRATION POINTS

### 6.1 Called By (Other Modules)

**GRN Management (1.2):**
- Generates batch number at GRN creation
- Links batch to GRN and PO

**Grading & Sorting (1.3):**
- Updates batch status to "in_grading"
- Logs grading events (grades, QC wastage)

**Packing (1.4):**
- Updates batch status to "in_packing"
- Logs packing completion
- Triggers inventory update

**Inventory (2.1):**
- Queries batch details for allocation
- Updates status to "in_inventory", "allocated"

**Order Allocation (3.2):**
- Links batch to Sales Order
- Updates status to "allocated", "in_transit"

**Delivery (3.4):**
- Updates status to "delivered"
- Sets delivery timestamp (triggers 3-day archive countdown)

**Wastage Tracking (2.3):**
- Links wastage events to batch
- Repacking creates new batch

---

### 6.2 Calls (Dependencies)

**Wastage Tracking (2.3):**
- Queries wastage events for batch summary

**Photo Storage (Supabase):**
- Links photos from all stages to batch

---

## 7. TESTING CHECKLIST

### 7.1 Unit Tests
- [ ] Batch number generation (sequential, unique)
- [ ] Repacked batch format (B###R)
- [ ] Status transition validation
- [ ] Repack validation (one max per batch)
- [ ] Archive logic (3 days after delivery)

### 7.2 Integration Tests
- [ ] Generate batch from GRN
- [ ] Complete batch journey (PO → delivery)
- [ ] Search by various criteria
- [ ] View batch timeline
- [ ] Create repacked batch
- [ ] Link documents to batch
- [ ] Archive old batches

### 7.3 Performance Tests
- [ ] Batch number generation under concurrent load
- [ ] Search with 1000+ batches
- [ ] Timeline rendering with 50+ events
- [ ] Bulk archive operation

---

## 8. DEPLOYMENT

### 8.1 Migration Order
1. Run `014_batch_tracking.sql` to create tables
2. Run `015_batch_tracking_module.sql` to register module
3. Deploy backend code
4. Deploy frontend code

### 8.2 Module Registration

```sql
-- Register Batch Tracking Module
INSERT INTO modules (
    module_key,
    module_name,
    description,
    icon,
    parent_module_id,
    is_active,
    display_order
) VALUES (
    'batch_tracking',
    'Batch Tracking',
    'Complete batch traceability from farm to customer',
    'Timeline',
    (SELECT id FROM modules WHERE module_key = 'inventory'),
    true,
    10
) ON CONFLICT (module_key) DO UPDATE SET
    module_name = 'Batch Tracking',
    description = 'Complete batch traceability from farm to customer',
    display_order = 10;
```

### 8.3 Scheduled Jobs
Add to `app/scheduler.py`:

```python
# Auto-archive old batches (daily at 2 AM)
scheduler.add_job(
    batch_tracking_service.archive_old_batches,
    trigger='cron',
    hour=2,
    minute=0,
    id='archive_old_batches'
)
```

---

## 9. SECURITY CONSIDERATIONS

### 9.1 Access Control
- All authenticated users can view batches
- Only users with module access can create/modify batches
- Batch history immutable (no edit/delete)
- Archive operation restricted to system/admin

### 9.2 Data Integrity
- Batch numbers globally unique (DB constraint)
- Cannot delete batches (maintain traceability)
- Status transitions validated
- Repack validation (one per batch)

---

## 10. FUTURE ENHANCEMENTS

### 10.1 Phase 2 (Post-Launch)
- QR code generation for batch labels
- Mobile app for batch scanning
- Customer-facing batch lookup (transparency)
- Batch-wise profitability analysis
- Mixed-batch consolidation (complex traceability)
- Export batch data (CSV, PDF reports)
- Advanced analytics (batch performance, farm quality trends)

---

**End of Technical Design: Batch Tracking Module**
