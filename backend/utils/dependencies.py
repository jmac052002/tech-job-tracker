from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.utils.security import decode_access_token

# HTTP Bearer authentication scheme
# This tells FastAPI to look for "Authorization: Bearer <token>" header
# Automatically extracts the token and passes it to route handlers
#
# How it works:
# 1. Client sends: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
# 2. HTTPBearer extracts: "eyJhbGciOiJIUzI1NiIs..."
# 3. Passes token to get_current_user() as HTTPAuthorizationCredentials
#
# What if header is missing or malformed?
# - FastAPI automatically returns 401 Unauthorized
# - Error: {"detail": "Not authenticated"}
#
# Why HTTPBearer instead of OAuth2PasswordBearer?
# - OAuth2PasswordBearer is for form-based login (username/password)
# - HTTPBearer is simpler and works with any Bearer token
# - We're using JWT, not full OAuth2, so HTTPBearer is more appropriate
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that validates JWT token and returns current user.

    This is the gatekeeper for all protected routes.
    Every request to a protected endpoint goes through this function.

    Validation process:
    -------------------
    1. Extract token from Authorization: Bearer <token> header
       - HTTPBearer() does this automatically
       - If header missing → 401 Unauthorized (before this function runs)

    2. Decode and verify JWT token
       - Checks signature with JWT_SECRET_KEY
       - Checks expiration timestamp
       - If invalid/expired → return None

    3. Extract user_id from token payload
       - JWT payload: {"sub": "42", "exp": 1716396000}
       - Extract: user_id = 42

    4. Query database for user
       - SELECT * FROM users WHERE id = 42
       - User might have been deleted since token was issued
       - If not found → 401 Unauthorized

    5. Return User object
       - Route handler receives authenticated user
       - Can access user.id, user.email, user.job_applications, etc.

    Why re-query database after validating token?
    ----------------------------------------------
    Token validation only proves token is valid, not that user still exists.

    Scenarios where token is valid but user shouldn't authenticate:
    - User account was deleted
    - User account was banned/suspended
    - User permissions changed (promoted to admin, downgraded, etc.)

    Trade-off:
    - Extra DB query on every request (slower)
    - vs accurate, up-to-date user data (more correct)

    Future optimization:
    - Cache user data in Redis with short TTL (5-15 min)
    - Reduces DB load while keeping data relatively fresh
    - Example: Redis key "user:42" → User data for 10 minutes

    Security considerations:
    ------------------------
    1. **Consistent error messages**:
       - All auth failures return same generic message
       - Don't reveal if token invalid vs user deleted vs wrong signature
       - Prevents attacker from learning system state

    2. **401 vs 403 status codes**:
       - 401 Unauthorized: Not authenticated (no token, invalid token)
       - 403 Forbidden: Authenticated but not authorized (has token but lacks permission)
       - This function returns 401 because it's about authentication, not authorization

    3. **WWW-Authenticate header**:
       - RFC 7235 requires this header on 401 responses
       - Tells client what authentication scheme to use
       - Value "Bearer" indicates JWT token expected

    Usage in route handlers:
    ------------------------
    @router.get("/api/jobs")
    def get_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # current_user is automatically injected by FastAPI
        # If token invalid, user never reaches this code (401 raised)
        jobs = db.query(JobApplication).filter(JobApplication.user_id == current_user.id).all()
        return jobs

    FastAPI dependency injection:
    -----------------------------
    Depends(get_current_user) is a FastAPI dependency.

    How it works:
    1. FastAPI sees Depends(get_current_user)
    2. Calls get_current_user() before route handler
    3. If get_current_user() raises HTTPException → return error to client
    4. If get_current_user() succeeds → pass User object to route handler

    Benefits:
    - Clean separation of concerns (auth logic separate from business logic)
    - Reusable across all protected routes
    - Easy to test (mock get_current_user in tests)
    - Type-safe (current_user: User gives IDE autocomplete)

    Args:
        credentials (HTTPAuthorizationCredentials): Auto-extracted by HTTPBearer
                                                    Contains .credentials (the token string)
        db (Session): Database session from get_db() dependency

    Returns:
        User: The authenticated user object from database

    Raises:
        HTTPException: 401 Unauthorized if:
                      - Token signature invalid
                      - Token expired
                      - Token malformed
                      - User ID missing from token
                      - User not found in database

    Example flow:
    -------------
    Client: GET /api/jobs
            Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    1. FastAPI extracts token with HTTPBearer
    2. Calls get_current_user(credentials=<token>, db=<session>)
    3. decode_access_token() validates signature and expiry
    4. Extract user_id = 42 from payload
    5. Query: SELECT * FROM users WHERE id = 42
    6. Return User(id=42, email="joseph@example.com", ...)
    7. Route handler executes with current_user = <User object>
    """

    # Define the exception we'll raise on any auth failure
    # Using same exception for all cases prevents information leakage
    # Attacker can't tell if token was invalid, expired, or user deleted
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # RFC 7235 requirement
    )

    # Step 1: Decode and verify JWT token
    # credentials.credentials contains the actual token string
    # decode_access_token() verifies signature and checks expiration
    # Returns payload dict if valid, None if invalid
    payload = decode_access_token(credentials.credentials)

    if payload is None:
        # Token is invalid (bad signature, expired, malformed)
        # Don't reveal why it failed (security best practice)
        raise credentials_exception

    # Step 2: Extract user_id from token payload
    # JWT standard: "sub" (subject) claim contains user identifier
    # We store user_id as string in token: {"sub": "42"}
    user_id_str: str = payload.get("sub")

    if user_id_str is None:
        # Token missing "sub" claim (malformed or tampered)
        raise credentials_exception

    # Convert user_id from string to integer
    # Tokens store everything as strings (JSON limitation)
    # Database expects integer for user.id
    try:
        user_id = int(user_id_str)
    except ValueError:
        # "sub" claim is not a valid integer (malformed token)
        raise credentials_exception

    # Step 3: Query database for user
    # Even though token is valid, user might have been deleted
    # Always verify user still exists before authenticating
    #
    # Why not trust the token alone?
    # - Token might be valid but user deleted after token issued
    # - Token might be stolen from deleted account
    # - User might be banned/suspended (future: check is_active field)
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        # User not found (deleted, never existed, or wrong database)
        raise credentials_exception

    # Step 4: Return authenticated user
    # Route handler receives this User object
    # Can access: user.id, user.email, user.job_applications, etc.
    return user
