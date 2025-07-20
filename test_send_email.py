#!/usr/bin/env python3
"""
Script to actually send a test email using our notification system.
This will test the complete email flow with SendGrid.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.email_service import EmailService
from src.services.notification_service import NotificationService


def test_send_real_email():
    """Send a real test email"""
    print("Testing Real Email Sending...")
    
    # Check environment variables
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    test_email = "tahaharana@gmail.com"
    
    if not api_key:
        print("ERROR: SENDGRID_API_KEY not set")
        print("   Set it with: export SENDGRID_API_KEY='your_api_key'")
        return False
    
    if not from_email:
        print("ERROR: FROM_EMAIL not set")
        print("   Set it with: export FROM_EMAIL='your_verified_email@example.com'")
        return False
    
    if not test_email:
        print("ERROR: TEST_EMAIL not set")
        print("   Set it with: export TEST_EMAIL='your_email@example.com'")
        return False
    
    print(f"PASS: Using SendGrid API key: {api_key[:10]}...")
    print(f"PASS: From email: {from_email}")
    print(f"PASS: To email: {test_email}")
    
    try:
        # Test 1: Send journal reminder email (production format)
        print("\n1. Testing Journal Reminder Email...")
        email_service = EmailService()
        
        # Use actual journal reminder format
        journal_prompt = "Write about the most challenging moment of your day and how you handled it."
        success = email_service.send_journal_reminder(test_email, "Test User", journal_prompt)
        
        if success:
            print("PASS: Journal reminder email sent successfully!")
        else:
            print("ERROR: Journal reminder email failed")
            return False
        
        # Test 2: Send through notification service (requires user in DB)
        print("\n2. Testing NotificationService with real user...")
        notification_service = NotificationService()
        
        # Create a mock user for testing
        from src.models.user_model import User
        from src.app import create_app
        
        app = create_app()
        with app.app_context():
            # Check if test user exists, create if not
            test_user_id = "test_user_123"
            user = User.find_by_google_id(test_user_id)
            if not user:
                print("Creating test user...")
                User.save(test_user_id, test_email, "Test User")
            
            # Send journal reminder through notification service
            success = notification_service.send_journal_reminder(test_user_id)
            
            if success:
                print("PASS: NotificationService journal reminder sent successfully!")
            else:
                print("ERROR: NotificationService journal reminder failed")
                return False
        
        print("\nSUCCESS: All production email tests passed!")
        print(f"Check your email at {test_email} for the journal reminder messages.")
        return True
        
    except Exception as e:
        print(f"ERROR: Email test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_send_real_email()
    sys.exit(0 if success else 1) 