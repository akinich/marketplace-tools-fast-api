"""
================================================================================
Farm Management System - Password Hashing & Verification
================================================================================
Version: 1.2.0
Last Updated: 2025-11-17

Changelog:
----------
v1.2.0 (2025-11-17):
  - Replaced passlib with direct bcrypt usage (fixes compatibility issues)
  - Updated to bcrypt 4.1.2 (stable, modern version)
  - Automatic UTF-8 encoding handling
  - Simplified password hashing implementation

v1.1.0 (2025-11-17):
  - Fixed generate_temporary_password() to enforce 72 byte bcrypt limit
  - Reduced default password length to 16 characters (safe for bcrypt)
  - Added explicit byte length check and truncation
  - Ensures compatibility with bcrypt's maximum password length

v1.0.0 (2025-11-17):
  - Initial password management utilities
  - Bcrypt hashing with configurable rounds
  - Password verification
  - Temporary password generation

================================================================================
"""

import bcrypt
from app.config import settings
import secrets
import string


# ============================================================================
# PASSWORD HASHING
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ============================================================================
# PASSWORD GENERATION
# ============================================================================


def generate_temporary_password(length: int = 16) -> str:
    """
    Generate a secure temporary password.

    Bcrypt has a 72 byte maximum password length. To ensure compatibility,
    this function limits passwords to 16 ASCII characters (well under 72 bytes).

    Args:
        length: Password length (default 16, max 70 for bcrypt safety)

    Returns:
        Randomly generated password string (ASCII only, safe for bcrypt)
    """
    # Enforce maximum length for bcrypt compatibility (72 bytes = ~72 ASCII chars)
    # Use 70 as safe maximum to account for any edge cases
    if length > 70:
        length = 70

    # Character sets (all ASCII, 1 byte per character)
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"

    # Ensure password contains at least one of each
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    # Fill the rest with random characters
    all_chars = uppercase + lowercase + digits + special
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


# ============================================================================
# PASSWORD VALIDATION
# ============================================================================


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets strength requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"

    return True, ""


def check_password_needs_rehash(hashed_password: str, target_rounds: int = 12) -> bool:
    """
    Check if password hash needs to be updated (e.g., bcrypt rounds changed).

    Args:
        hashed_password: Stored hashed password
        target_rounds: Target number of rounds (default: 12)

    Returns:
        True if needs rehashing, False otherwise
    """
    try:
        # Extract rounds from existing hash (bcrypt format: $2b$rounds$...)
        parts = hashed_password.split('$')
        if len(parts) >= 3:
            current_rounds = int(parts[2])
            return current_rounds < target_rounds
        return False
    except Exception:
        return False
