                                                                                         
from __future__ import annotations

import asyncio
import smtplib
import uuid
from email.message import EmailMessage
from email.utils import formataddr
from string import Template
from typing import Any

import structlog

from app.shared.config import settings

logger = structlog.get_logger(__name__)

_TEMPLATES: dict[str, dict[str, str]] = {
    "task_assigned": {
        "subject": "\U0001f4cb Task Assigned: $task_title",
        "body": (
            "Hi $recipient_name,\n\nYou have been assigned a new task:\n\n"
            "  Task: $task_title\n  Due:  $due_date\n  Meeting: $meeting_title\n\n"
            "Log in to DecisionFlow to view and update this task.\n\n— DecisionFlow AI"
        ),
    },
    "task_overdue": {
        "subject": "\u26a0\ufe0f Overdue Task: $task_title",
        "body": (
            "Hi $recipient_name,\n\nThe following task is now overdue:\n\n"
            "  Task: $task_title\n  Was due: $due_date\n\n"
            "Please update the status in DecisionFlow.\n\n— DecisionFlow AI"
        ),
    },
    "escalation_triggered": {
        "subject": "\u26a0\ufe0f Escalation: Overdue Task — $task_title",
        "body": (
            "Hi $recipient_name,\n\nThis is an automated escalation notice.\n\n"
            "  Task: $task_title\n  Due: $due_date\n  Escalation Level: $escalation_level\n\n"
            "Please take action immediately in DecisionFlow.\n\n— DecisionFlow AI"
        ),
    },
    "escalation_level_2": {
        "subject": "\U0001f6a8 Escalated to Manager: $task_title",
        "body": (
            "Hi $recipient_name,\n\nAn overdue task has been escalated to you (Level 2):\n\n"
            "  Task: $task_title\n\nThe task owner has not responded.\n\n— DecisionFlow AI"
        ),
    },
    "escalation_level_3": {
        "subject": "\U0001f534 Final Escalation: $task_title",
        "body": (
            "Hi $recipient_name,\n\nThis is a final escalation notice (Level 3):\n\n"
            "  Task: $task_title\n\nImmediate action required.\n\n— DecisionFlow AI"
        ),
    },
    "meeting_processed": {
        "subject": "\u2705 Meeting Processed: $meeting_title",
        "body": (
            "Hi $recipient_name,\n\nYour meeting has been processed:\n\n"
            "  Meeting: $meeting_title\n  Decisions: $decision_count\n"
            "  Tasks: $task_count\n  Risks: $risk_count\n\n— DecisionFlow AI"
        ),
    },
    "user_invited": {
        "subject": "\U0001f389 You've been invited to $org_name on DecisionFlow",
        "body": (
            "Hi $recipient_name,\n\nYou've been invited to join $org_name.\n\n"
            "Temporary password: $temp_password\n\nPlease change it on first login.\n\n— DecisionFlow AI"
        ),
    },
    "default": {"subject": "$subject", "body": "$body"},
}


class EmailAdapter:
                                                                       

    async def send(
        self,
        recipient_id: uuid.UUID,
        subject: str,
        body: str,
        payload: dict[str, Any],
    ) -> bool:
        recipient_email = payload.get("recipient_email")
        recipient_name = payload.get("recipient_name", "there")
        event_type = payload.get("event_type", "default")

        if not recipient_email:
            logger.warning("email_no_address", recipient_id=str(recipient_id), event_type=event_type)
            return False

        rendered_subject, rendered_body = self._render(
            event_type=event_type,
            subject=subject,
            body=body,
            payload={**payload, "recipient_name": recipient_name},
        )
        return await self._send_raw(recipient_email, rendered_subject, rendered_body)

    async def send_verification_email(self, *, recipient_email: str, recipient_name: str, verification_url: str) -> bool:
                                                                                 
        subject = "Verify your email address for DecisionFlow AI"
        text_body = f"Hi {recipient_name},\n\nVerify your email: {verification_url}\n\nThis link expires in 30 minutes."
        html_body = f'''<!doctype html><html><body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#172033"><table role="presentation" width="100%"><tr><td align="center" style="padding:40px 16px"><table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:14px"><tr><td style="padding:28px 36px;background:#182a4d;color:#fff;font-size:22px;font-weight:700">DecisionFlow AI</td></tr><tr><td style="padding:36px"><h1 style="margin:0 0 16px;font-size:24px">Verify your email address</h1><p>Hi {recipient_name},</p><p>Confirm your email to finish creating your organization and start extracting decisions and action items from your documents.</p><p style="margin:28px 0"><a href="{verification_url}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:13px 22px;border-radius:8px;font-weight:700">Verify email address</a></p><p style="font-size:13px;color:#667085">This link expires in 30 minutes. If you did not create this account, safely ignore this email.</p></td></tr></table></td></tr></table></body></html>'''
        if not settings.smtp_configured:
            logger.info("verification_email_dev_send", to=recipient_email, subject=subject)
            return True
        message = EmailMessage()
        message["From"] = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_FROM))
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(text_body, charset="utf-8")
        message.add_alternative(html_body, subtype="html")
        try:
            await asyncio.to_thread(self._deliver, message)
            logger.info("verification_email_sent", to=recipient_email)
            return True
        except (OSError, smtplib.SMTPException) as exc:
            logger.error("verification_email_failed", to=recipient_email, error=str(exc))
            return False

    async def send_invitation_verification_email(
        self, *, recipient_email: str, recipient_name: str, verification_url: str
    ) -> bool:
        ttl_hours = settings.INVITATION_TTL_HOURS
        subject = "Verify your invitation to DecisionFlow AI"
        text_body = (
            f"Hi {recipient_name},\n\nYou've been invited to a DecisionFlow workspace. "
            f"Verify your email to activate your access: {verification_url}\n\n"
            f"After verification, you will set your own password. This link expires in {ttl_hours} hours."
        )
        html_body = f'''<!doctype html><html><body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#172033"><table role="presentation" width="100%"><tr><td align="center" style="padding:40px 16px"><table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:14px"><tr><td style="padding:28px 36px;background:#182a4d;color:#fff;font-size:22px;font-weight:700">DecisionFlow AI</td></tr><tr><td style="padding:36px"><h1 style="margin:0 0 16px;font-size:24px">You have been invited</h1><p>Hi {recipient_name},</p><p>Verify your email address to activate your workspace access. You will then be able to choose your own password.</p><p style="margin:28px 0"><a href="{verification_url}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:13px 22px;border-radius:8px;font-weight:700">Verify email address</a></p><p style="font-size:13px;color:#667085">This link expires in {ttl_hours} hours. If you were not expecting this invitation, safely ignore this email.</p></td></tr></table></td></tr></table></body></html>'''
        return await self._send_html_email(
            recipient_email, subject, text_body, html_body, "invitation_verification"
        )

    async def send_password_reset_email(self, *, recipient_email: str, recipient_name: str, reset_url: str) -> bool:
                                                                                                
        subject = "Reset your DecisionFlow AI password"
        text_body = f"Hi {recipient_name},\n\nReset your password: {reset_url}\n\nThis link expires in 30 minutes."
        html_body = f'''<!doctype html><html><body style="margin:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#172033"><table role="presentation" width="100%"><tr><td align="center" style="padding:40px 16px"><table role="presentation" width="100%" style="max-width:600px;background:#fff;border-radius:14px"><tr><td style="padding:28px 36px;background:#182a4d;color:#fff;font-size:22px;font-weight:700">DecisionFlow AI</td></tr><tr><td style="padding:36px"><h1 style="margin:0 0 16px;font-size:24px">Reset your password</h1><p>Hi {recipient_name},</p><p>We received a request to reset your password. Choose a new password to secure your account.</p><p style="margin:28px 0"><a href="{reset_url}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:13px 22px;border-radius:8px;font-weight:700">Reset password</a></p><p style="font-size:13px;color:#667085">This link expires in 30 minutes. If you did not request a password reset, safely ignore this email.</p></td></tr></table></td></tr></table></body></html>'''
        return await self._send_html_email(recipient_email, subject, text_body, html_body, "password_reset")

    async def _send_html_email(self, recipient_email: str, subject: str, text_body: str, html_body: str, event: str) -> bool:
        if not settings.smtp_configured:
            logger.info("account_action_email_dev_send", to=recipient_email, event_type=event)
            return True
        message = EmailMessage()
        message["From"] = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_FROM))
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(text_body, charset="utf-8")
        message.add_alternative(html_body, subtype="html")
        try:
            await asyncio.to_thread(self._deliver, message)
            logger.info("account_action_email_sent", to=recipient_email, event_type=event)
            return True
        except (OSError, smtplib.SMTPException) as exc:
            logger.error("account_action_email_failed", to=recipient_email, event_type=event, error=str(exc))
            return False

    async def _send_raw(self, to_address: str, subject: str, body: str) -> bool:
        if not settings.smtp_configured:
            if not settings.is_production:
                logger.info("email_dev_send", to=to_address, subject=subject, body_preview=body[:100])
                return True
            logger.error("smtp_not_configured", to=to_address)
            return False

        message = EmailMessage()
        message["From"] = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_FROM))
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(body, charset="utf-8")

        try:
            await asyncio.to_thread(self._deliver, message)
            logger.info("email_sent", to=to_address, subject=subject[:50])
            return True
        except (OSError, smtplib.SMTPException) as exc:
            logger.error("email_send_failed", to=to_address, error=str(exc))
            return False

    @staticmethod
    def _deliver(message: EmailMessage) -> None:
                                                                              
        smtp_class = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
        with smtp_class(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        ) as client:
            if settings.SMTP_USE_TLS:
                client.starttls()
            if settings.SMTP_USERNAME:
                client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            client.send_message(message)

    def _render(
        self,
        event_type: str,
        subject: str,
        body: str,
        payload: dict[str, Any],
    ) -> tuple[str, str]:
        template = _TEMPLATES.get(event_type, _TEMPLATES["default"])
        raw_subject = template["subject"] if "$subject" not in template["subject"] else subject
        raw_body = template["body"] if "$body" not in template["body"] else body
        safe_payload = {key: str(value) if value is not None else "" for key, value in payload.items()}

        try:
            return (
                Template(raw_subject).safe_substitute(safe_payload),
                Template(raw_body).safe_substitute(safe_payload),
            )
        except (ValueError, TypeError):
            return subject, body
