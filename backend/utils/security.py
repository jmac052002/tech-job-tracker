import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bcrypt configuration
# We use bcrypt directly instead of passlib for better Python 3.12+ compatibility
# Cost factor (rounds): 12 = 2^12 = 4,096 iterations
# Higher cost = slower hashing = more secure (but slower UX)
# Default cost factor of 12 is a good balance as of 2024
BCRYPT_ROUNDS = 12

# JWT Configuration from environment variables
# These MUST be set in your .env file
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # Default to HS256 if not set
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))  # Default 60 minutes


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Why bcrypt?
    -----------
    - **Adaptive cost factor**: Uses 2^12 rounds by default (4,096 iterations)
      - This is computationally expensive (~300ms per hash)
      - Makes brute-force attacks impractical (GPUs can only try ~1,000 passwords/sec)
      - Cost factor can be increased as hardware improves

    - **Built-in salt**: Automatically generates a unique random salt for each password
      - Salt: Random data added before hashing to prevent rainbow table attacks
      - Same password → different hash every time
      - 22-character salt embedded in the hash output

    - **Battle-tested**: Industry standard used by Django, Ruby on Rails, etc.

    Why NOT these alternatives?
    ---------------------------
    - **Plain text**: NEVER acceptable - database leak exposes all passwords
    - **MD5/SHA256**: Too fast - GPUs can compute billions of hashes per second
    - **SHA256 + manual salt**: Still too fast, requires error-prone manual salt management

    Real-world impact:
    ------------------
    - LinkedIn breach (2012): MD5 hashes - 6.5M passwords cracked in days
    - Ashley Madison breach (2015): Bcrypt hashes - only 11M of 36M cracked after months

    Bcrypt Hash Format:
    -------------------
    Example: $2b$12$KIXIJGh8cEm.jA8N7L0Zy.OxV4bZ6FgH7Qv2M3nJ5kL9pR8sT6uW

    $2b$    = Bcrypt algorithm version
    $12$    = Cost factor (2^12 = 4,096 rounds)
    KIX...  = 22-character salt (random per hash)
    .Ox...  = 31-character hash result

    Args:
        plain_password (str): The plain text password to hash

    Returns:
        str: The bcrypt hash (includes algorithm version, cost factor, salt, and hash)

    Security note:
        The entire string (version + cost + salt + hash) is stored in the database.
        No need to store salt separately - it's embedded in the hash.

    Python 3.12+ note:
        Using bcrypt directly instead of passlib for better compatibility.
        Bcrypt requires bytes input, so we encode the password to UTF-8.
    """
    # Convert password string to bytes (bcrypt requires bytes)
    password_bytes = plain_password.encode('utf-8')

    # Generate salt and hash in one step
    # gensalt(rounds=12): Creates a salt with cost factor 2^12
    # hashpw(): Hashes the password with the generated salt
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=BCRYPT_ROUNDS))

    # Return as string (decode from bytes)
    # Database stores strings, not bytes
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.

    How it works:
    -------------
    1. Extracts the salt from the stored hash
    2. Hashes the provided plain password with that same salt
    3. Compares the new hash with the stored hash
    4. Returns True if they match, False otherwise

    Security features:
    ------------------
    - **Constant-time comparison**: Prevents timing attacks
      - Timing attack: Attacker measures how long comparison takes to guess password
      - Constant-time: Takes same time regardless of how many characters match

    - **Safe error handling**: Returns False for invalid hash formats (doesn't crash)

    Args:
        plain_password (str): The password attempt (from login form)
        hashed_password (str): The stored bcrypt hash (from database)

    Returns:
        bool: True if password matches, False otherwise

    Example usage:
        # During login
        user = db.query(User).filter(User.email == email).first()
        if user and verify_password(password_attempt, user.hashed_password):
            # Login successful
            return create_access_token({"sub": str(user.id)})
        else:
            # Login failed - IMPORTANT: Don't reveal which part failed
            raise HTTPException(401, "Invalid credentials")

    Python 3.12+ note:
        Using bcrypt.checkpw() directly for better compatibility.
        Both inputs must be bytes, so we encode them.
    """
    # Convert both password and hash to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    # Verify password
    # checkpw() does constant-time comparison (prevents timing attacks)
    # Returns True if password matches, False otherwise
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    JWT Structure: Three parts separated by dots
    --------------------------------------------
    header.payload.signature

    Example token:
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsImV4cCI6MTcxNjM5NjAwMH0.3pKl8V5Kk2GGxFD...

    Part 1: Header (Base64-encoded JSON)
    {
      "alg": "HS256",     # Algorithm used (HMAC-SHA256)
      "typ": "JWT"        # Token type
    }

    Part 2: Payload (Base64-encoded JSON - the actual data)
    {
      "sub": "42",        # Subject (user_id in our case)
      "exp": 1716396000   # Expiration timestamp (Unix epoch)
    }

    Part 3: Signature (HMAC-SHA256 hash)
    HMACSHA256(
      base64(header) + "." + base64(payload),
      JWT_SECRET_KEY
    )

    Security concepts:
    ------------------
    - **Payload is NOT encrypted**: Only Base64-encoded (anyone can decode it)
      - Base64 is encoding, not encryption
      - Never put sensitive data in payload (no passwords, emails, credit cards)
      - Only put user identifier (sub = user_id)

    - **Signature prevents tampering**:
      - If attacker modifies payload, signature becomes invalid
      - Only someone with JWT_SECRET_KEY can create valid signatures
      - This is why JWT_SECRET_KEY must be kept secret!

    - **Expiration is enforced**:
      - Token auto-expires after JWT_EXPIRE_MINUTES
      - Limits damage if token is stolen
      - User must re-login after expiration

    Why JWT over session cookies?
    -----------------------------
    ✅ Stateless: Backend doesn't need to store sessions (scales better)
    ✅ Mobile-friendly: Works with React Native (easier than cookies)
    ✅ Microservices: Any service can validate token with the secret key
    ❌ Can't revoke before expiry: Once issued, valid until expiration (need Redis blacklist)

    Args:
        data (dict): Payload data to encode in token
                     Should include {"sub": str(user_id)}
        expires_delta (Optional[timedelta]): Custom expiration time
                                             Defaults to JWT_EXPIRE_MINUTES from .env

    Returns:
        str: The signed JWT token

    Example usage:
        # After successful login or registration
        token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}

    Security warning:
        If JWT_SECRET_KEY is leaked, attackers can forge tokens for any user!
        - Generate a strong random key (32+ characters)
        - Store in .env, never commit to git
        - Rotate periodically (forces all users to re-login)
        - Use AWS Secrets Manager in production
    """
    # Create a copy of the data to avoid modifying the original
    to_encode = data.copy()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)

    # Add expiration to payload
    # "exp" is a standard JWT claim that python-jose checks automatically
    to_encode.update({"exp": expire})

    # Sign and encode the token
    # jwt.encode() does three things:
    # 1. Base64-encodes the header
    # 2. Base64-encodes the payload
    # 3. Creates HMAC-SHA256 signature using JWT_SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Validation process:
    -------------------
    1. Split token into header.payload.signature
    2. Verify signature using JWT_SECRET_KEY
       - Recalculates HMAC-SHA256 hash
       - Compares with signature in token
       - If mismatch → token was tampered with → REJECT

    3. Check expiration timestamp
       - Compares "exp" claim with current time
       - If expired → REJECT

    4. Extract and return payload

    Common rejection reasons:
    -------------------------
    - **Invalid signature**: Token was modified or signed with wrong key
    - **Expired**: Token past its expiration time
    - **Malformed**: Not a valid JWT format
    - **Wrong algorithm**: Algorithm confusion attack attempt

    Algorithm confusion attack (prevented):
    ---------------------------------------
    Attacker tries to change algorithm from RS256 to HS256, then signs
    with the public key. We prevent this by explicitly specifying
    algorithms=["HS256"] in jwt.decode().

    Args:
        token (str): The JWT token to decode

    Returns:
        Optional[dict]: The decoded payload if valid, None if invalid

    Example usage:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            # Query user from database...
        except:
            raise HTTPException(401, "Invalid token")

    Security note:
        Even if token is valid, always re-query the user from database.
        Why? Token might be valid but:
        - User was deleted
        - User was banned/suspended
        - User's permissions changed

        Trade-off: Extra DB query vs stale user data
        Future optimization: Cache user data in Redis with short TTL
    """
    try:
        # Decode and verify token
        # algorithms=[JWT_ALGORITHM]: Only accept HS256 (prevents algorithm confusion)
        # Raises JWTError if signature invalid or token expired
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        # Token is invalid (bad signature, expired, malformed, etc.)
        # Return None so calling code can handle appropriately
        return None
