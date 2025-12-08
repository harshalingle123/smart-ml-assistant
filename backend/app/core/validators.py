"""
Validation utilities for authentication and user input.
"""
import re
from typing import Dict, List


class PasswordValidator:
    """Validates password with minimal requirements"""

    MIN_LENGTH = 6
    MAX_LENGTH = 128

    @staticmethod
    def validate_password(password: str) -> Dict[str, any]:
        """
        Validate password with minimal requirements.

        Requirements:
        - Minimum 6 characters
        - Maximum 128 characters

        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []

        # Length check
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long")

        if len(password) > PasswordValidator.MAX_LENGTH:
            errors.append(f"Password must not exceed {PasswordValidator.MAX_LENGTH} characters")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class EmailValidator:
    """Additional email validation beyond EmailStr"""

    @staticmethod
    def validate_email(email: str) -> Dict[str, any]:
        """
        Validate email format and check for disposable email domains.

        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []

        # Basic format check (additional to EmailStr)
        if not email or '@' not in email:
            errors.append("Invalid email format")
            return {"valid": False, "errors": errors}

        # Check for disposable email domains (common ones)
        disposable_domains = [
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org',
            'getnada.com', 'maildrop.cc', 'trashmail.com'
        ]

        domain = email.split('@')[1].lower()
        if domain in disposable_domains:
            errors.append("Disposable email addresses are not allowed")

        # Check for plus addressing abuse (optional - can be disabled)
        # if '+' in email.split('@')[0]:
        #     errors.append("Plus addressing is not supported")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class InputSanitizer:
    """Sanitize user inputs to prevent injection attacks"""

    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitize user name input.
        Allow letters, spaces, hyphens, and apostrophes.
        """
        # Remove any characters that aren't letters, spaces, hyphens, or apostrophes
        sanitized = re.sub(r"[^a-zA-Z\s\-']", '', name)

        # Limit length
        sanitized = sanitized[:100]

        # Remove extra spaces
        sanitized = ' '.join(sanitized.split())

        return sanitized.strip()

    @staticmethod
    def sanitize_string(text: str, max_length: int = 255) -> str:
        """
        General string sanitization.
        Remove control characters and limit length.
        """
        # Remove control characters
        sanitized = ''.join(char for char in text if char.isprintable() or char in '\n\t')

        # Limit length
        sanitized = sanitized[:max_length]

        return sanitized.strip()
