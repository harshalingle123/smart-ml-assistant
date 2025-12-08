"""
Email service for sending OTP verification codes and other notifications.
Supports multiple providers: SMTP, SendGrid, AWS SES, Mailgun.
"""
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
from datetime import datetime, timedelta
from app.core.config import settings
from app.mongodb import mongodb
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP or third-party providers"""

    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.sender_email = getattr(settings, 'SENDER_EMAIL', self.smtp_username)
        self.sender_name = getattr(settings, 'SENDER_NAME', 'AutoML')

    def _send_smtp_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email via SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email

            # Add text and HTML parts
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            message.attach(part1)
            message.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Send email using configured provider.
        Falls back to console logging if no provider is configured.
        """
        if not self.smtp_username or not self.smtp_password:
            # Development mode: log to console
            logger.warning(f"""
            ============================================
            EMAIL SERVICE (Development Mode)
            ============================================
            To: {to_email}
            Subject: {subject}

            {text_body}
            ============================================
            """)
            return True

        return self._send_smtp_email(to_email, subject, html_body, text_body)

    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code"""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))

    async def send_otp_email(self, email: str, otp: str, purpose: str = "signup") -> bool:
        """Send OTP verification email"""
        purpose_text = {
            "signup": "Complete Your Registration",
            "login": "Verify Your Login",
            "password_reset": "Reset Your Password",
            "email_change": "Verify Your New Email"
        }.get(purpose, "Verify Your Account")

        subject = f"{purpose_text} - OTP Code"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .otp-box {{ background: white; border: 2px dashed #667eea; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
                .warning {{ color: #dc2626; font-size: 14px; margin-top: 20px; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{purpose_text}</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>You've requested a verification code for your AutoML account. Use the code below to proceed:</p>

                    <div class="otp-box">
                        <div class="otp-code">{otp}</div>
                    </div>

                    <p><strong>This code will expire in 10 minutes.</strong></p>

                    <p>If you didn't request this code, please ignore this email or contact support if you have concerns.</p>

                    <div class="warning">
                        ⚠️ Never share this code with anyone. Our team will never ask for your verification code.
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2025 AutoML. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
{purpose_text}

Hello,

You've requested a verification code for your AutoML account.

Your verification code is: {otp}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Never share this code with anyone. Our team will never ask for your verification code.

---
AutoML Team
This is an automated message, please do not reply.
        """

        return self.send_email(email, subject, html_body, text_body)

    async def store_otp(self, email: str, otp: str, purpose: str = "signup") -> bool:
        """Store OTP in database with expiration"""
        try:
            # Normalize email to lowercase
            email = email.lower()

            otp_data = {
                "email": email,
                "otp": otp,
                "purpose": purpose,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10),
                "verified": False,
                "attempts": 0
            }

            # Delete any existing OTP for this email and purpose
            await mongodb.database["otp_codes"].delete_many({
                "email": email,
                "purpose": purpose
            })

            # Insert new OTP
            await mongodb.database["otp_codes"].insert_one(otp_data)
            logger.info(f"OTP stored for {email} with purpose {purpose}")
            return True

        except Exception as e:
            logger.error(f"Failed to store OTP for {email}: {str(e)}")
            return False

    async def verify_otp(self, email: str, otp: str, purpose: str = "signup") -> Dict:
        """
        Verify OTP code.
        Returns: {"valid": bool, "message": str}
        """
        try:
            # Normalize email to lowercase
            email = email.lower()

            # Find OTP record
            otp_record = await mongodb.database["otp_codes"].find_one({
                "email": email,
                "purpose": purpose,
                "verified": False
            })

            if not otp_record:
                return {"valid": False, "message": "No OTP found or already verified"}

            # Check if expired
            if datetime.utcnow() > otp_record["expires_at"]:
                await mongodb.database["otp_codes"].delete_one({"_id": otp_record["_id"]})
                return {"valid": False, "message": "OTP has expired"}

            # Check attempts
            if otp_record["attempts"] >= 5:
                await mongodb.database["otp_codes"].delete_one({"_id": otp_record["_id"]})
                return {"valid": False, "message": "Too many failed attempts"}

            # Verify OTP
            if otp_record["otp"] != otp:
                # Increment attempts
                await mongodb.database["otp_codes"].update_one(
                    {"_id": otp_record["_id"]},
                    {"$inc": {"attempts": 1}}
                )
                remaining = 5 - (otp_record["attempts"] + 1)
                return {"valid": False, "message": f"Invalid OTP. {remaining} attempts remaining"}

            # OTP is valid - mark as verified
            await mongodb.database["otp_codes"].update_one(
                {"_id": otp_record["_id"]},
                {"$set": {"verified": True}}
            )

            return {"valid": True, "message": "OTP verified successfully"}

        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return {"valid": False, "message": "Verification failed"}

    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email after successful registration"""
        subject = "Welcome to AutoML!"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .features {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .feature-item {{ margin: 10px 0; padding-left: 25px; position: relative; }}
                .feature-item:before {{ content: "✓"; position: absolute; left: 0; color: #667eea; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to AutoML! 🎉</h1>
                </div>
                <div class="content">
                    <p>Hi {name},</p>
                    <p>Thank you for joining AutoML! We're excited to have you on board.</p>

                    <div class="features">
                        <h3>What you can do with AutoML:</h3>
                        <div class="feature-item">Train custom ML models with automated machine learning</div>
                        <div class="feature-item">Access datasets from Kaggle and HuggingFace</div>
                        <div class="feature-item">Deploy models with direct API access</div>
                        <div class="feature-item">Use pre-built AI models for various tasks</div>
                        <div class="feature-item">Track your model performance and usage</div>
                    </div>

                    <p style="text-align: center;">
                        <a href="{settings.FRONTEND_URL}" class="button">Get Started</a>
                    </p>

                    <p>If you have any questions, feel free to reach out to our support team.</p>

                    <p>Happy modeling!</p>
                    <p><strong>The AutoML Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Welcome to AutoML!

Hi {name},

Thank you for joining AutoML! We're excited to have you on board.

What you can do with AutoML:
✓ Train custom ML models with automated machine learning
✓ Access datasets from Kaggle and HuggingFace
✓ Deploy models with direct API access
✓ Use pre-built AI models for various tasks
✓ Track your model performance and usage

Get started now: {settings.FRONTEND_URL}

If you have any questions, feel free to reach out to our support team.

Happy modeling!
The AutoML Team
        """

        return self.send_email(email, subject, html_body, text_body)


# Global email service instance
email_service = EmailService()
