# FastAPI Backend Setup Plan

## Overview
Setting up a FastAPI backend with SQLAlchemy ORM, SQLite database, and CRUD operations for job application tracking.

## Implementation Steps

### 1. Create requirements.txt
**File:** `backend/requirements.txt`

**Packages needed:**
- `fastapi` — the web framework itself
- `uvicorn[standard]` — ASGI server to run FastAPI (with extra performance dependencies)
- `sqlalchemy` — ORM (Object-Relational Mapping) for database interactions
- `pydantic` — data validation (comes with FastAPI but explicit for clarity)
- `python-dotenv` — loads environment variables from `.env` files

**Why these choices:**
- FastAPI requires an ASGI server (uvicorn) to run
- SQLAlchemy is the standard Python ORM — provides a Pythonic way to interact with databases without writing raw SQL
- Pydantic is FastAPI's validation layer — ensures data coming in/out matches expected types
- python-dotenv loads environment variables from `.env` — keeps secrets out of code

---

### 2. Create .env and .env.example files
**Files:** `.env` (not committed) and `.env.example` (safe to commit)

**Purpose:** Store configuration like database URLs outside of code

**.env contents:**
```
DATABASE_URL=sqlite:///./jobs.db
```

**.env.example contents:**
```
DATABASE_URL=sqlite:///./jobs.db
```

**Why this approach:**
- `.env` contains actual values (never committed to git)
- `.env.example` shows what variables are needed with safe placeholder values
- Makes switching to PostgreSQL later as simple as changing the `DATABASE_URL`
- Follows 12-factor app methodology (config in environment, not code)

**Security benefit:**
- When you deploy to production, you'll have database credentials
- Those credentials should NEVER be in your code or git history
- Environment variables keep them separate and secure

**For AWS migration:**
- When you move to RDS PostgreSQL, you'll just change `DATABASE_URL` to:
  ```
  DATABASE_URL=postgresql://user:password@rds-endpoint:5432/dbname
  ```
- SQLAlchemy works with both SQLite and PostgreSQL — no code changes needed

---

### 3. Create database.py
**File:** `backend/database.py`

**Purpose:** Single source of truth for database connection and session management

**Components:**
1. **Load environment variables** — `load_dotenv()` reads `.env` file
2. **SQLALCHEMY_DATABASE_URL** — Read from `os.getenv("DATABASE_URL")`
3. **engine** — SQLAlchemy engine that manages connections to the database
4. **SessionLocal** — factory for creating database sessions (each request gets its own session)
5. **Base** — declarative base class that all models inherit from
6. **get_db()** — dependency function that provides a database session to route handlers

**Why structured this way:**
- Separating DB config from business logic follows separation of concerns
- Reading from environment variables means no hardcoded database URLs
- `get_db()` ensures each API request gets its own DB session and it's properly closed after
- Using a dependency injection pattern (FastAPI's `Depends`) makes testing easier

**Environment variable approach:**
- The database URL is never hardcoded in Python files
- Same code works in development (SQLite) and production (PostgreSQL)
- Just change the `.env` file — no code changes required

---

### 4. Create JobApplication model
**File:** `backend/models/job_application.py`

**Purpose:** Define the database table schema using SQLAlchemy ORM

**Fields:**
- `id` — Integer, primary key, auto-incremented
- `company` — String, required
- `position` — String, required
- `status` — String (e.g., "applied", "interviewing", "rejected", "offer")
- `date_applied` — Date, when you submitted the application
- `notes` — Text, optional longer notes
- `follow_up_date` — Date, optional reminder date

**Why SQLAlchemy models:**
- They map Python classes to database tables automatically
- Provide type safety and validation at the ORM level
- Make migrations easier when you need to change schema later

---

### 5. Create Pydantic schemas
**File:** `backend/models/schemas.py`

**Purpose:** Define the shape of data coming in (requests) and going out (responses) from the API

**Schemas needed:**
1. **JobApplicationBase** — shared fields (company, position, status, etc.)
2. **JobApplicationCreate** — for POST requests (excludes `id`)
3. **JobApplicationUpdate** — for PUT/PATCH requests (all fields optional)
4. **JobApplicationResponse** — for responses (includes `id`, matches DB model)

**Why separate from SQLAlchemy models:**
- SQLAlchemy models = database representation
- Pydantic models = API contract (what clients send/receive)
- This separation lets you control what's exposed via API vs what's stored in DB
- Security: prevents clients from manipulating fields they shouldn't (like `id` on creation)

---

### 6. Create CRUD operations
**File:** `backend/routes/job_applications.py`

**Purpose:** API endpoints for Create, Read, Update, Delete operations

**Endpoints:**
- `POST /api/jobs` — create new job application
- `GET /api/jobs` — list all job applications
- `GET /api/jobs/{id}` — get single job application by ID
- `PUT /api/jobs/{id}` — update existing job application
- `DELETE /api/jobs/{id}` — delete job application

**Why separate routes file:**
- Keeps `main.py` clean and focused on app initialization
- Makes the codebase easier to navigate as it grows
- Each route uses dependency injection (`Depends(get_db)`) to get a DB session

**Design pattern:**
- Route handlers stay thin — they just parse requests and call business logic
- For now, logic is simple enough to live in routes
- As complexity grows, we'll extract to a `services/` layer

---

### 7. Create main.py (FastAPI app entry point)
**File:** `backend/main.py`

**Purpose:** Initialize FastAPI app, configure CORS, mount routes, create DB tables

**Components:**
1. **FastAPI app instance** — the application object
2. **CORS middleware** — allows frontend (mobile app) to call the API from different origin
3. **Database table creation** — `Base.metadata.create_all(bind=engine)` on startup
4. **Router inclusion** — mounts the job application routes under `/api` prefix

**Why CORS is needed:**
- Your React Native app will run on a different port/origin than the API
- Without CORS headers, browsers/apps block cross-origin requests
- For dev, we'll allow all origins (`*`); in production, lock this down to specific domains

**Why create tables on startup:**
- For SQLite in development, this is convenient — tables auto-create if they don't exist
- For production (PostgreSQL), you'd use a proper migration tool like Alembic
- This approach works for now, but we'll revisit for production

---

## Files to Create

```
.env                             # ✅ Environment variables (NOT committed)
.env.example                     # ✅ Template for .env (safe to commit)
backend/
├── main.py                      # ✅ FastAPI app entry point
├── database.py                  # ✅ Database connection and session
├── requirements.txt             # ✅ Python dependencies
├── models/
│   ├── __init__.py              # ✅ Makes it a Python package
│   ├── job_application.py       # ✅ SQLAlchemy model
│   └── schemas.py               # ✅ Pydantic request/response models
└── routes/
    ├── __init__.py              # ✅ Makes it a Python package
    └── job_applications.py      # ✅ CRUD route handlers
```

---

## Security & Best Practices Considerations

### 1. **SQL Injection Protection**
- SQLAlchemy ORM automatically parameterizes queries — no raw SQL concatenation
- This protects against SQL injection by default

### 2. **Input Validation**
- Pydantic schemas validate all incoming data before it reaches the database
- Type mismatches, missing required fields, etc. are caught automatically

### 3. **Database Session Management**
- Each request gets its own session via `get_db()` dependency
- Sessions are closed in a `finally` block — prevents connection leaks

### 4. **CORS Configuration**
- For development: `allow_origins=["*"]` (permissive)
- For production: lock down to specific frontend URL
- This prevents unauthorized websites from calling your API

### 5. **Error Handling**
- FastAPI automatically returns proper HTTP status codes
- 404 when resource not found, 422 for validation errors, etc.

### 6. **Environment Variables**
- ✅ Using `.env` files from the start — this is the right approach
- Never commit `.env` to git (should be in `.gitignore`)
- Production environments (AWS Lambda, EC2, etc.) will use actual environment variables, not `.env` files

### 7. **Future Considerations (flagged for AWS migration):**
- **Connection pooling:** SQLite doesn't need it, but PostgreSQL will
- **Migration tool:** Alembic for schema changes in production
- **Authentication:** Not implemented yet — when we add it, consider JWT or AWS Cognito
- **Database URL:** Already set up for easy PostgreSQL migration ✅

---

## Testing the API

After implementation, you can test with:

```bash
# Start the server
source venv/bin/activate
uvicorn backend.main:app --reload

# API will be available at http://localhost:8000
# Auto-generated docs at http://localhost:8000/docs (Swagger UI)
# Alternative docs at http://localhost:8000/redoc
```

FastAPI automatically generates interactive API documentation — you can test all endpoints directly in the browser.

---

## Next Steps After This Plan

1. Implement all the files in order (.env → requirements → database → models → routes → main)
2. Explain each file's purpose as we build it
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Run the server and test the API docs
5. Test CRUD operations to ensure everything works

---

## .gitignore Check

Make sure `.env` is in `.gitignore` so it's never committed:
```
.env
venv/
__pycache__/
*.pyc
*.db
```

---

## Why This Approach is Better

**Your suggestion to use environment variables from the start is excellent because:**

1. **No refactoring later** — when you switch to PostgreSQL/RDS, you just change `.env`
2. **Security best practice** — credentials never touch your code or git history
3. **Follows 12-factor app** — industry standard for building cloud-native apps
4. **Easy deployment** — same code runs everywhere, configuration is external
5. **No hardcoded URLs** — makes testing with different databases trivial

This is the professional way to build it. Good instinct!

---

## Ready to Implement?

Updated plan includes:
- ✅ `.env` and `.env.example` files
- ✅ `python-dotenv` in requirements.txt
- ✅ `database.py` reads `DATABASE_URL` from environment

Let me know when you're ready and I'll implement all the files with explanations for each!
