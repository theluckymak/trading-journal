"""
Password validation utilities.
"""
import re
from typing import Tuple


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - At least 8 characters
    - At most 128 characters
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
    
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common weak passwords
    common_passwords = [
        "password", "12345678", "password123", "qwerty123", 
        "admin123", "welcome123", "letmein123"
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common, please choose a stronger password"
    
    return True, "Password is strong"


def sanitize_input(text: str, max_length: int = None) -> str:
    """
    Sanitize text input to prevent XSS and injection attacks.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")
    
    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def validate_email_format(email: str) -> bool:
    """
    Validate email format (basic check).
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    # Basic email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
