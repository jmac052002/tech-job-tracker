from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date, datetime

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
    user_id: int  # Added for authentication - each job belongs to a user

    class Config:
        # This allows Pydantic to read data from SQLAlchemy model attributes
        # Without this, you'd get errors when trying to convert a SQLAlchemy object to JSON
        from_attributes = True  # Pydantic v2 syntax (was orm_mode in v1)


# ============================================================================
# User Schemas (Authentication)
# ============================================================================

# Why separate User schemas from JobApplication schemas?
# ------------------------------------------------------
# - Different validation rules (email format vs company name)
# - Different security requirements (never expose hashed_password)
# - Clear separation of concerns (auth logic vs business logic)
# - Easier to maintain and test


class UserBase(BaseModel):
    """
    Base User schema with shared fields.

    Why EmailStr instead of str?
    ----------------------------
    - EmailStr is a Pydantic type that validates email format
    - Rejects invalid emails like "notanemail", "test@", "@example.com"
    - Uses regex validation: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
    - Prevents typos during registration (better UX)
    - Prevents malicious input (security)

    Note: EmailStr requires 'email-validator' package
    If you get an error, install it: pip install email-validator
    """
    email: EmailStr = Field(..., description="User's email address (must be valid format)")


class UserCreate(UserBase):
    """
    Schema for user registration (POST /auth/register).

    Security considerations:
    ------------------------
    1. **Password is plain text here** (will be hashed before storing):
       - User sends plain text over HTTPS (encrypted in transit)
       - Backend receives plain text in this schema
       - Backend calls hash_password() before saving to database
       - Database only stores bcrypt hash, never plain text

    2. **Minimum 8 characters** (enforced by min_length):
       - Prevents weak passwords like "123" or "pass"
       - 8 chars is minimum, but passphrase is better ("correct horse battery staple")
       - Production: Consider zxcvbn library for entropy-based validation

    3. **No maximum length** (bcrypt truncates at 72 bytes):
       - Let users create long passphrases
       - Bcrypt only uses first 72 bytes anyway
       - Better UX than arbitrary max_length=20

    Why not enforce complexity rules (1 uppercase, 1 number, 1 special)?
    --------------------------------------------------------------------
    - Forces users into predictable patterns attackers know
    - "Password123!" is worse than "correct horse battery staple"
    - Length matters more than character variety
    - Complexity rules often hurt UX without improving security

    What we DO enforce:
    - Minimum 8 characters (prevents trivial passwords)
    - Email format validation (prevents typos)
    - Email uniqueness (checked in route handler)
    """
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")


class UserResponse(UserBase):
    """
    Schema for returning user data in API responses.

    Security note: NO PASSWORD FIELD
    --------------------------------
    This schema intentionally excludes any password field (plain or hashed).

    Why?
    - API responses are logged
    - Frontend might cache responses
    - Browser DevTools shows network responses
    - Even hashed passwords shouldn't be exposed in API responses

    What if you need to verify password?
    - Users send password to /auth/login
    - Backend verifies with verify_password()
    - Never send password back to client

    Fields included:
    ----------------
    - id: User's unique identifier (needed for relationships)
    - email: Useful for displaying "Logged in as: user@example.com"
    - created_at: Shows account age, useful for profile pages

    Example JSON response:
    {
      "id": 42,
      "email": "joseph@example.com",
      "created_at": "2024-03-15T10:30:00"
    }
    """
    id: int
    created_at: datetime

    class Config:
        # Allows Pydantic to read from SQLAlchemy User model
        # Converts: User(id=42, email="...", hashed_password="...") → UserResponse(id=42, email="...")
        # Notice: hashed_password is automatically excluded (not in this schema)
        from_attributes = True


class Token(BaseModel):
    """
    Schema for JWT token responses (returned by /auth/login and /auth/register).

    OAuth2 specification:
    ---------------------
    This format follows the OAuth2 standard for token responses.
    Even though we're not using full OAuth2, we follow the convention:
    - access_token: The JWT token string
    - token_type: Always "bearer" (indicates Authorization: Bearer <token>)

    Why "bearer" token?
    -------------------
    - Bearer = "whoever bears (holds) this token is authorized"
    - No additional proof required (unlike signed requests)
    - Simple for clients to use: Authorization: Bearer <token>
    - Standard HTTP header, works with all HTTP clients

    Security implication:
    ---------------------
    If token is stolen, attacker can use it until expiration.
    This is why:
    - Tokens should have short expiry (60 min default)
    - HTTPS is mandatory (prevents man-in-the-middle theft)
    - Tokens should be stored securely (React Native SecureStore, not localStorage)

    Example JSON response:
    {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer"
    }

    Client usage:
    fetch('/api/jobs', {
      headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIs...'
      }
    })
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class TokenData(BaseModel):
    """
    Schema for decoded JWT token data (internal use).

    This is NOT returned in API responses.
    It's used internally to represent the decoded token payload.

    When is this used?
    ------------------
    When get_current_user() dependency decodes a token:
    1. Extract token from Authorization header
    2. Decode JWT → dict like {"sub": "42", "exp": 1716396000}
    3. Convert to TokenData object → TokenData(user_id=42)
    4. Use user_id to query database

    Why Optional[int]?
    ------------------
    During decoding, user_id might be missing or invalid:
    - Token might not have "sub" claim
    - "sub" might be non-numeric
    - Token might be malformed

    None allows us to handle these cases gracefully:
    if token_data.user_id is None:
        raise HTTPException(401, "Invalid token")

    Example decoded token:
    JWT payload: {"sub": "42", "exp": 1716396000}
    TokenData: TokenData(user_id=42)
    """
    user_id: Optional[int] = Field(None, description="User ID extracted from token")
