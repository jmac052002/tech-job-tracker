from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# SQLAlchemy model — represents the database table structure
# This is the "source of truth" for what gets stored in the database
class JobApplication(Base):
    __tablename__ = "job_applications"  # Table name in the database

    # Primary key — auto-incremented ID
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to users table — each job belongs to one user
    # ForeignKey('users.id'): References the id column in users table
    # nullable=False: Every job MUST have an owner (can't be orphaned)
    # index=True: Fast lookups when filtering by user (WHERE user_id = ?)
    #
    # Why this is critical for security:
    # -----------------------------------
    # Without user_id:
    # - No way to determine ownership
    # - Anyone can see/modify any job
    # - Data breach (User A sees User B's job search)
    #
    # With user_id:
    # - Every job belongs to exactly one user
    # - Queries filter by current_user.id
    # - Prevents IDOR (Insecure Direct Object Reference) vulnerabilities
    #
    # Example IDOR attack (prevented by user_id):
    # User A: GET /api/jobs/5 → Only succeeds if job.user_id == User A's id
    # User A: GET /api/jobs/6 → Returns 404 if job.user_id == User B's id
    #
    # Database-level enforcement:
    # - Foreign key constraint ensures user exists before creating job
    # - If user deleted, jobs are cascade deleted (defined in User model)
    # - Can't have orphaned jobs (user_id pointing to non-existent user)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Required fields — nullable=False means they must have a value
    company = Column(String, nullable=False, index=True)  # Indexed for faster searches
    position = Column(String, nullable=False)

    # Status field — examples: "applied", "interviewing", "offer", "rejected"
    # Not using an Enum here to keep it flexible (you can add statuses later)
    status = Column(String, nullable=False, index=True)  # Indexed for filtering by status

    # Date when the application was submitted
    date_applied = Column(Date, nullable=False)

    # Optional fields — nullable=True (default) means they can be empty
    notes = Column(String, nullable=True)  # Longer text notes about the application
    follow_up_date = Column(Date, nullable=True)  # Reminder date for follow-ups

    # Relationship to User model
    # This is NOT a database column — it's a SQLAlchemy relationship
    # Enables: job.user (returns User object who owns this job)
    #
    # Parameters:
    # - "User": Name of the related model
    # - back_populates="job_applications": Bidirectional relationship
    #   - From JobApplication: job.user (User object)
    #   - From User: user.job_applications (list of JobApplication objects)
    #
    # SQLAlchemy magic:
    # - job.user doesn't execute a SQL query immediately
    # - It's lazy-loaded: query runs when you first access job.user
    # - Alternatively can be eager-loaded: .options(joinedload(JobApplication.user))
    #
    # Example usage:
    # job = db.query(JobApplication).first()
    # print(job.user.email)  # Automatically queries users table
    user = relationship("User", back_populates="job_applications")

    # Optional: You can add a __repr__ method for debugging
    # This makes it easier to see what's in an object when you print it
    def __repr__(self):
        return f"<JobApplication(id={self.id}, company='{self.company}', position='{self.position}', status='{self.status}')>"
