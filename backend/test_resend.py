#!/usr/bin/env python3
"""
Test script to verify Resend email configuration.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.email_service import EmailService

def test_resend():
    print("=" * 60)
    print("RESEND CONFIGURATION TEST")
    print("=" * 60)
    
    has_key = bool(settings.RESEND_API_KEY)
    has_email = bool(settings.RESEND_FROM_EMAIL)
    
    print(f"RESEND_API_KEY configured: {'YES' if has_key else 'NO'}")
    print(f"RESEND_FROM_EMAIL configured: {'YES' if has_email else 'NO'}")
    
    if not has_key:
        print("\nNO RESEND_API_KEY!")
        return False
    
    if not has_email:
        print("\nNO RESEND_FROM_EMAIL!")
        return False
    
    print(f"\nAPI Key (first 20 chars): {settings.RESEND_API_KEY[:20]}...")
    print(f"From Email: {settings.RESEND_FROM_EMAIL}")
    
    # Test email
    email_service = EmailService()
    test_email = "test@example.com"
    
    print(f"\nSending test email to: {test_email}")
    result = email_service.send_email(
        to_email=test_email,
        subject="Test Email from Trading Journal",
        html_content="<p>This is a test email</p>",
        text_content="This is a test email"
    )
    
    if result:
        print("SUCCESS: Email sent!")
    else:
        print("FAILED: Email not sent - check logs above")
    
    print("=" * 60)
    return result

if __name__ == "__main__":
    success = test_resend()
    sys.exit(0 if success else 1)
