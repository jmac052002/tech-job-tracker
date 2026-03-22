from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models.job_application import JobApplication
from backend.models.user import User
from backend.models.schemas import (
    JobApplicationCreate,
    JobApplicationUpdate,
    JobApplicationResponse
)
from backend.utils.dependencies import get_current_user

# Create a router — this groups related routes together
# prefix="/api/jobs" means all routes here start with /api/jobs
# tags=["jobs"] groups these routes in the auto-generated API docs
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# CREATE — Add a new job application
# POST /api/jobs
# Request body: JobApplicationCreate schema (validated by Pydantic)
# Response: JobApplicationResponse schema (includes the new ID)
# PROTECTED: Requires valid JWT token (current_user dependency)
@router.post("", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job_application(
    job: JobApplicationCreate,  # Pydantic validates this automatically
    current_user: User = Depends(get_current_user),  # SECURITY: Validate JWT token
    db: Session = Depends(get_db)  # Dependency injection — FastAPI provides a DB session
):
    """
    Create a new job application for the authenticated user.

    Security note:
    --------------
    - Requires Authorization: Bearer <token> header
    - Automatically sets user_id to current authenticated user
    - Users can only create jobs for themselves (can't impersonate others)

    Why set user_id server-side?
    -----------------------------
    - Client could send any user_id in request body (security vulnerability)
    - Example attack: User A sends user_id=2 to create job for User B
    - Prevention: Always set user_id = current_user.id (ignore client input)
    - This is called "trusting the authentication, not the request"
    """
    # Convert Pydantic model to SQLAlchemy model
    # .model_dump() converts Pydantic object to a dictionary
    db_job = JobApplication(**job.model_dump())

    # SECURITY: Set user_id to authenticated user (ignore any client-provided user_id)
    # This prevents users from creating jobs for other users
    db_job.user_id = current_user.id

    # Add to database session and commit
    db.add(db_job)  # Stages the new record
    db.commit()  # Saves to database
    db.refresh(db_job)  # Refreshes the object to get the auto-generated ID

    return db_job  # FastAPI automatically converts to JSON using JobApplicationResponse


# READ ALL — Get all job applications for current user
# GET /api/jobs
# Response: List of JobApplicationResponse (only user's own jobs)
# PROTECTED: Requires valid JWT token
@router.get("", response_model=List[JobApplicationResponse])
def get_all_job_applications(
    current_user: User = Depends(get_current_user),  # SECURITY: Validate JWT token
    db: Session = Depends(get_db)
):
    """
    Get all job applications for the authenticated user.

    Security note - Data Isolation:
    --------------------------------
    - MUST filter by user_id to prevent data leaks
    - Without filter: User A could see User B's job applications
    - This is called IDOR (Insecure Direct Object Reference) vulnerability

    Example attack (prevented):
    - User A authenticates, gets token
    - User A calls GET /api/jobs
    - Without filter: Returns all jobs from all users (data breach!)
    - With filter: Returns only User A's jobs (secure)

    Why this matters:
    -----------------
    - Job applications contain sensitive data (company names, dates, notes)
    - Privacy violation if users can see each other's job searches
    - Regulatory compliance (GDPR, CCPA) requires data isolation

    Future enhancements:
    --------------------
    - Add pagination (limit, offset) for large job lists
    - Add filtering (status="interviewing", company="Google")
    - Add sorting (date_applied DESC, company ASC)
    """
    # SECURITY: Filter by current user's ID
    # Only return jobs that belong to the authenticated user
    jobs = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()

    return jobs  # FastAPI converts the list to JSON


# READ ONE — Get a single job application by ID (only if user owns it)
# GET /api/jobs/{job_id}
# Path parameter: job_id (extracted from URL)
# Response: JobApplicationResponse or 404 error
# PROTECTED: Requires valid JWT token
@router.get("/{job_id}", response_model=JobApplicationResponse)
def get_job_application(
    job_id: int,  # FastAPI extracts this from the URL path
    current_user: User = Depends(get_current_user),  # SECURITY: Validate JWT token
    db: Session = Depends(get_db)
):
    """
    Get a specific job application by ID (only if current user owns it).

    Security note - IDOR Prevention:
    ---------------------------------
    IDOR = Insecure Direct Object Reference

    Attack scenario (prevented by user_id check):
    1. User A creates Job #5 (user_id=1)
    2. User B creates Job #6 (user_id=2)
    3. User A tries: GET /api/jobs/6
    4. Without user_id check: Returns Job #6 (data leak!)
    5. With user_id check: Returns 404 (secure)

    Why return 404 instead of 403?
    -------------------------------
    - 404 Not Found: Resource doesn't exist (or user doesn't own it)
    - 403 Forbidden: Resource exists but user lacks permission

    Returning 404 for both cases prevents information leakage:
    - Attacker can't tell if job_id exists or not
    - Prevents enumeration (guessing valid job IDs)
    - Better privacy (doesn't reveal other users' job IDs)

    Example:
    - User A: GET /api/jobs/999 → 404 (doesn't exist)
    - User A: GET /api/jobs/6 → 404 (exists but belongs to User B)
    - Attacker can't distinguish between these cases
    """
    # SECURITY: Query for job by BOTH id AND user_id
    # This ensures user can only access their own jobs
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id  # CRITICAL: Ownership check
    ).first()

    # If not found OR user doesn't own it, return 404
    # Don't reveal whether job exists or user just doesn't own it
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job application with id {job_id} not found"
        )

    return job


# UPDATE — Update an existing job application (only if user owns it)
# PUT /api/jobs/{job_id}
# Path parameter: job_id
# Request body: JobApplicationUpdate (all fields optional)
# Response: Updated JobApplicationResponse or 404 error
# PROTECTED: Requires valid JWT token
@router.put("/{job_id}", response_model=JobApplicationResponse)
def update_job_application(
    job_id: int,
    job_update: JobApplicationUpdate,  # Pydantic validates this
    current_user: User = Depends(get_current_user),  # SECURITY: Validate JWT token
    db: Session = Depends(get_db)
):
    """
    Update a job application (only if current user owns it).

    Security note - Preventing Unauthorized Modifications:
    ------------------------------------------------------
    Without user_id check:
    - User A could modify User B's jobs (integrity violation)
    - Example: User A: PUT /api/jobs/6 {"status": "rejected"}
    - If job #6 belongs to User B, this would modify their data!

    With user_id check:
    - User A can only modify their own jobs
    - Attempt to modify others' jobs returns 404

    Why this matters:
    -----------------
    - Prevents malicious users from sabotaging others' job tracking
    - Prevents accidental modifications (typo in job_id)
    - Ensures data integrity (users own their data)

    Additional security:
    --------------------
    - Can't change user_id via update (ownership is immutable)
    - Even if client sends "user_id": 2 in request, it's ignored
    - user_id is set at creation time and never changed
    """
    # SECURITY: Find job by BOTH id AND user_id
    # Ensures user can only update their own jobs
    db_job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id  # CRITICAL: Ownership check
    ).first()

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


# DELETE — Delete a job application (only if user owns it)
# DELETE /api/jobs/{job_id}
# Path parameter: job_id
# Response: 204 No Content (success) or 404 error
# PROTECTED: Requires valid JWT token
@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_application(
    job_id: int,
    current_user: User = Depends(get_current_user),  # SECURITY: Validate JWT token
    db: Session = Depends(get_db)
):
    """
    Delete a job application (only if current user owns it).

    Security note - Preventing Unauthorized Deletions:
    --------------------------------------------------
    Without user_id check:
    - User A could delete User B's jobs (destructive attack)
    - Example: User A: DELETE /api/jobs/6
    - If job #6 belongs to User B, their data is lost!

    With user_id check:
    - User A can only delete their own jobs
    - Attempt to delete others' jobs returns 404

    Why this is especially critical:
    ---------------------------------
    - DELETE is irreversible (no undo)
    - Loss of data is permanent (unless you have backups)
    - Malicious user could wipe others' job tracking history
    - Prevents both intentional attacks and accidental deletions

    Production consideration:
    -------------------------
    - Consider soft delete (is_deleted flag) instead of hard delete
    - Allows data recovery if user changes mind
    - Useful for audit trails (who deleted what when)
    - Example: deleted_at timestamp instead of DELETE query
    """
    # SECURITY: Find job by BOTH id AND user_id
    # Ensures user can only delete their own jobs
    db_job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id  # CRITICAL: Ownership check
    ).first()

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
