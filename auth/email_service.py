"""
Email Service for CoreSense Authentication
Password reset and email verification functionality with secure token management
"""

import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import logging

from .models import User, PasswordResetToken, EmailVerificationToken
from .auth_service import auth_service, AuthConfig
from .database import db_service
from .user_service import AuthResult

logger = logging.getLogger(__name__)

class EmailConfig:
    """Email configuration with environment variables"""
    
    # SMTP Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # Email settings
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@coresense.ai")
    FROM_NAME: str = os.getenv("FROM_NAME", "CoreSense AI Platform")
    REPLY_TO: str = os.getenv("REPLY_TO", "support@coresense.ai")
    
    # Application URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8501")
    
    # Email templates
    RESET_PASSWORD_SUBJECT: str = "Reset Your CoreSense Password"
    VERIFY_EMAIL_SUBJECT: str = "Verify Your CoreSense Account"
    WELCOME_EMAIL_SUBJECT: str = "Welcome to CoreSense AI Platform"

class EmailTemplates:
    """Email templates for various authentication emails"""
    
    PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Your Password - CoreSense AI</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #6C63FF; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        .security-note { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>💫 CoreSense AI Platform</h1>
        <h2>Password Reset Request</h2>
    </div>
    
    <div class="content">
        <p>Hello {{ user_name }},</p>
        
        <p>We received a request to reset your password for your CoreSense account. If you didn't make this request, please ignore this email.</p>
        
        <p>To reset your password, click the button below:</p>
        
        <p style="text-align: center;">
            <a href="{{ reset_link }}" class="button">Reset My Password</a>
        </p>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 3px;">{{ reset_link }}</p>
        
        <div class="security-note">
            <strong>⚠️ Security Notice:</strong>
            <ul>
                <li>This link will expire in {{ expiry_hours }} hour(s)</li>
                <li>For security reasons, this link can only be used once</li>
                <li>If you didn't request this reset, please contact support immediately</li>
            </ul>
        </div>
        
        <p>Best regards,<br>The CoreSense AI Team</p>
    </div>
    
    <div class="footer">
        <p>CoreSense AI Platform - Intelligent Core Training System</p>
        <p>If you have any questions, contact us at {{ support_email }}</p>
    </div>
</body>
</html>
    """
    
    EMAIL_VERIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Verify Your Email - CoreSense AI</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #6C63FF 0%, #8B5FBF 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        .welcome-note { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>💫 CoreSense AI Platform</h1>
        <h2>Welcome to CoreSense!</h2>
    </div>
    
    <div class="content">
        <p>Hello {{ user_name }},</p>
        
        <div class="welcome-note">
            <strong>🎉 Welcome to CoreSense AI Platform!</strong><br>
            You're one step away from starting your intelligent core training journey.
        </div>
        
        <p>To activate your account and start using CoreSense, please verify your email address by clicking the button below:</p>
        
        <p style="text-align: center;">
            <a href="{{ verification_link }}" class="button">Verify My Email</a>
        </p>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 3px;">{{ verification_link }}</p>
        
        <p><strong>What's next after verification?</strong></p>
        <ul>
            <li>🏋️ Complete your fitness profile</li>
            <li>🎯 Set your core training goals</li>
            <li>📊 Start your first stability assessment</li>
            <li>🤖 Get personalized AI coaching</li>
        </ul>
        
        <p>This verification link will expire in {{ expiry_hours }} hours for security reasons.</p>
        
        <p>Excited to help you achieve your core training goals!<br>The CoreSense AI Team</p>
    </div>
    
    <div class="footer">
        <p>CoreSense AI Platform - Intelligent Core Training System</p>
        <p>If you have any questions, contact us at {{ support_email }}</p>
    </div>
</body>
</html>
    """

class EmailService:
    """Service for sending authentication-related emails"""
    
    def __init__(self, config: EmailConfig = None):
        self.config = config or EmailConfig()
        self.auth_config = AuthConfig()
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """
        Send an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.FROM_NAME} <{self.config.FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Reply-To'] = self.config.REPLY_TO
            
            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls(context=context)
                
                if self.config.SMTP_USERNAME and self.config.SMTP_PASSWORD:
                    server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """
        Send password reset email
        
        Args:
            user: User object
            reset_token: Password reset token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate reset link
            reset_link = f"{self.config.FRONTEND_URL}/reset-password?token={reset_token}"
            
            # Prepare template variables
            template_vars = {
                'user_name': user.full_name,
                'reset_link': reset_link,
                'expiry_hours': self.auth_config.PASSWORD_RESET_EXPIRE_HOURS,
                'support_email': self.config.REPLY_TO
            }
            
            # Render HTML template
            template = Template(EmailTemplates.PASSWORD_RESET_TEMPLATE)
            html_content = template.render(**template_vars)
            
            # Send email
            return self._send_email(
                to_email=user.email,
                subject=self.config.RESET_PASSWORD_SUBJECT,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False
    
    def send_email_verification(self, user: User, verification_token: str) -> bool:
        """
        Send email verification email
        
        Args:
            user: User object
            verification_token: Email verification token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate verification link
            verification_link = f"{self.config.FRONTEND_URL}/verify-email?token={verification_token}"
            
            # Prepare template variables
            template_vars = {
                'user_name': user.full_name,
                'verification_link': verification_link,
                'expiry_hours': self.auth_config.EMAIL_VERIFICATION_EXPIRE_HOURS,
                'support_email': self.config.REPLY_TO
            }
            
            # Render HTML template
            template = Template(EmailTemplates.EMAIL_VERIFICATION_TEMPLATE)
            html_content = template.render(**template_vars)
            
            # Send email
            return self._send_email(
                to_email=user.email,
                subject=self.config.VERIFY_EMAIL_SUBJECT,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send email verification: {e}")
            return False

class PasswordResetService:
    """Service for handling password reset functionality"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
        self.email_service = EmailService()
    
    def initiate_password_reset(self, email: str) -> AuthResult:
        """
        Initiate password reset process
        
        Args:
            email: User email address
            
        Returns:
            AuthResult with reset initiation outcome
        """
        try:
            # Find user by email
            user = db_service.get_user_by_email(email)
            if not user:
                # Return success even if user not found (security best practice)
                return AuthResult(
                    success=True,
                    message="If an account with this email exists, you will receive password reset instructions."
                )
            
            if not user.is_active:
                return AuthResult(
                    success=False,
                    message="This account has been deactivated. Please contact support.",
                    errors=["Account deactivated"]
                )
            
            # Generate secure reset token
            reset_token = auth_service.generate_secure_token()
            token_hash = auth_service.hash_token(reset_token)
            
            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.config.PASSWORD_RESET_EXPIRE_HOURS)
            
            # Create password reset token record
            with db_service.session_scope() as session:
                password_reset = PasswordResetToken(
                    user_id=user.id,
                    token=reset_token,
                    token_hash=token_hash,
                    expires_at=expires_at
                )
                session.add(password_reset)
                session.flush()
            
            # Send password reset email
            email_sent = self.email_service.send_password_reset_email(user, reset_token)
            
            if not email_sent:
                logger.warning(f"Failed to send password reset email to {user.email}")
            
            logger.info(f"Password reset initiated for user: {user.email}")
            
            return AuthResult(
                success=True,
                message="If an account with this email exists, you will receive password reset instructions."
            )
            
        except Exception as e:
            logger.error(f"Password reset initiation failed: {e}")
            return AuthResult(
                success=False,
                message="Password reset failed due to a system error",
                errors=[str(e)]
            )
    
    def reset_password_with_token(self, token: str, new_password: str) -> AuthResult:
        """
        Reset password using reset token
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            AuthResult with password reset outcome
        """
        try:
            # Find password reset token
            with db_service.session_scope() as session:
                password_reset = session.query(PasswordResetToken).filter(
                    PasswordResetToken.token == token
                ).first()
                
                if not password_reset:
                    return AuthResult(
                        success=False,
                        message="Invalid or expired reset token",
                        errors=["Token not found"]
                    )
                
                if not password_reset.is_valid:
                    return AuthResult(
                        success=False,
                        message="Invalid or expired reset token",
                        errors=["Token expired or already used"]
                    )
                
                # Verify token hash
                if not auth_service.verify_token_hash(token, password_reset.token_hash):
                    password_reset.increment_attempts()
                    return AuthResult(
                        success=False,
                        message="Invalid reset token",
                        errors=["Token verification failed"]
                    )
                
                # Get user
                user = session.query(User).filter(User.id == password_reset.user_id).first()
                if not user or not user.is_active:
                    return AuthResult(
                        success=False,
                        message="User account not found or deactivated",
                        errors=["User not found"]
                    )
                
                # Validate new password
                is_valid_password, password_errors = auth_service.validate_password(new_password)
                if not is_valid_password:
                    password_reset.increment_attempts()
                    return AuthResult(
                        success=False,
                        message="New password does not meet security requirements",
                        errors=password_errors
                    )
                
                # Hash new password
                new_hashed_password = auth_service.hash_password(new_password)
                
                # Update user password
                user.hashed_password = new_hashed_password
                
                # Mark token as used
                password_reset.mark_used()
                
                session.flush()
            
            logger.info(f"Password reset completed for user: {user.email}")
            
            return AuthResult(
                success=True,
                message="Password reset successfully. You can now login with your new password."
            )
            
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return AuthResult(
                success=False,
                message="Password reset failed due to a system error",
                errors=[str(e)]
            )

class EmailVerificationService:
    """Service for handling email verification functionality"""
    
    def __init__(self, config: AuthConfig = None):
        self.config = config or AuthConfig()
        self.email_service = EmailService()
    
    def send_verification_email(self, user_id: int) -> AuthResult:
        """
        Send email verification
        
        Args:
            user_id: User ID
            
        Returns:
            AuthResult with verification send outcome
        """
        try:
            # Get user
            user = db_service.get_user_by_id(user_id)
            if not user:
                return AuthResult(
                    success=False,
                    message="User not found",
                    errors=["User does not exist"]
                )
            
            if user.is_verified:
                return AuthResult(
                    success=False,
                    message="Email is already verified",
                    errors=["Already verified"]
                )
            
            # Generate secure verification token
            verification_token = auth_service.generate_secure_token()
            token_hash = auth_service.hash_token(verification_token)
            
            # Calculate expiration time
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.config.EMAIL_VERIFICATION_EXPIRE_HOURS)
            
            # Create email verification token record
            with db_service.session_scope() as session:
                email_verification = EmailVerificationToken(
                    user_id=user.id,
                    token=verification_token,
                    token_hash=token_hash,
                    email=user.email,
                    expires_at=expires_at
                )
                session.add(email_verification)
                session.flush()
            
            # Send verification email
            email_sent = self.email_service.send_email_verification(user, verification_token)
            
            if not email_sent:
                logger.warning(f"Failed to send verification email to {user.email}")
                return AuthResult(
                    success=False,
                    message="Failed to send verification email",
                    errors=["Email delivery failed"]
                )
            
            logger.info(f"Verification email sent to user: {user.email}")
            
            return AuthResult(
                success=True,
                message="Verification email sent successfully. Please check your inbox."
            )
            
        except Exception as e:
            logger.error(f"Email verification send failed: {e}")
            return AuthResult(
                success=False,
                message="Failed to send verification email due to a system error",
                errors=[str(e)]
            )
    
    def verify_email_with_token(self, token: str) -> AuthResult:
        """
        Verify email using verification token
        
        Args:
            token: Email verification token
            
        Returns:
            AuthResult with verification outcome
        """
        try:
            # Find email verification token
            with db_service.session_scope() as session:
                email_verification = session.query(EmailVerificationToken).filter(
                    EmailVerificationToken.token == token
                ).first()
                
                if not email_verification:
                    return AuthResult(
                        success=False,
                        message="Invalid or expired verification token",
                        errors=["Token not found"]
                    )
                
                if not email_verification.is_valid:
                    return AuthResult(
                        success=False,
                        message="Invalid or expired verification token",
                        errors=["Token expired or already used"]
                    )
                
                # Verify token hash
                if not auth_service.verify_token_hash(token, email_verification.token_hash):
                    email_verification.increment_attempts()
                    return AuthResult(
                        success=False,
                        message="Invalid verification token",
                        errors=["Token verification failed"]
                    )
                
                # Get user
                user = session.query(User).filter(User.id == email_verification.user_id).first()
                if not user or not user.is_active:
                    return AuthResult(
                        success=False,
                        message="User account not found or deactivated",
                        errors=["User not found"]
                    )
                
                # Mark user as verified
                user.is_verified = True
                
                # Mark token as verified
                email_verification.mark_verified()
                
                session.flush()
            
            logger.info(f"Email verified for user: {user.email}")
            
            return AuthResult(
                success=True,
                message="Email verified successfully! Your account is now active.",
                user=user
            )
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return AuthResult(
                success=False,
                message="Email verification failed due to a system error",
                errors=[str(e)]
            )

# Global service instances
email_service = EmailService()
password_reset_service = PasswordResetService()
email_verification_service = EmailVerificationService()

# Export classes and services
__all__ = [
    'EmailConfig',
    'EmailTemplates',
    'EmailService',
    'PasswordResetService',
    'EmailVerificationService',
    'email_service',
    'password_reset_service',
    'email_verification_service'
]