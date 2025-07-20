#!/usr/bin/env python3
"""
Simple test to verify email integration works.
Run this to test if SendGrid is properly configured.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.email_service import EmailService
from src.services.notification_service import NotificationService


def test_email_integration():
    """Test if email service works with SendGrid"""
    print("Testing Email Integration...")
    
    try:
        # Test 1: Check if SendGrid API key is set
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            print("ERROR: SENDGRID_API_KEY not found in environment")
            print("   Set it with: export SENDGRID_API_KEY='your_api_key'")
            return False
        
        print("PASS: SENDGRID_API_KEY found")
        
        # Test 2: Test email service creation
        email_service = EmailService()
        print("PASS: EmailService created successfully")
        
        # Test 3: Test notification service
        notification_service = NotificationService()
        print("PASS: NotificationService created successfully")
        
        # Test 4: Test email sending (optional - comment out if you don't want to send real emails)
        test_email = os.getenv("TEST_EMAIL")
        if test_email:
            print(f"Sending test email to {test_email}...")
            success = email_service.send_test_email(test_email, "Test User")
            if success:
                print("PASS: Test email sent successfully!")
            else:
                print("ERROR: Test email failed to send")
                return False
        else:
            print("WARNING: Set TEST_EMAIL environment variable to test actual email sending")
            print("   Set it with: export TEST_EMAIL='your_email@example.com'")
        
        print("\nSUCCESS: Email integration test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Email integration test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_email_integration()
    sys.exit(0 if success else 1) 