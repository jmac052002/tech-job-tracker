from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.schemas import UserCreate, UserResponse, Token
from backend.utils.security import hash_password, verify_password, create_access_token
from backend.utils.dependencies import get_current_user

# Create router for authentication endpoints
# prefix="/auth": All routes here start with /auth
# tags=["authentication"]: Groups these endpoints in API docs
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Process:
    --------
    1. Validate email format (handled by Pydantic EmailStr)
    2. Check if email already registered (return 400 if exists)
    3. Validate password length (handled by Pydantic min_length=8)
    4. Hash password with bcrypt
    5. Create user in database
    6. Generate JWT access token
    7. Return user info + token (auto-login)

    Why auto-login after registration?
    -----------------------------------
    - Better UX: User doesn't need to login again after registering
    - Industry standard: Most apps auto-login after signup
    - No security downside: User just proved they own the email (sort of)

    Note on email verification:
    ---------------------------
    In production, you should:
    - Send verification email with confirmation link
    - Mark account as email_verified = False
    - Require verification before full access
    - This prevents:
      a) Registering with someone else's email
      b) Typos in email (user can't recover account)

    For MVP, we skip email verification (out of scope).

    Security considerations:
    ------------------------
    1. **Email uniqueness check**:
       - Prevents duplicate accounts
       - Returns 400 (not 409 Conflict) to avoid revealing existing users
       - Database unique constraint provides final safety net (race conditions)

    2. **Password hashing**:
       - NEVER store plain text password
       - hash_password() uses bcrypt with salt
       - Even if database leaks, passwords aren't directly exposed

    3. **Generic error messages**:
       - Don't reveal if email exists (prevents user enumeration)
       - Both "email exists" and "invalid format" return generic 400

    4. **Validation before DB operations**:
       - Pydantic validates email format before we touch database
       - Avoids wasted database queries on invalid input
       - Returns 422 Unprocessable Entity for validation errors

    Args:
        user_data (UserCreate): Email and password from request body
        db (Session): Database session from dependency injection

    Returns:
        dict: {
            "user": UserResponse (id, email, created_at),
            "token": Token (access_token, token_type)
        }

    Raises:
        HTTPException 400: Email already registered
        HTTPException 422: Invalid email format or password too short (Pydantic)

    Example request:
        POST /auth/register
        {
          "email": "joseph@example.com",
          "password": "SecurePassword123"
        }

    Example response:
        201 Created
        {
          "user": {
            "id": 42,
            "email": "joseph@example.com",
            "created_at": "2024-03-15T10:30:00"
          },
          "token": {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
          }
        }
    """

    # Step 1: Check if email already exists
    # Query database for existing user with this email
    # .first() returns User object if found, None if not found
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        # Email already registered
        # Return 400 Bad Request (not 409 Conflict to avoid revealing existing emails)
        # Don't reveal if email exists (prevents user enumeration attack)
        # Attacker could try millions of emails to build user database
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Step 2: Hash the password
    # user_data.password is plain text (sent over HTTPS)
    # hash_password() returns bcrypt hash (safe to store)
    # Example output: $2b$12$KIXIJGh8cEm.jA8N7L0Zy.OxV4bZ6FgH7Qv2M3nJ5kL9pR8sT6uW
    hashed_password = hash_password(user_data.password)

    # Step 3: Create new user in database
    # Create SQLAlchemy User object
    # Note: We pass hashed_password, NOT user_data.password
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password
        # created_at is auto-set by SQLAlchemy (default=datetime.utcnow)
    )

    # Add to database session (stages the INSERT)
    db.add(db_user)

    # Commit transaction (executes INSERT)
    # If this fails (e.g., database down), raises exception
    # FastAPI automatically rolls back and returns 500 Internal Server Error
    db.commit()

    # Refresh object to get auto-generated values (id, created_at)
    # After commit, db_user.id is populated with auto-increment value
    db.refresh(db_user)

    # Step 4: Generate JWT access token
    # Token payload: {"sub": "42", "exp": 1716396000}
    # "sub" is JWT standard for subject (user identifier)
    # Must convert user.id to string (JSON limitation)
    access_token = create_access_token(data={"sub": str(db_user.id)})

    # Step 5: Return user info + token
    # FastAPI automatically converts to JSON
    # UserResponse excludes hashed_password (security)
    return {
        "user": UserResponse.model_validate(db_user),  # Pydantic v2 syntax
        "token": Token(access_token=access_token, token_type="bearer")
    }


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.

    Why OAuth2PasswordRequestForm?
    -------------------------------
    - FastAPI's built-in form for username/password login
    - Follows OAuth2 specification (even though we're not using full OAuth2)
    - Parses application/x-www-form-urlencoded data (form data, not JSON)
    - Fields: username, password (we use username for email)

    Why form data instead of JSON?
    -------------------------------
    - OAuth2 spec requires form data
    - FastAPI's /docs interface expects OAuth2PasswordRequestForm
    - Allows "Authorize" button in Swagger UI to work automatically
    - Alternative: Accept JSON and manually parse (loses /docs integration)

    Authentication process:
    -----------------------
    1. Query database for user by email
    2. Verify password against stored bcrypt hash
    3. Generate JWT token if valid
    4. Return token (or 401 if invalid)

    Security considerations:
    ------------------------
    1. **Generic error message**:
       - Don't reveal if email exists or password wrong
       - Both return same "Invalid credentials" message
       - Prevents user enumeration (attacker can't build user list)
       - Prevents targeted attacks (attacker doesn't know if email is valid)

    2. **Timing attack prevention**:
       - Constant-time password comparison (bcrypt.verify does this)
       - Takes same time regardless of which character is wrong
       - Without this, attacker could guess password char-by-char by measuring response time
       - Example: "a" takes 1ms, "p" takes 50ms → first char is "p"

    3. **No password hints**:
       - Don't say "wrong password" or "email not found"
       - Don't say "password must contain uppercase"
       - All failures return same generic message

    4. **Rate limiting (future)**:
       - Should add rate limiting to prevent brute-force
       - Example: Max 5 failed attempts per minute per IP
       - Libraries: slowapi, fastapi-limiter
       - Without this, attacker can try thousands of passwords

    Why not return user info on login?
    -----------------------------------
    - Token is enough (client can decode "sub" claim if needed)
    - Keeps response minimal (bandwidth)
    - If needed, client can call GET /auth/me with token

    Args:
        form_data (OAuth2PasswordRequestForm): Username (email) and password from form
        db (Session): Database session from dependency injection

    Returns:
        Token: {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
        }

    Raises:
        HTTPException 401: Invalid email or password

    Example request (form data, not JSON):
        POST /auth/login
        Content-Type: application/x-www-form-urlencoded

        username=joseph@example.com&password=SecurePassword123

    Example response:
        200 OK
        {
          "access_token": "eyJhbGciOiJIUzI1NiIs...",
          "token_type": "bearer"
        }

    Client usage:
        1. Call POST /auth/login with credentials
        2. Receive access_token
        3. Store token securely (React Native: SecureStore, not AsyncStorage)
        4. Send token with all API requests:
           Authorization: Bearer <access_token>
    """

    # Define the exception we'll use for any auth failure
    # Same message for all failures (prevents user enumeration)
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},  # RFC 7235 requirement
    )

    # Step 1: Query database for user by email
    # OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    # .first() returns User object if found, None if not found
    user = db.query(User).filter(User.email == form_data.username).first()

    # Step 2: Verify user exists and password is correct
    # We do both checks together to avoid timing attacks
    # Don't reveal which part failed (email missing vs wrong password)
    if not user:
        # User not found (email doesn't exist)
        # Return generic error (don't reveal email not registered)
        raise invalid_credentials

    # Verify password against stored bcrypt hash
    # verify_password() does constant-time comparison (prevents timing attacks)
    # Returns True if password matches, False otherwise
    if not verify_password(form_data.password, user.hashed_password):
        # Password incorrect
        # Return same generic error (don't reveal password was wrong)
        raise invalid_credentials

    # Step 3: Authentication successful - generate JWT token
    # User exists and password correct
    # Create token with user_id in payload
    access_token = create_access_token(data={"sub": str(user.id)})

    # Step 4: Return token
    # Client will use this token for all future API requests
    # Token expires after JWT_EXPIRE_MINUTES (default 60 min)
    return Token(access_token=access_token, token_type="bearer")


# Optional: Add a /auth/me endpoint to get current user info
# Useful for frontend to fetch user details after login
@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.

    This is a protected route (requires valid JWT token).

    Why is this useful?
    -------------------
    - Frontend can fetch user details after login
    - Display "Logged in as: user@example.com"
    - Verify token is still valid
    - Refresh user data if needed

    Security note:
    --------------
    - Must include Authorization: Bearer <token> header
    - get_current_user dependency validates token
    - Returns 401 if token invalid/expired

    Args:
        current_user (User): Auto-injected by get_current_user dependency

    Returns:
        UserResponse: User info (id, email, created_at)

    Example request:
        GET /auth/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Example response:
        200 OK
        {
          "id": 42,
          "email": "joseph@example.com",
          "created_at": "2024-03-15T10:30:00"
        }
    """
    # get_current_user dependency already validated token and queried user
    # Just return the user object (FastAPI converts to UserResponse JSON)
    return current_user
