from sqlalchemy import Column, Integer, String, Date
from backend.database import Base

# SQLAlchemy model — represents the database table structure
# This is the "source of truth" for what gets stored in the database
class JobApplication(Base):
    __tablename__ = "job_applications"  # Table name in the database

    # Primary key — auto-incremented ID
    id = Column(Integer, primary_key=True, index=True)

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

    # Optional: You can add a __repr__ method for debugging
    # This makes it easier to see what's in an object when you print it
    def __repr__(self):
        return f"<JobApplication(id={self.id}, company='{self.company}', position='{self.position}', status='{self.status}')>"
