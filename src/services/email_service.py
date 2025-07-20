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
        # Use a more reliable from email - either your verified sender or a generic one
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
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                .content {{ padding: 30px 20px; }}
                .greeting {{ font-size: 18px; margin-bottom: 20px; color: #2c3e50; }}
                .prompt-section {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 25px; margin: 25px 0; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); }}
                .prompt-title {{ font-size: 16px; font-weight: 600; margin-bottom: 10px; }}
                .prompt-text {{ font-style: italic; font-size: 16px; line-height: 1.5; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; font-weight: 600; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: transform 0.2s; }}
                .button:hover {{ transform: translateY(-2px); }}
                .encouragement {{ font-size: 14px; color: #7f8c8d; margin: 20px 0; }}
                .footer {{ background-color: #ecf0f1; padding: 20px; text-align: center; font-size: 12px; color: #7f8c8d; }}
                .footer a {{ color: #3498db; text-decoration: none; }}
                .footer a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sentimeter</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        <h2>Hello {user_name}! 👋</h2>
                        <p>It's time for your daily reflection. Take a moment to pause and write about your day.</p>
                    </div>
                    
                    <div class="prompt-section">
                        <div class="prompt-title">Today's Prompt:</div>
                        <div class="prompt-text">{journal_prompt}</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/journal" class="button">Write in Your Journal ✍️</a>
                    </div>
                    
                    <div class="encouragement">
                        <p>💡 Remember, even a few minutes of reflection can make a big difference in your emotional well-being.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>You're receiving this email because you have journal notifications enabled.</p>
                    <p><a href="https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/settings">Manage notification settings</a> | <a href="https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/unsubscribe">Unsubscribe</a></p>
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
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                .content {{ padding: 30px 20px; }}
                .greeting {{ font-size: 18px; margin-bottom: 20px; color: #2c3e50; }}
                .success-message {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 25px; margin: 25px 0; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); }}
                .footer {{ background-color: #ecf0f1; padding: 20px; text-align: center; font-size: 12px; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sentimeter</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        <h2>Hello {user_name}! 👋</h2>
                        <p>This is a test email to confirm that your notification settings are working correctly.</p>
                    </div>
                    
                    <div class="success-message">
                        <h3>✅ Email Notifications Working!</h3>
                        <p>If you received this email, your email notifications are properly configured!</p>
                    </div>
                </div>
                <div class="footer">
                    <p>You're receiving this email because you have notifications enabled.</p>
                    <p><a href="https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/settings">Manage notification settings</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.provider.send_email(user_email, subject, html_content)

    def send_weekly_survey_reminder(self, user_email: str, user_name: str, survey_link: str = None) -> bool:
        """Send a weekly survey reminder email"""
        subject = "Your Weekly Check-in is Ready - Sentimeter"
        
        # Default survey link if not provided
        if not survey_link:
            survey_link = "https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/weekly-checkin"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Survey Reminder</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                .content {{ padding: 30px 20px; }}
                .greeting {{ font-size: 18px; margin-bottom: 20px; color: #2c3e50; }}
                .survey-section {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 25px; margin: 25px 0; border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); }}
                .features {{ margin: 20px 0; }}
                .features ul {{ list-style: none; padding: 0; }}
                .features li {{ padding: 8px 0; font-size: 14px; }}
                .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; font-weight: 600; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: transform 0.2s; }}
                .button:hover {{ transform: translateY(-2px); }}
                .privacy-note {{ font-size: 14px; color: #7f8c8d; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }}
                .footer {{ background-color: #ecf0f1; padding: 20px; text-align: center; font-size: 12px; color: #7f8c8d; }}
                .footer a {{ color: #3498db; text-decoration: none; }}
                .footer a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sentimeter</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        <h2>Hi {user_name}! 📊</h2>
                        <p>It's time for your weekly mental health check-in. Taking a few minutes to reflect on your week can help you track your well-being and identify patterns.</p>
                    </div>
                    
                    <div class="survey-section">
                        <h3>This week's check-in includes:</h3>
                        <div class="features">
                            <ul>
                                <li>📊 Quick ratings (stress, anxiety, happiness, etc.)</li>
                                <li>💭 Optional safety questions</li>
                                <li>📈 Progress tracking over time</li>
                                <li>🎯 Personalized insights</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{survey_link}" class="button">Take Your Weekly Check-in 📝</a>
                    </div>
                    
                    <div class="privacy-note">
                        <p>🔒 Your responses are private and secure. This data helps you understand your mental health patterns and make informed decisions about your well-being.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>You're receiving this email because you have weekly survey notifications enabled.</p>
                    <p><a href="https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/settings">Manage notification settings</a> | <a href="https://sentimeter-frontend-nzxteujmb-ahatanars-projects.vercel.app/unsubscribe">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.provider.send_email(user_email, subject, html_content)
