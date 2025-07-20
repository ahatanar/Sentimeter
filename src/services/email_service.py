import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from src.config import Config


class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str, from_email: str = None) -> bool:
        """Send an email using the provider"""
        pass


class SendGridEmailProvider(EmailProvider):
    """SendGrid implementation of email provider"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY environment variable is required")
        self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
        self.from_email = os.getenv("FROM_EMAIL", "noreply@sentimeter.com")
    
    def send_email(self, to_email: str, subject: str, html_content: str, from_email: str = None) -> bool:
        """Send email using SendGrid"""
        try:
            from_email = from_email or self.from_email
            mail = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=HtmlContent(html_content)
            )
            
            response = self.sg.send(mail)
            success = response.status_code in [200, 201, 202]
            if not success:
                print(f"SendGrid error: Status {response.status_code}, Body: {response.body}")
            
            return success
        except Exception as e:
            print(f"Error sending email via SendGrid: {e}")
            return False


class EmailServiceFactory:
    """Factory for creating email service instances"""
    
    @staticmethod
    def create_provider(provider_name: str = None) -> EmailProvider:
        """Create an email provider based on configuration"""
        provider_name = provider_name or os.getenv("EMAIL_PROVIDER", "sendgrid")
        
        if provider_name.lower() == "sendgrid":
            return SendGridEmailProvider()
        else:
            raise ValueError(f"Unsupported email provider: {provider_name}")


class EmailService:
    """Main email service that uses the factory pattern"""
    
    def __init__(self, provider: EmailProvider = None):
        self.provider = provider or EmailServiceFactory.create_provider()
    
    def send_journal_reminder(self, user_email: str, user_name: str, journal_prompt: str) -> bool:
        """Send a journal reminder email"""
        subject = "Time to Reflect - Your Daily Journal Reminder"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Journal Reminder</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4A90E2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .prompt {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #4A90E2; }}
                .button {{ display: inline-block; background-color: #4A90E2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sentimeter</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>It's time for your daily reflection. Take a moment to pause and write about your day.</p>
                    
                    <div class="prompt">
                        <h3>Today's Prompt:</h3>
                        <p><em>{journal_prompt}</em></p>
                    </div>
                    
                    <a href="http://localhost:3000/journal" class="button">Write in Your Journal</a>
                    
                    <p>Remember, even a few minutes of reflection can make a big difference in your emotional well-being.</p>
                </div>
                <div class="footer">
                    <p>You're receiving this email because you have journal notifications enabled.</p>
                    <p><a href="http://localhost:3000/settings">Manage notification settings</a> | <a href="#">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.provider.send_email(user_email, subject, html_content)
    
    def send_test_email(self, user_email: str, user_name: str) -> bool:
        """Send a test email"""
        subject = "Test Email - Sentimeter Notifications"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Email</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4A90E2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sentimeter</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>This is a test email to confirm that your notification settings are working correctly.</p>
                    <p>If you received this email, your email notifications are properly configured!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.provider.send_email(user_email, subject, html_content)
