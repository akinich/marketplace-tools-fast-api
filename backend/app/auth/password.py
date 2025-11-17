"""
================================================================================
Farm Management System - Password Hashing & Verification
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial password management utilities
  - Bcrypt hashing with configurable rounds
  - Password verification
  - Temporary password generation

================================================================================
"""

from passlib.context import CryptContext
from app.config import settings
import secrets
import string

# ============================================================================
# PASSWORD CONTEXT
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# PASSWORD GENERATION
# ============================================================================


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a secure temporary password.

    Args:
        length: Password length (default 12)

    Returns:
        Randomly generated password string
    """
    # Character sets
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


def check_password_needs_rehash(hashed_password: str) -> bool:
    """
    Check if password hash needs to be updated (e.g., bcrypt rounds changed).

    Args:
        hashed_password: Stored hashed password

    Returns:
        True if needs rehashing, False otherwise
    """
    return pwd_context.needs_update(hashed_password)
