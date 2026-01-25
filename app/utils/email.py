import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email using SMTP"""
    try:
        # Skip if SMTP is not configured
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"SMTP not configured. Skipping email to {to_email}")
            print(f"Email subject: {subject}")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        message["To"] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(to_email: str, reset_token: str, full_name: str) -> bool:
    """Send password reset email"""
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .button {{ display: inline-block; padding: 12px 30px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{settings.APP_NAME}</h1>
            </div>
            <div class="content">
                <h2>Password Reset Request</h2>
                <p>Hi {full_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <a href="{reset_link}" class="button">Reset Password</a>
                <p>If you didn't request this, you can safely ignore this email.</p>
                <p>This link will expire in 1 hour.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {settings.APP_NAME}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, "Password Reset Request", html_content)


def send_verification_email(to_email: str, verification_token: str, full_name: str) -> bool:
    """Send email verification email"""
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .button {{ display: inline-block; padding: 12px 30px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to {settings.APP_NAME}!</h1>
            </div>
            <div class="content">
                <h2>Verify Your Email</h2>
                <p>Hi {full_name},</p>
                <p>Thank you for registering! Please verify your email address by clicking the button below:</p>
                <a href="{verification_link}" class="button">Verify Email</a>
                <p>If you didn't create an account, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2026 {settings.APP_NAME}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, "Verify Your Email", html_content)
