# Development Planning Module - Technical Guide

**Version:** 1.0.1
**Audience:** Developers, System Architects, Database Administrators

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Reference](#api-reference)
4. [Service Layer Logic](#service-layer-logic)
5. [Frontend Architecture](#frontend-architecture)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Security & Permissions](#security--permissions)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Performance Considerations](#performance-considerations)

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  - Material-UI Components               │
│  - React Router                         │
│  - Form Validation                      │
│  - State Management                     │
└──────────────┬──────────────────────────┘
               │ REST API (HTTP/JSON)
┌──────────────▼──────────────────────────┐
│         Backend (FastAPI)               │
│  - Route Handlers                       │
│  - Service Layer                        │
│  - Pydantic Validation                  │
│  - Business Logic                       │
│  - Authentication/Authorization         │
└──────────────┬──────────────────────────┘
               │ asyncpg (async)
┌──────────────▼──────────────────────────┐
│       Database (PostgreSQL)             │
│  - Relational Data                      │
│  - Triggers for timestamps              │
│  - Indexes for performance              │
│  - Check constraints                    │
└─────────────────────────────────────────┘
```

### Module Structure

**Backend:**
```
backend/app/
├── routes/development.py           # API endpoints
├── schemas/development.py          # Pydantic models
├── services/development_service.py # Business logic
└── migrations/
    └── development_module_v1.0.0.sql

backend/
├── run_development_migration.py    # Migration runner
└── run_all_migrations.py          # All migrations checker
```

**Frontend:**
```
frontend/src/
├── pages/
│   └── DevelopmentModule.jsx       # Main router and components
└── api/
    └── index.js                    # API client (developmentAPI)
```

**Documentation:**
```
docs/development/
├── README.md                       # Overview
├── user-guide.md                   # User documentation
└── technical-guide.md              # This file
```

---

## Database Schema

### Entity Relationship Overview

```
user_profiles ──┬──< features ──┬──< feature_steps
                │                └──< feature_comments
                └──< feature_comments
                
auth.users (email) ← joined for email display
```

### Table: `features`

Primary table storing feature records.

```sql
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    priority VARCHAR(20) DEFAULT 'medium',
    target_date DATE,
    created_by_id UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_feature_status CHECK (
        status IN ('planned', 'in_development', 'testing', 'completed', 'on_hold')
    ),
    CONSTRAINT valid_feature_priority CHECK (
        priority IN ('low', 'medium', 'high', 'critical')
    )
);
```

**Columns:**
- `id` - Auto-incrementing primary key
- `title` - Feature title (max 200 characters)
- `description` - Detailed description (unlimited text)
- `status` - Current lifecycle status (enum: planned, in_development, testing, completed, on_hold)
- `priority` - Importance level (enum: low, medium, high, critical)
- `target_date` - Optional completion target (date only, no time)
- `created_by_id` - Foreign key to user_profiles (UUID)
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update (auto-updated via trigger)

**Indexes:**
```sql
CREATE INDEX idx_features_status ON features(status);
CREATE INDEX idx_features_priority ON features(priority);
CREATE INDEX idx_features_created_by ON features(created_by_id);
CREATE INDEX idx_features_target_date ON features(target_date);
CREATE INDEX idx_features_created_at ON features(created_at DESC);
```

### Table: `feature_steps`

Implementation steps/tasks for features.

```sql
CREATE TABLE feature_steps (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo',
    step_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_step_status CHECK (
        status IN ('todo', 'in_progress', 'done')
    )
);
```

**Columns:**
- `id` - Auto-incrementing primary key
- `feature_id` - Foreign key to features (cascading delete)
- `title` - Step title (max 200 characters)
- `description` - Optional step details
- `status` - Step status (enum: todo, in_progress, done)
- `step_order` - Display order (0-based, manual ordering)
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update

**Indexes:**
```sql
CREATE INDEX idx_feature_steps_feature_id ON feature_steps(feature_id);
CREATE INDEX idx_feature_steps_status ON feature_steps(status);
CREATE INDEX idx_feature_steps_order ON feature_steps(feature_id, step_order);
```

**Cascade Behavior:**
- Deleting a feature automatically deletes all its steps

### Table: `feature_comments`

Discussion comments on features.

```sql
CREATE TABLE feature_comments (
    id SERIAL PRIMARY KEY,
    feature_id INTEGER NOT NULL REFERENCES features(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Columns:**
- `id` - Auto-incrementing primary key
- `feature_id` - Foreign key to features (cascading delete)
- `user_id` - Foreign key to user_profiles (UUID)
- `comment` - Comment text (required, unlimited length)
- `created_at` - Timestamp of creation
- `updated_at` - Timestamp of last update

**Indexes:**
```sql
CREATE INDEX idx_feature_comments_feature_id ON feature_comments(feature_id);
CREATE INDEX idx_feature_comments_user_id ON feature_comments(user_id);
```

**Cascade Behavior:**
- Deleting a feature automatically deletes all its comments

### Database Triggers

**Auto-update `updated_at` timestamp:**

```sql
CREATE OR REPLACE FUNCTION update_features_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_features_updated_at
    BEFORE UPDATE ON features
    FOR EACH ROW
    EXECUTE FUNCTION update_features_updated_at();

CREATE TRIGGER trigger_feature_steps_updated_at
    BEFORE UPDATE ON feature_steps
    FOR EACH ROW
    EXECUTE FUNCTION update_features_updated_at();

CREATE TRIGGER trigger_feature_comments_updated_at
    BEFORE UPDATE ON feature_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_features_updated_at();
```

### Module Registration

The module is registered in the `modules` table:

```sql
INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active)
VALUES ('development', 'Development Planning', 'Plan features and track development progress', 'code', 11, TRUE)
ON CONFLICT (module_key) DO NOTHING;
```

---

## API Reference

Base URL: `/api/v1/development`

All endpoints require authentication via JWT token in `Authorization` header.

### Feature Endpoints

#### `GET /development`

List all features with pagination and filtering.

**Query Parameters:**
- `page` (integer, optional, default=1) - Page number
- `limit` (integer, optional, default=50, max=100) - Items per page
- `status` (string, optional) - Filter by status (planned, in_development, testing, completed, on_hold)
- `priority` (string, optional) - Filter by priority (low, medium, high, critical)

**Response:** `FeaturesListResponse`
```json
{
  "features": [
    {
      "id": 1,
      "title": "Add user authentication",
      "description": "Implement OAuth2 authentication...",
      "status": "in_development",
      "priority": "high",
      "target_date": "2025-12-31",
      "created_by_id": "uuid-here",
      "created_by_name": "John Doe",
      "created_by_email": "john@example.com",
      "created_at": "2025-11-20T10:00:00",
      "updated_at": "2025-11-20T15:30:00",
      "step_count": 5,
      "completed_steps": 3,
      "comment_count": 8
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 50,
  "total_pages": 1
}
```

**Authorization:** Authenticated user (any role)

---

#### `GET /development/stats`

Get feature statistics.

**Response:** `FeatureStatsResponse`
```json
{
  "total_features": 42,
  "planned": 10,
  "in_development": 15,
  "testing": 8,
  "completed": 7,
  "on_hold": 2,
  "by_priority": {
    "low": 8,
    "medium": 20,
    "high": 10,
    "critical": 4
  },
  "total_steps": 150,
  "completed_steps": 95
}
```

**Authorization:** Authenticated user (any role)

---

#### `GET /development/{feature_id}`

Get single feature with steps and comments.

**Path Parameters:**
- `feature_id` (integer) - Feature ID

**Response:** `FeatureDetailResponse`
```json
{
  "id": 1,
  "title": "Add user authentication",
  "description": "Implement OAuth2...",
  "status": "in_development",
  "priority": "high",
  "target_date": "2025-12-31",
  "created_by_id": "uuid",
  "created_by_name": "John Doe",
  "created_by_email": "john@example.com",
  "created_at": "2025-11-20T10:00:00",
  "updated_at": "2025-11-20T15:30:00",
  "steps": [
    {
      "id": 1,
      "feature_id": 1,
      "title": "Create database schema",
      "description": "Add users and roles tables",
      "status": "done",
      "step_order": 0,
      "created_at": "2025-11-20T10:05:00",
      "updated_at": "2025-11-20T12:00:00"
    }
  ],
  "comments": [
    {
      "id": 1,
      "feature_id": 1,
      "user_id": "uuid",
      "user_name": "Jane Smith",
      "user_email": "jane@example.com",
      "comment": "Started work on database schema",
      "created_at": "2025-11-20T10:10:00",
      "updated_at": "2025-11-20T10:10:00"
    }
  ]
}
```

**Authorization:** Authenticated user (any role)
**Errors:** 404 if feature not found

---

#### `POST /development`

Create a new feature.

**Request Body:** `CreateFeatureRequest`
```json
{
  "title": "Add user authentication",
  "description": "Implement OAuth2 authentication with social login support",
  "priority": "high",
  "target_date": "2025-12-31"
}
```

**Response:** `FeatureDetailResponse` (201 Created)

**Authorization:** Admin only
**Errors:** 
- 403 if user is not admin
- 422 if validation fails

---

#### `PUT /development/{feature_id}`

Update an existing feature.

**Path Parameters:**
- `feature_id` (integer) - Feature ID

**Request Body:** `UpdateFeatureRequest` (all fields optional)
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "status": "testing",
  "priority": "critical",
  "target_date": "2025-12-15"
}
```

**Response:** `FeatureDetailResponse`

**Authorization:** Admin only
**Errors:**
- 403 if user is not admin
- 404 if feature not found
- 400 if no fields to update

---

#### `DELETE /development/{feature_id}`

Delete a feature (and all its steps and comments).

**Path Parameters:**
- `feature_id` (integer) - Feature ID

**Response:**
```json
{
  "message": "Feature deleted successfully"
}
```

**Authorization:** Admin only
**Errors:**
- 403 if user is not admin
- 404 if feature not found

---

### Step Endpoints

#### `POST /development/{feature_id}/steps`

Add a step to a feature.

**Path Parameters:**
- `feature_id` (integer) - Feature ID

**Request Body:** `CreateStepRequest`
```json
{
  "title": "Create database schema",
  "description": "Add users and roles tables",
  "step_order": 0
}
```

**Response:** `StepResponse` (201 Created)

**Authorization:** Admin only
**Errors:**
- 403 if user is not admin
- 404 if feature not found

**Note:** If `step_order` is omitted, step is appended to the end.

---

#### `PUT /development/steps/{step_id}`

Update a step.

**Path Parameters:**
- `step_id` (integer) - Step ID

**Request Body:** `UpdateStepRequest` (all fields optional)
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "status": "done",
  "step_order": 1
}
```

**Response:** `StepResponse`

**Authorization:** Admin only
**Errors:**
- 403 if user is not admin
- 404 if step not found
- 400 if no fields to update

---

#### `DELETE /development/steps/{step_id}`

Delete a step.

**Path Parameters:**
- `step_id` (integer) - Step ID

**Response:**
```json
{
  "message": "Step deleted successfully"
}
```

**Authorization:** Admin only
**Errors:**
- 403 if user is not admin
- 404 if step not found

---

#### `POST /development/{feature_id}/steps/reorder`

Reorder steps for a feature.

**Path Parameters:**
- `feature_id` (integer) - Feature ID

**Request Body:** `ReorderStepsRequest`
```json
{
  "step_ids": [3, 1, 2]
}
```

**Response:** `List[StepResponse]`

**Authorization:** Admin only
**Errors:**
- 403 if user is not admin
- 404 if feature not found

**Note:** Step IDs should be in the desired display order.

---

### Comment Endpoints

#### `POST /development/{feature_id}/comments`

Add a comment to a feature.

**Path Parameters:**
- `feature_id` (integer) - Feature ID

**Request Body:** `CreateCommentRequest`
```json
{
  "comment": "Started work on database schema"
}
```

**Response:** `CommentResponse` (201 Created)

**Authorization:** Authenticated user (any role)
**Errors:**
- 404 if feature not found

---

#### `DELETE /development/comments/{comment_id}`

Delete a comment.

**Path Parameters:**
- `comment_id` (integer) - Comment ID

**Response:**
```json
{
  "message": "Comment deleted successfully"
}
```

**Authorization:** 
- Comment owner can delete their own comments
- Admin can delete any comment

**Errors:**
- 403 if user is neither owner nor admin
- 404 if comment not found

---

## Service Layer Logic

### File: `backend/app/services/development_service.py`

#### Function: `get_features_list()`

**Purpose:** Fetch paginated, filtered list of features

**Key Logic:**
1. Build WHERE clause from status/priority filters
2. Get total count for pagination
3. Fetch features with:
   - Left join to user_profiles for creator name
   - Left join to auth.users for creator email (v1.0.1 fix)
   - Subqueries for step counts and comment counts
4. Sort by priority (critical → low), then created_at DESC
5. Apply pagination (LIMIT/OFFSET)

**SQL Pattern:**
```sql
SELECT f.*, up.full_name, au.email,
       (SELECT COUNT(*) FROM feature_steps WHERE feature_id = f.id) as step_count,
       (SELECT COUNT(*) FROM feature_steps WHERE feature_id = f.id AND status = 'done') as completed_steps,
       (SELECT COUNT(*) FROM feature_comments WHERE feature_id = f.id) as comment_count
FROM features f
LEFT JOIN user_profiles up ON f.created_by_id = up.id
LEFT JOIN auth.users au ON au.id = up.id
WHERE status = $1 AND priority = $2
ORDER BY CASE priority ... END, created_at DESC
LIMIT $3 OFFSET $4
```

---

#### Function: `get_feature_by_id()`

**Purpose:** Fetch single feature with all steps and comments

**Key Logic:**
1. Fetch feature details with joins for user info
2. Fetch all steps ordered by step_order
3. Fetch all comments ordered by created_at ASC
4. Combine into single response object

**Returns:** 404 if feature not found

---

#### Function: `create_feature()`

**Purpose:** Create new feature

**Key Logic:**
1. Insert feature with provided data
2. created_by_id set to current user
3. Status defaults to 'planned'
4. Fetch and return complete feature details

**Returns:** Created feature with ID

---

#### Function: `update_feature()`

**Purpose:** Update feature fields

**Key Logic:**
1. Build dynamic UPDATE query based on provided fields
2. Only update non-None values (partial update support)
3. updated_at automatically set by trigger

**Validation:** At least one field must be provided

---

#### Function: `create_step()`

**Purpose:** Add step to feature

**Key Logic:**
1. Verify feature exists
2. If step_order not provided, get MAX(step_order) + 1
3. Insert step with default status 'todo'

**Returns:** Created step details

---

#### Function: `update_step()`

**Purpose:** Update step fields

**Key Logic:**
- Similar to update_feature, supports partial updates
- Can update title, description, status, step_order

---

#### Function: `reorder_steps()`

**Purpose:** Bulk reorder steps

**Key Logic:**
1. Use database transaction
2. Loop through step_ids array
3. Update step_order = array index for each step
4. Return all steps in new order

---

#### Function: `add_comment()`

**Purpose:** Add comment to feature

**Key Logic:**
1. Verify feature exists
2. Insert comment with current user ID
3. Fetch comment with user info joined (v1.0.1: from auth.users)

---

#### Function: `delete_comment()`

**Purpose:** Delete comment with permission check

**Key Logic:**
1. Fetch comment to check ownership
2. Verify user is either comment owner or admin
3. Delete if authorized

**Authorization:** Enforced at service layer

---

#### Function: `get_feature_stats()`

**Purpose:** Calculate statistics

**Key Logic:**
1. Single query with COUNT() FILTER for each status
2. Separate query for priority distribution (GROUP BY)
3. Query for step statistics (total and completed)

**Performance:** Uses indexes on status and priority columns

---

## Frontend Architecture

### File: `frontend/src/pages/DevelopmentModule.jsx`

#### Component Structure

```jsx
DevelopmentModule (Router)
├── FeaturesList
│   ├── Stats Cards (5 cards)
│   ├── Filter Section (status, priority)
│   ├── Features Table
│   │   ├── Progress bars
│   │   ├── Status/priority chips
│   │   └── Action buttons
│   ├── Pagination
│   └── Create Feature Dialog (admin only)
└── FeatureDetail
    ├── Header (title, status, priority, target date)
    ├── Description Card
    ├── Steps Card
    │   ├── Progress bar
    │   ├── Step checklist
    │   └── Add Step Dialog (admin only)
    ├── Comments Card
    │   ├── Comment list
    │   └── Add comment input
    └── Edit Feature Dialog (admin only)
```

#### State Management

**FeaturesList Component:**
```javascript
const [features, setFeatures] = useState([]);
const [loading, setLoading] = useState(true);
const [total, setTotal] = useState(0);
const [page, setPage] = useState(0);
const [rowsPerPage, setRowsPerPage] = useState(10);
const [stats, setStats] = useState(null);
const [statusFilter, setStatusFilter] = useState('');
const [priorityFilter, setPriorityFilter] = useState('');
const [createOpen, setCreateOpen] = useState(false);
const [newFeature, setNewFeature] = useState({...});
```

**FeatureDetail Component:**
```javascript
const [feature, setFeature] = useState(null);
const [loading, setLoading] = useState(true);
const [newComment, setNewComment] = useState('');
const [submitting, setSubmitting] = useState(false);
const [stepDialog, setStepDialog] = useState(false);
const [editDialog, setEditDialog] = useState(false);
```

#### API Integration

**File:** `frontend/src/api/index.js`

```javascript
export const developmentAPI = {
  getFeatures: async (params) => {
    const response = await apiClient.get('/development', { params });
    return response.data;
  },
  getFeatureStats: async () => { ... },
  getFeature: async (featureId) => { ... },
  createFeature: async (data) => { ... },
  updateFeature: async (featureId, data) => { ... },
  deleteFeature: async (featureId) => { ... },
  createStep: async (featureId, data) => { ... },
  updateStep: async (stepId, data) => { ... },
  deleteStep: async (stepId) => { ... },
  addComment: async (featureId, data) => { ... },
  deleteComment: async (commentId) => { ... },
};
```

#### Key Functions

**Fetch Features:**
```javascript
const fetchFeatures = async () => {
  setLoading(true);
  try {
    const params = {
      page: page + 1,  // API uses 1-based pages
      limit: rowsPerPage,
    };
    if (statusFilter) params.status = statusFilter;
    if (priorityFilter) params.priority = priorityFilter;
    
    const data = await developmentAPI.getFeatures(params);
    setFeatures(data.features || []);
    setTotal(data.total || 0);
  } catch (error) {
    enqueueSnackbar('Failed to fetch features', { variant: 'error' });
  } finally {
    setLoading(false);
  }
};
```

**Toggle Step:**
```javascript
const handleToggleStep = async (step) => {
  const newStatus = step.status === 'done' ? 'todo' : 'done';
  try {
    await developmentAPI.updateStep(step.id, { status: newStatus });
    fetchFeature();  // Refresh to update progress
  } catch (error) {
    enqueueSnackbar('Failed to update step', { variant: 'error' });
  }
};
```

---

## Data Flow Diagrams

### Creating a Feature

```
User (Admin) → Frontend → Backend → Database
     |             |           |         |
     |  Clicks     |  POST     | INSERT  |
     |  "Create"   |  /api/v1/ |  INTO   |
     |             |  develop  | features|
     |             |  ment     |         |
     |             |           |         |
     |  ← Form  ← |  ← 201 ← |  ← ID  ←|
     |    displays|    Created|         |
     |    feature |    +data  |         |
```

### Updating Step Status

```
Admin → Frontend → Backend → Database
  |        |          |          |
  | Click  | PUT      | UPDATE   |
  | check  | /steps/  | feature  |
  | box    | {id}     | _steps   |
  |        |          | SET      |
  |        |          | status   |
  |        |          |          |
  | ← UI  | ← 200 ← | ← trigger|
  |  updates|   OK    |  updates |
  |  progress|        |  updated |
  |  bar   |          |  _at     |
```

---

## Security & Permissions

### Authentication

- All endpoints require valid JWT token
- Token passed in `Authorization: Bearer <token>` header
- Token validated by `get_current_user` dependency

### Authorization

**Admin-Only Actions:**
- Create features
- Update features
- Delete features
- Create steps
- Update steps
- Delete steps
- Reorder steps
- Delete any comment

**All Authenticated Users:**
- View features
- View statistics
- Add comments
- Delete own comments

**Authorization Implementation:**

```python
# In routes/development.py
@router.post("", response_model=FeatureDetailResponse)
async def create_feature(
    request: CreateFeatureRequest,
    admin: CurrentUser = Depends(require_admin),  # Admin only
):
    return await development_service.create_feature(request, admin.id)

@router.get("", response_model=FeaturesListResponse)
async def list_features(
    current_user: CurrentUser = Depends(get_current_user),  # Any user
):
    return await development_service.get_features_list(...)
```

### Data Validation

**Backend Validation (Pydantic):**
- Title: 1-200 characters
- Status: Must be valid enum value
- Priority: Must be valid enum value
- Feature ID: Must be positive integer
- All required fields enforced

**Frontend Validation:**
- Empty title check
- Form state validation
- User role checks before showing admin controls

### SQL Injection Prevention

- All queries use parameterized queries ($1, $2, etc.)
- No string concatenation of user input
- asyncpg library handles escaping

---

## Testing

### Unit Tests

**Recommended test coverage:**

```python
# test_development_service.py

async def test_create_feature():
    """Test creating a feature returns correct data"""
    
async def test_get_features_filters():
    """Test status and priority filters work"""
    
async def test_update_step_status():
    """Test step status can be updated"""
    
async def test_delete_comment_permissions():
    """Test users can only delete own comments"""
```

### Integration Tests

```python
# test_development_api.py

async def test_feature_lifecycle():
    """Test complete workflow: create → add steps → complete → delete"""
    
async def test_multi_user_comments():
    """Test multiple users can comment on same feature"""
```

### Frontend Tests

```javascript
// DevelopmentModule.test.jsx

test('renders features list', async () => { ... });
test('filters by status', async () => { ... });
test('admin can create feature', async () => { ... });
test('regular user cannot create feature', async () => { ... });
```

---

## Deployment

### Database Migration

**Production deployment checklist:**

1. **Backup database:**
   ```bash
   pg_dump -U postgres -d production_db > backup.sql
   ```

2. **Run migration:**
   ```bash
   cd backend
   python run_development_migration.py
   ```

3. **Verify tables:**
   ```sql
   \dt *feature*
   SELECT * FROM modules WHERE module_key = 'development';
   ```

4. **Grant permissions:**
   ```sql
   GRANT SELECT, INSERT, UPDATE, DELETE ON features TO app_user;
   GRANT SELECT, INSERT, UPDATE, DELETE ON feature_steps TO app_user;
   GRANT SELECT, INSERT, UPDATE, DELETE ON feature_comments TO app_user;
   ```

### Environment Variables

No additional environment variables required. Uses existing:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ALLOWED_ORIGINS`

### Monitoring

**Key metrics to monitor:**

- Feature creation rate
- Average steps per feature
- Comment activity
- Feature completion time
- API response times for `/development` endpoint
- Database query performance on features table

---

## Performance Considerations

### Database Optimization

**Indexes:**
- `features(status)` - For status filter
- `features(priority)` - For priority filter
- `features(created_at DESC)` - For sorting
- `feature_steps(feature_id, step_order)` - For step retrieval
- `feature_comments(feature_id)` - For comment retrieval

**Query Optimization:**
- Subqueries for counts (step_count, completed_steps, comment_count) are indexed
- Pagination limits result set size
- Filters reduce result set before sorting

### API Performance

**Pagination:**
- Default: 50 items per page
- Maximum: 100 items per page
- Prevents large result sets

**Caching Opportunities:**
- Statistics endpoint (`/stats`) - can be cached for 5 minutes
- Feature list with no filters - can be cached briefly

### Frontend Performance

**Optimizations:**
- Lazy loading of feature details (only when clicked)
- Debounced filter changes
- Pagination reduces DOM elements
- Material-UI components are optimized

---

## Error Handling

### Backend Error Codes

- `400` - Bad request (validation error, missing fields)
- `403` - Forbidden (not admin, not comment owner)
- `404` - Not found (feature, step, or comment doesn't exist)
- `422` - Unprocessable entity (Pydantic validation failed)
- `500` - Internal server error (database error, unexpected exception)

### Frontend Error Handling

```javascript
try {
  const data = await developmentAPI.getFeatures(params);
  setFeatures(data.features);
} catch (error) {
  if (error.response?.status === 403) {
    enqueueSnackbar('Permission denied', { variant: 'error' });
  } else {
    enqueueSnackbar('Failed to fetch features', { variant: 'error' });
  }
}
```

---

## Future Enhancements

### Planned Features

1. **File Attachments** - Attach files/screenshots to features
2. **@Mentions** - Mention users in comments with notifications
3. **Email Notifications** - Notify on status changes, mentions
4. **Advanced Search** - Full-text search on titles and descriptions
5. **Tags/Labels** - Categorize features with custom tags
6. **Time Tracking** - Track time spent on features
7. **Dependencies** - Link features that depend on each other
8. **Milestones** - Group features into release milestones
9. **Export** - Export features to CSV, JSON, or PDF

### Technical Debt

- Add drag-and-drop for step reordering (frontend)
- Implement optimistic UI updates
- Add WebSocket support for real-time updates
- Improve test coverage to 90%+
- Add API rate limiting
- Implement audit logging

---

**Document Version:** 1.0.1
**Last Updated:** 2025-11-20
**Maintainer:** Development Team
