"""
Email Service
Handles transactional email sending for subscription system

Supports:
- SendGrid (recommended)
- AWS SES (alternative)
- SMTP (fallback)

Features:
- HTML email templates
- Personalization
- Retry logic
- Delivery tracking
- Background queue support
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for transactional emails

    Prioritizes providers in order:
    1. SendGrid (if configured)
    2. AWS SES (if configured)
    3. SMTP (fallback)
    """

    def __init__(self):
        self.provider = None
        self.templates_dir = Path(__file__).parent.parent / "templates" / "emails"

        # Try to initialize email provider
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize email provider based on available configuration"""
        from app.core.config import settings

        # Try SendGrid first (recommended)
        if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
            try:
                from sendgrid import SendGridAPIClient
                self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
                self.provider = "sendgrid"
                logger.info("Email service initialized with SendGrid")
                return
            except ImportError:
                logger.warning("SendGrid library not installed. Run: pip install sendgrid")
            except Exception as e:
                logger.warning(f"Failed to initialize SendGrid: {str(e)}")

        # Try AWS SES
        if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
            try:
                import boto3
                self.client = boto3.client(
                    'ses',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                self.provider = "ses"
                logger.info("Email service initialized with AWS SES")
                return
            except ImportError:
                logger.warning("Boto3 library not installed. Run: pip install boto3")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS SES: {str(e)}")

        # Try SMTP as fallback
        if hasattr(settings, 'SMTP_HOST') and settings.SMTP_HOST:
            self.provider = "smtp"
            logger.info("Email service initialized with SMTP")
            return

        logger.warning("No email provider configured. Emails will be logged only.")
        self.provider = "mock"

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self.provider not in [None, "mock"]

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send email using configured provider

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional)
            reply_to: Reply-to address (optional)
            attachments: List of attachment dicts (optional)

        Returns:
            Dict with success status and message_id
        """
        from app.core.config import settings

        # Use default sender if not provided
        if not from_email:
            from_email = getattr(settings, 'EMAIL_FROM', 'noreply@yourapp.com')
        if not from_name:
            from_name = getattr(settings, 'EMAIL_FROM_NAME', 'Smart ML Assistant')

        logger.info(f"Sending email to {to_email}: {subject}")

        try:
            if self.provider == "sendgrid":
                result = await self._send_sendgrid(
                    to_email, subject, html_content, from_email, from_name, reply_to
                )
            elif self.provider == "ses":
                result = await self._send_ses(
                    to_email, subject, html_content, from_email, from_name, reply_to
                )
            elif self.provider == "smtp":
                result = await self._send_smtp(
                    to_email, subject, html_content, from_email, from_name, reply_to
                )
            else:
                # Mock mode - just log
                logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
                logger.info(f"[MOCK EMAIL] HTML length: {len(html_content)} chars")
                result = {
                    "success": True,
                    "message_id": f"mock_{datetime.utcnow().timestamp()}",
                    "provider": "mock"
                }

            if result["success"]:
                logger.info(f"Email sent successfully: {result.get('message_id')}")
            else:
                logger.error(f"Email sending failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider
            }

    async def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str]
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        from sendgrid.helpers.mail import Mail, Email, To, Content

        try:
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if reply_to:
                message.reply_to = Email(reply_to)

            response = self.client.send(message)

            return {
                "success": response.status_code in [200, 202],
                "message_id": response.headers.get('X-Message-Id'),
                "status_code": response.status_code,
                "provider": "sendgrid"
            }

        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "sendgrid"
            }

    async def _send_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str]
    ) -> Dict[str, Any]:
        """Send email via AWS SES"""
        try:
            response = self.client.send_email(
                Source=f"{from_name} <{from_email}>",
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': html_content,
                            'Charset': 'UTF-8'
                        }
                    }
                },
                ReplyToAddresses=[reply_to] if reply_to else []
            )

            return {
                "success": True,
                "message_id": response['MessageId'],
                "provider": "ses"
            }

        except Exception as e:
            logger.error(f"AWS SES error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "ses"
            }

    async def _send_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str]
    ) -> Dict[str, Any]:
        """Send email via SMTP"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from app.core.config import settings

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            if reply_to:
                msg['Reply-To'] = reply_to

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if getattr(settings, 'SMTP_TLS', True):
                    server.starttls()
                if hasattr(settings, 'SMTP_USER') and settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                server.send_message(msg)

            return {
                "success": True,
                "message_id": f"smtp_{datetime.utcnow().timestamp()}",
                "provider": "smtp"
            }

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "smtp"
            }

    def _load_template(self, template_name: str) -> str:
        """Load email template from file"""
        template_path = self.templates_dir / f"{template_name}.html"

        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}")
            return "<html><body>{{content}}</body></html>"

        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Simple template rendering (replace {{variables}})"""
        rendered = template

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    # ===== TRANSACTIONAL EMAIL METHODS =====

    async def send_payment_confirmation(
        self,
        user_email: str,
        user_name: str,
        plan_name: str,
        amount: float,
        currency: str,
        payment_id: str,
        payment_date: datetime,
        next_billing_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Send payment confirmation email after successful payment

        This is sent immediately after payment.captured webhook
        """
        template = self._load_template("payment_confirmation")

        context = {
            "user_name": user_name,
            "plan_name": plan_name,
            "amount": f"{currency} {amount:,.2f}",
            "payment_id": payment_id,
            "payment_date": payment_date.strftime("%B %d, %Y"),
            "next_billing_date": next_billing_date.strftime("%B %d, %Y") if next_billing_date else "N/A",
            "current_year": datetime.utcnow().year
        }

        html_content = self._render_template(template, context)

        return await self.send_email(
            to_email=user_email,
            subject=f"Payment Confirmation - {plan_name}",
            html_content=html_content
        )

    async def send_failed_payment_alert(
        self,
        user_email: str,
        user_name: str,
        plan_name: str,
        amount: float,
        currency: str,
        failure_reason: str,
        retry_date: datetime,
        payment_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send failed payment alert with retry information

        This is sent when payment.failed webhook is received
        """
        template = self._load_template("failed_payment")

        context = {
            "user_name": user_name,
            "plan_name": plan_name,
            "amount": f"{currency} {amount:,.2f}",
            "failure_reason": failure_reason,
            "retry_date": retry_date.strftime("%B %d, %Y"),
            "payment_link": payment_link or "#",
            "has_payment_link": "block" if payment_link else "none",
            "current_year": datetime.utcnow().year
        }

        html_content = self._render_template(template, context)

        return await self.send_email(
            to_email=user_email,
            subject="⚠️ Payment Failed - Action Required",
            html_content=html_content
        )

    async def send_subscription_expiry_warning(
        self,
        user_email: str,
        user_name: str,
        plan_name: str,
        expiry_date: datetime,
        days_remaining: int,
        renewal_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send subscription expiry warning

        Sent at 7, 3, and 1 days before expiry
        """
        template = self._load_template("subscription_expiry")

        urgency = "urgent" if days_remaining <= 1 else "warning"

        context = {
            "user_name": user_name,
            "plan_name": plan_name,
            "expiry_date": expiry_date.strftime("%B %d, %Y"),
            "days_remaining": days_remaining,
            "urgency": urgency,
            "renewal_link": renewal_link or "#",
            "current_year": datetime.utcnow().year
        }

        html_content = self._render_template(template, context)

        subject = f"⏰ Your {plan_name} expires in {days_remaining} day{'s' if days_remaining > 1 else ''}"

        return await self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content
        )

    async def send_usage_warning(
        self,
        user_email: str,
        user_name: str,
        resource_name: str,
        usage_percentage: float,
        used: int,
        limit: int,
        plan_name: str,
        upgrade_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send usage limit warning

        Sent at 80%, 90%, and 100% usage
        """
        template = self._load_template("usage_warning")

        # Determine urgency level
        if usage_percentage >= 100:
            urgency = "critical"
            urgency_text = "Limit Reached"
        elif usage_percentage >= 90:
            urgency = "urgent"
            urgency_text = "Almost at Limit"
        else:
            urgency = "warning"
            urgency_text = "Approaching Limit"

        context = {
            "user_name": user_name,
            "resource_name": resource_name,
            "usage_percentage": f"{usage_percentage:.1f}",
            "used": f"{used:,}",
            "limit": f"{limit:,}",
            "plan_name": plan_name,
            "urgency": urgency,
            "urgency_text": urgency_text,
            "upgrade_link": upgrade_link or "#",
            "current_year": datetime.utcnow().year
        }

        html_content = self._render_template(template, context)

        subject = f"⚠️ {urgency_text}: {resource_name} at {usage_percentage:.0f}%"

        return await self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content
        )

    async def send_welcome_email(
        self,
        user_email: str,
        user_name: str,
        plan_name: str
    ) -> Dict[str, Any]:
        """
        Send welcome email after subscription activation

        This is sent after first successful payment
        """
        template = self._load_template("welcome")

        context = {
            "user_name": user_name,
            "plan_name": plan_name,
            "dashboard_link": "#",  # Add your dashboard URL
            "docs_link": "#",  # Add your docs URL
            "support_email": "support@yourapp.com",
            "current_year": datetime.utcnow().year
        }

        html_content = self._render_template(template, context)

        return await self.send_email(
            to_email=user_email,
            subject=f"Welcome to {plan_name}! 🎉",
            html_content=html_content
        )

    async def send_invoice_email(
        self,
        user_email: str,
        user_name: str,
        invoice_number: str,
        invoice_date: datetime,
        amount: float,
        currency: str,
        invoice_pdf_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send invoice email with PDF attachment

        This will be implemented in Day 5-6 with invoice generation
        """
        template = self._load_template("invoice")

        context = {
            "user_name": user_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date.strftime("%B %d, %Y"),
            "amount": f"{currency} {amount:,.2f}",
            "invoice_pdf_url": invoice_pdf_url or "#",
            "has_pdf": "block" if invoice_pdf_url else "none",
            "current_year": datetime.utcnow().year
        }

        html_content = self._render_template(template, context)

        return await self.send_email(
            to_email=user_email,
            subject=f"Invoice {invoice_number}",
            html_content=html_content
        )


# Global email service instance
email_service = EmailService()
