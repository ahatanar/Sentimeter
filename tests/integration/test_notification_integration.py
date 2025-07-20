#!/usr/bin/env python3
"""
Test the complete notification system integration.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.notification_service import NotificationService
from src.services.email_service import EmailService


def test_notification_integration():
    """Test the complete notification system"""
    print("Testing Complete Notification System...")
    
    try:
        # Test 1: Check environment variables
        required_vars = ["SENDGRID_API_KEY", "FROM_EMAIL"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"ERROR: Missing environment variables: {', '.join(missing_vars)}")
            print("   Set them with:")
            for var in missing_vars:
                print(f"   export {var}='your_value'")
            return False
        
        print("PASS: Environment variables configured")
        
        # Test 2: Test email service
        email_service = EmailService()
        print("PASS: EmailService created")
        
        # Test 3: Test notification service
        notification_service = NotificationService()
        print("PASS: NotificationService created")
        
        # Test 4: Test journal prompts
        prompts = notification_service.get_journal_prompts()
        print(f"PASS: Found {len(prompts)} journal prompts")
        
        # Test 5: Test email sending (if TEST_EMAIL is set)
        test_email = os.getenv("TEST_EMAIL")
        if test_email:
            print(f"Testing email to {test_email}...")
            success = notification_service.send_test_email("test_user_id")
            if success:
                print("PASS: Test email sent successfully!")
            else:
                print("ERROR: Test email failed")
                return False
        else:
            print("WARNING: Set TEST_EMAIL to test actual email sending")
        
        print("\nSUCCESS: Notification system integration test passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Notification system test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_notification_integration()
    sys.exit(0 if success else 1) 