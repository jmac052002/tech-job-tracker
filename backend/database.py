import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
# check_same_thread=False is needed only for SQLite
# It allows multiple threads to use the same connection
# This is safe in FastAPI because each request gets its own session
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal is a factory for creating database sessions
# Each request will get its own session instance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
# All SQLAlchemy models will inherit from this
Base = declarative_base()

# Dependency function that provides a database session to route handlers
# This ensures each request gets its own session and it's properly closed
def get_db():
    db = SessionLocal()
    try:
        yield db  # FastAPI will inject this session into route handlers
    finally:
        db.close()  # Always close the session, even if an error occurs
