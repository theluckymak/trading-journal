"""
Encryption service for sensitive data (MT5 credentials).
"""
from cryptography.fernet import Fernet
from typing import Optional
import base64

from app.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with Fernet cipher."""
        # Ensure the key is properly formatted (32 bytes, base64 encoded)
        key = settings.ENCRYPTION_KEY.encode()
        
        # If key is not proper length, derive one from it
        if len(key) < 32:
            key = base64.urlsafe_b64encode(key.ljust(32, b'0'))
        elif len(key) > 32:
            key = base64.urlsafe_b64encode(key[:32])
        else:
            key = base64.urlsafe_b64encode(key)
            
        self.cipher = Fernet(key)
    
    def encrypt(self, plain_text: str) -> str:
        """
        Encrypt plain text data.
        
        Args:
            plain_text: Plain text to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        encrypted_bytes = self.cipher.encrypt(plain_text.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_text: Base64 encoded encrypted data
            
        Returns:
            Decrypted plain text, or None if decryption fails
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception:
            return None


# Global instance
encryption_service = EncryptionService()
