from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend.routes import job_applications

# Create all database tables
# This runs once when the app starts
# If tables already exist, it does nothing
# For production, you'd use a migration tool like Alembic instead
Base.metadata.create_all(bind=engine)

# Create FastAPI app instance
app = FastAPI(
    title="Tech Job Tracker API",
    description="API for tracking job applications during the job hunt",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your React Native app to call the API from a different origin
# Origins: List of allowed domains that can call this API
# Credentials: Allow cookies/auth headers
# Methods: Which HTTP methods are allowed
# Headers: Which headers clients can send
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development — allows all origins
    # For production, lock this down to specific domains:
    # allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include routers
# This mounts all the job application routes under /api/jobs
app.include_router(job_applications.router)


# Root endpoint — just a health check
@app.get("/")
def read_root():
    return {
        "message": "Tech Job Tracker API",
        "status": "running",
        "docs": "/docs",  # Link to auto-generated interactive API docs
        "redoc": "/redoc"  # Link to alternative API documentation
    }


# You can add more routers here as you build other features
# Example future routes:
# from backend.routes import users, analytics
# app.include_router(users.router)
# app.include_router(analytics.router)
