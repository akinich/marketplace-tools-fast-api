# Marketplace ERP - Quick Start Guide

**Version: 1.0.0** | **Last Updated: 2025-11-17**

This is a quick start guide for developers. For comprehensive deployment instructions with Render and Supabase, see [README.md](README.md).

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL database (or Supabase account)
- Git

## Quick Setup (Local Development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd farm2-app-fast-api
```

### 2. Database Setup

**Option A: Using Supabase (Recommended)**
1. Create a Supabase project at https://supabase.com
2. Copy `sql_scripts/v1.0.0_initial_schema.sql`
3. Paste into Supabase SQL Editor and run
4. Get your DATABASE_URL from Project Settings → Database

**Option B: Local PostgreSQL**
```bash
# Create database
createdb farm_management

# Run schema script
psql farm_management < sql_scripts/v1.0.0_initial_schema.sql
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and JWT secret
```

**Required .env variables:**
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/farm_management
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
JWT_REFRESH_SECRET_KEY=your-super-secret-refresh-key
ALLOWED_ORIGINS=http://localhost:3000
```

**Start backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

Backend will be available at http://localhost:8000

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env if needed (default backend URL is http://localhost:8000)
```

**Start frontend:**
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

### 5. Create First Admin User

**If using Supabase:**
1. Go to Authentication → Users → Add User
2. Create user with email/password
3. Copy the User UID
4. Run this SQL in SQL Editor:
   ```sql
   INSERT INTO user_profiles (id, email, full_name, role_id, is_active)
   VALUES ('USER_UID_HERE', 'admin@example.com', 'Admin User', 1, TRUE);
   ```

**If using local PostgreSQL:**
```sql
-- Insert into auth.users (simulate Supabase auth)
INSERT INTO auth.users (id, email)
VALUES (gen_random_uuid(), 'admin@example.com');

-- Create user profile
INSERT INTO user_profiles (id, email, full_name, role_id, is_active)
SELECT id, email, 'Admin User', 1, TRUE
FROM auth.users
WHERE email = 'admin@example.com';
```

### 6. Login and Start Using

1. Open http://localhost:3000
2. Login with your admin credentials
3. Navigate through:
   - Dashboard - View KPIs
   - Admin Panel - Manage users
   - Inventory - Manage items and stock

## API Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
farm2-app-fast-api/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── schemas/     # Pydantic models
│   │   └── auth/        # Authentication
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # React frontend
│   ├── src/
│   │   ├── api/        # API client
│   │   ├── pages/      # Page components
│   │   ├── components/ # Reusable components
│   │   └── store/      # State management
│   ├── package.json
│   └── .env.example
└── sql_scripts/         # Database schemas
    └── v1.0.0_initial_schema.sql
```

## Common Issues

### CORS Errors
- Make sure `ALLOWED_ORIGINS` in backend `.env` includes frontend URL
- Default: `http://localhost:3000`

### Database Connection Failed
- Check DATABASE_URL format
- For Supabase: Use "Transaction" pooler URL for better performance
- For local: Ensure PostgreSQL is running

### Frontend Can't Connect to Backend
- Ensure backend is running on port 8000
- Check `VITE_API_BASE_URL` in frontend `.env`

### 401 Unauthorized
- Token might be expired, logout and login again
- Check if user profile exists in database

## Development Workflow

### Making Changes

1. **Backend changes:**
   - Edit files in `backend/app/`
   - FastAPI auto-reloads with `--reload` flag
   - Check http://localhost:8000/docs for API changes

2. **Frontend changes:**
   - Edit files in `frontend/src/`
   - Vite hot-reloads automatically
   - Check browser console for errors

### Testing

**Backend:**
```bash
# Run tests (when implemented)
cd backend
pytest
```

**Frontend:**
```bash
# Lint code
cd frontend
npm run lint
```

### Database Migrations

When making schema changes:
1. Create new SQL file: `sql_scripts/vX.X.X_description.sql`
2. Add version header with changelog
3. Run script on your database
4. Update version in code

## Next Steps

- Read [README.md](README.md) for deployment to production
- Check individual component READMEs:
  - [Backend README](backend/README.md)
  - [Frontend README](frontend/README.md)
- Review API documentation at `/docs`
- Customize theme in `frontend/src/theme/theme.js`

## Need Help?

- Check the comprehensive [README.md](README.md)
- Review API docs at http://localhost:8000/docs
- Check database schema in `sql_scripts/`

## Changelog

### v1.0.0 (2025-11-17)
- Initial quick start guide
- Local development setup instructions
- Common troubleshooting tips
