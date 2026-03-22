from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models.job_application import JobApplication
from backend.models.schemas import (
    JobApplicationCreate,
    JobApplicationUpdate,
    JobApplicationResponse
)

# Create a router — this groups related routes together
# prefix="/api/jobs" means all routes here start with /api/jobs
# tags=["jobs"] groups these routes in the auto-generated API docs
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# CREATE — Add a new job application
# POST /api/jobs
# Request body: JobApplicationCreate schema (validated by Pydantic)
# Response: JobApplicationResponse schema (includes the new ID)
@router.post("", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job_application(
    job: JobApplicationCreate,  # Pydantic validates this automatically
    db: Session = Depends(get_db)  # Dependency injection — FastAPI provides a DB session
):
    # Convert Pydantic model to SQLAlchemy model
    # .model_dump() converts Pydantic object to a dictionary
    db_job = JobApplication(**job.model_dump())

    # Add to database session and commit
    db.add(db_job)  # Stages the new record
    db.commit()  # Saves to database
    db.refresh(db_job)  # Refreshes the object to get the auto-generated ID

    return db_job  # FastAPI automatically converts to JSON using JobApplicationResponse


# READ ALL — Get all job applications
# GET /api/jobs
# Optional query params could be added later (filtering, pagination, etc.)
# Response: List of JobApplicationResponse
@router.get("", response_model=List[JobApplicationResponse])
def get_all_job_applications(
    db: Session = Depends(get_db)
):
    # Query all job applications from the database
    jobs = db.query(JobApplication).all()
    return jobs  # FastAPI converts the list to JSON


# READ ONE — Get a single job application by ID
# GET /api/jobs/{job_id}
# Path parameter: job_id (extracted from URL)
# Response: JobApplicationResponse or 404 error
@router.get("/{job_id}", response_model=JobApplicationResponse)
def get_job_application(
    job_id: int,  # FastAPI extracts this from the URL path
    db: Session = Depends(get_db)
):
    # Query for a specific job by ID
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()

    # If not found, return 404 error
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {job_id} not found"
        )

    return job


# UPDATE — Update an existing job application
# PUT /api/jobs/{job_id}
# Path parameter: job_id
# Request body: JobApplicationUpdate (all fields optional)
# Response: Updated JobApplicationResponse or 404 error
@router.put("/{job_id}", response_model=JobApplicationResponse)
def update_job_application(
    job_id: int,
    job_update: JobApplicationUpdate,  # Pydantic validates this
    db: Session = Depends(get_db)
):
    # Find the existing job
    db_job = db.query(JobApplication).filter(JobApplication.id == job_id).first()

    if db_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {job_id} not found"
        )

    # Update only the fields that were provided
    # exclude_unset=True means only update fields that were actually sent
    # This allows partial updates (e.g., only changing status)
    update_data = job_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_job, field, value)  # Updates the SQLAlchemy object

    db.commit()  # Save changes to database
    db.refresh(db_job)  # Refresh to get the updated state

    return db_job


# DELETE — Delete a job application
# DELETE /api/jobs/{job_id}
# Path parameter: job_id
# Response: 204 No Content (success) or 404 error
@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_application(
    job_id: int,
    db: Session = Depends(get_db)
):
    # Find the job to delete
    db_job = db.query(JobApplication).filter(JobApplication.id == job_id).first()

    if db_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {job_id} not found"
        )

    # Delete from database
    db.delete(db_job)
    db.commit()

    # 204 No Content — successful deletion, no response body needed
    return None
