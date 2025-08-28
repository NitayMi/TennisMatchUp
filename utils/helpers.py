"""
Minimal helper functions for TennisMatchUp
Only the essential functions to avoid import errors
"""
import re
from werkzeug.security import generate_password_hash, check_password_hash

def validate_email(email):
    """Validate email address format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it has 10-15 digits (international format)
    return len(digits_only) >= 10 and len(digits_only) <= 15

def hash_password(password):
    """Hash a password for storing in the database"""
    return generate_password_hash(password)

def check_password(password_hash, password):
    """Check if provided password matches the hash"""
    return check_password_hash(password_hash, password)