"""
Email service for sending verification and notification emails.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_USER
        self.resend_api_key = settings.RESEND_API_KEY
        # Use configured sender or fallback to onboarding@resend.dev
        self.resend_from_email = settings.RESEND_FROM_EMAIL or "onboarding@resend.dev"
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text fallback (optional)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        if self.resend_api_key:
            logger.info(f"Attempting to send email via Resend to {to_email}")
            logger.info(f"From: {self.resend_from_email}")
            if not self.resend_from_email:
                logger.error("Resend configured but RESEND_FROM_EMAIL is missing")
                return False
            try:
                payload = {
                    "from": self.resend_from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                }
                if text_content:
                    payload["text"] = text_content

                logger.info(f"Sending Resend request with payload to: {to_email}")
                response = httpx.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=5.0,  # Reduced timeout
                )
                logger.info(f"Resend response status: {response.status_code}")
                logger.info(f"Resend response body: {response.text}")
                if 200 <= response.status_code < 300:
                    logger.info(f"Email sent successfully to {to_email} via Resend")
                    return True
                logger.error(
                    "Resend email failed: %s - %s",
                    response.status_code,
                    response.text,
                )
                return False
            except httpx.TimeoutException as e:
                logger.error(f"Resend timeout for {to_email}: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Resend email failed for {to_email}: {str(e)}")
                return False

        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("SMTP not configured, skipping email send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """
        Send email verification link.
        
        Args:
            to_email: User's email address
            verification_token: Unique verification token
        
        Returns:
            True if email was sent successfully
        """
        # Construct verification URL
        frontend_url = settings.CORS_ORIGINS.split(',')[0]  # Get first origin
        verification_url = f"{frontend_url}/auth/verify-email?token={verification_token}"
        
        subject = "Verify Your Email - Trading Journal"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to Trading Journal!</h2>
                <p>Thank you for registering. Please verify your email address to activate your account.</p>
                
                <a href="{verification_url}" class="button">Verify Email Address</a>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #2563eb;">{verification_url}</p>
                
                <p>This link will expire in 24 hours.</p>
                
                <div class="footer">
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Trading Journal!
        
        Thank you for registering. Please verify your email address to activate your account.
        
        Click this link to verify: {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset link.
        
        Args:
            to_email: User's email address
            reset_token: Unique reset token
        
        Returns:
            True if email was sent successfully
        """
        frontend_url = settings.CORS_ORIGINS.split(',')[0]
        reset_url = f"{frontend_url}/auth/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - Trading Journal"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #dc2626;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password for your Trading Journal account.</p>
                
                <a href="{reset_url}" class="button">Reset Password</a>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #dc2626;">{reset_url}</p>
                
                <p>This link will expire in 1 hour.</p>
                
                <div class="footer">
                    <p>If you didn't request a password reset, please ignore this email or contact support if you're concerned.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        We received a request to reset your password for your Trading Journal account.
        
        Click this link to reset your password: {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
