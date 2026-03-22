from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

# SQLAlchemy model for User table
# This represents authenticated users in the system


class User(Base):
    """
    User model for authentication and authorization.

    This table stores user credentials and authentication data.
    Each user owns their own job applications (one-to-many relationship).

    Table structure:
    ----------------
    users
    ├── id (PK, auto-increment)
    ├── email (unique, indexed)
    ├── hashed_password
    └── created_at

    Security design decisions:
    --------------------------
    1. **Email as unique identifier**:
       - Simpler than separate username field
       - Common UX pattern (users remember their email)
       - Unique constraint prevents duplicate accounts

    2. **Only hashed_password stored (never plain text)**:
       - Even if database is leaked, passwords aren't directly exposed
       - Bcrypt hashing makes cracking impractical
       - No "password" column exists - only "hashed_password"

    3. **Email indexed for fast lookups**:
       - Login queries need to find user by email quickly
       - Index provides O(log n) lookup instead of O(n) table scan
       - Small performance cost on INSERT, big benefit on SELECT

    4. **created_at timestamp**:
       - Useful for analytics (user growth tracking)
       - Account age verification
       - Audit trail (when was account created?)

    Relationship design:
    --------------------
    One User → Many JobApplications
    - Each job application belongs to exactly one user
    - When user is deleted, their jobs are deleted (cascade)
    - This enables data isolation (users can't see each other's jobs)

    Why this matters for security:
    -------------------------------
    Without user_id foreign key on job_applications:
    - No way to determine ownership
    - Anyone could access/modify any job
    - Privacy nightmare (User A sees User B's job search)

    With user_id foreign key:
    - Queries filter by current_user.id
    - Prevents IDOR (Insecure Direct Object Reference) vulnerabilities
    - Users only see their own data

    Future considerations:
    ----------------------
    - Add email_verified field (for email verification flow)
    - Add is_active field (for banning/suspending users)
    - Add last_login timestamp (for analytics)
    - Add two_factor_enabled field (for 2FA support)
    - Add password_changed_at (for forcing password rotation)
    """

    __tablename__ = "users"

    # Primary key - auto-incremented integer
    # Every user gets a unique ID automatically
    id = Column(Integer, primary_key=True, index=True)

    # Email - unique identifier for login
    # Constraints:
    # - unique=True: No two users can have same email (prevents duplicate accounts)
    # - nullable=False: Email is required (can't be empty)
    # - index=True: Fast lookups during login (SELECT * FROM users WHERE email = ?)
    #
    # Why indexed?
    # - Every login queries by email
    # - Without index: O(n) table scan (slow as users grow)
    # - With index: O(log n) B-tree lookup (fast even with millions of users)
    email = Column(String, unique=True, nullable=False, index=True)

    # Hashed password - bcrypt hash (never plain text!)
    # Format: $2b$12$<22-char-salt><31-char-hash>
    # Example: $2b$12$KIXIJGh8cEm.jA8N7L0Zy.OxV4bZ6FgH7Qv2M3nJ5kL9pR8sT6uW
    #
    # Security note:
    # - This column stores the output of hash_password()
    # - Even database administrators can't see user passwords
    # - If database is leaked, attackers must brute-force each hash (very slow)
    hashed_password = Column(String, nullable=False)

    # Account creation timestamp
    # Automatically set to current time when user registers
    # default=datetime.utcnow: SQLAlchemy calls this function on INSERT
    #
    # Why UTC?
    # - Avoids timezone confusion (consistent across global deployments)
    # - Frontend can convert to user's local timezone
    # - AWS servers run on UTC
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to JobApplication model
    # This is a SQLAlchemy relationship, not a database column
    # It enables: user.job_applications (list of all jobs for this user)
    #
    # Parameters:
    # - "JobApplication": Name of the related model (string to avoid circular import)
    # - back_populates="user": Creates bidirectional relationship
    #   - From User: user.job_applications (list of JobApplication objects)
    #   - From JobApplication: job.user (User object)
    # - cascade="all, delete-orphan": When user deleted, delete their jobs too
    #
    # Why cascade delete?
    # - MVP decision: Keep it simple, delete user = delete their data
    # - Alternative: Keep orphaned jobs for data retention compliance
    # - Production consideration: May want soft delete (is_deleted flag) instead
    #
    # SQLAlchemy magic:
    # - This doesn't add a column to the users table
    # - It adds Python-level convenience for accessing related data
    # - Example: user.job_applications returns a list without writing SQL JOIN
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        """
        String representation for debugging.

        Never include password (even hashed) in __repr__!
        This might get logged, and logs should never contain credentials.

        Safe to include:
        - id (public identifier)
        - email (used for login, not sensitive like password)
        - created_at (public metadata)

        Example output:
        <User(id=42, email='joseph@example.com')>
        """
        return f"<User(id={self.id}, email='{self.email}', created_at='{self.created_at}')>"
