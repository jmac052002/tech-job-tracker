from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Pydantic models define the "shape" of data in API requests/responses
# These are separate from SQLAlchemy models (database structure)
# Why? To control what data is exposed via the API vs what's in the database

# Base schema — shared fields that all schemas inherit
# This follows DRY (Don't Repeat Yourself) principle
class JobApplicationBase(BaseModel):
    company: str = Field(..., min_length=1, description="Company name (required)")
    position: str = Field(..., min_length=1, description="Job position title (required)")
    status: str = Field(..., description="Application status (e.g., applied, interviewing, rejected, offer)")
    date_applied: date = Field(..., description="Date the application was submitted")
    notes: Optional[str] = Field(None, description="Optional notes about the application")
    follow_up_date: Optional[date] = Field(None, description="Optional follow-up reminder date")


# Schema for creating a new job application (POST request)
# Inherits all fields from JobApplicationBase
# Does NOT include 'id' because the database auto-generates it
class JobApplicationCreate(JobApplicationBase):
    pass  # Inherits everything from Base, nothing extra needed


# Schema for updating an existing job application (PUT/PATCH request)
# All fields are optional because you might only update one field
# Example: You might only want to update the status from "applied" to "interviewing"
class JobApplicationUpdate(BaseModel):
    company: Optional[str] = Field(None, min_length=1)
    position: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    date_applied: Optional[date] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None


# Schema for API responses (what gets returned to the client)
# Includes the 'id' field because existing records have an ID
# The Config class tells Pydantic to work with SQLAlchemy models
class JobApplicationResponse(JobApplicationBase):
    id: int

    class Config:
        # This allows Pydantic to read data from SQLAlchemy model attributes
        # Without this, you'd get errors when trying to convert a SQLAlchemy object to JSON
        from_attributes = True  # Pydantic v2 syntax (was orm_mode in v1)
