"""
Email utilities for sending newsletters using Resend API
Production-ready with error handling, logging, and retry logic
"""
import resend
import logging
from typing import List, Tuple, Optional
from django.conf import settings
from time import sleep

logger = logging.getLogger(__name__)


class EmailService:
    """Production-ready email service using Resend API"""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        if not self.api_key:
            raise ValueError("RESEND_API_KEY not found in settings")
        resend.api_key = self.api_key

    def send_single_email(
            self,
            to_email: str,
            subject: str,
            message: str,
            from_email: Optional[str] = None,
            html_content: Optional[str] = None,
            retry_count: int = 3
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a single email with retry logic

        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Plain text message
            from_email: Sender email (defaults to settings)
            html_content: Optional HTML content
            retry_count: Number of retry attempts

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not from_email:
            from_email = getattr(
                settings,
                'RESEND_FROM_EMAIL',
                'Amravati Wears Market <onboarding@resend.dev>'
            )

        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": message,
        }

        # Add HTML content if provided
        if html_content:
            params["html"] = html_content

        for attempt in range(retry_count):
            try:
                response = resend.Emails.send(params)
                logger.info(f"Email sent successfully to {to_email}: {response}")
                return True, None

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Attempt {attempt + 1}/{retry_count} failed for {to_email}: {error_msg}"
                )

                # If this is the last attempt, return the error
                if attempt == retry_count - 1:
                    logger.error(f"Failed to send email to {to_email} after {retry_count} attempts")
                    return False, error_msg

                # Wait before retrying (exponential backoff)
                sleep(2 ** attempt)

        return False, "Unknown error"

    def send_bulk_email(
            self,
            recipient_list: List[str],
            subject: str,
            message: str,
            from_email: Optional[str] = None,
            html_content: Optional[str] = None,
            batch_size: int = 10,
            delay_between_batches: float = 1.0
    ) -> Tuple[int, List[dict]]:
        """
        Send emails to multiple recipients in batches

        Args:
            recipient_list: List of recipient email addresses
            subject: Email subject
            message: Plain text message
            from_email: Sender email
            html_content: Optional HTML content
            batch_size: Number of emails to send before pausing
            delay_between_batches: Seconds to wait between batches

        Returns:
            Tuple of (success_count: int, failed_emails: List[dict])
        """
        if not recipient_list:
            logger.warning("No recipients provided for bulk email")
            return 0, []

        success_count = 0
        failed_emails = []
        total_emails = len(recipient_list)

        logger.info(f"Starting bulk email send to {total_emails} recipients")

        for index, email in enumerate(recipient_list, 1):
            # Validate email format
            if not email or '@' not in email:
                logger.warning(f"Invalid email format: {email}")
                failed_emails.append({
                    'email': email,
                    'error': 'Invalid email format'
                })
                continue

            # Send email
            success, error = self.send_single_email(
                to_email=email,
                subject=subject,
                message=message,
                from_email=from_email,
                html_content=html_content
            )

            if success:
                success_count += 1
                logger.info(f"Progress: {index}/{total_emails} - Sent to {email}")
            else:
                failed_emails.append({
                    'email': email,
                    'error': error
                })
                logger.error(f"Progress: {index}/{total_emails} - Failed to send to {email}")

            # Batch delay to avoid rate limiting
            if index % batch_size == 0 and index < total_emails:
                logger.info(f"Batch complete. Waiting {delay_between_batches}s before next batch...")
                sleep(delay_between_batches)

        logger.info(
            f"Bulk email complete: {success_count} sent, {len(failed_emails)} failed"
        )

        return success_count, failed_emails


# Convenience functions for backward compatibility
def send_bulk_email(
        subject: str,
        message: str,
        recipient_list: List[str],
        html_content: Optional[str] = None
) -> Tuple[int, List[dict]]:
    """
    Convenience function to send bulk emails

    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient emails
        html_content: Optional HTML content

    Returns:
        Tuple of (success_count, failed_emails)
    """
    try:
        email_service = EmailService()
        return email_service.send_bulk_email(
            recipient_list=recipient_list,
            subject=subject,
            message=message,
            html_content=html_content
        )
    except Exception as e:
        logger.critical(f"Critical error in send_bulk_email: {str(e)}")
        return 0, [{'email': 'all', 'error': str(e)}]


def send_email(
        to_email: str,
        subject: str,
        message: str,
        html_content: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to send a single email

    Args:
        to_email: Recipient email
        subject: Email subject
        message: Plain text message
        html_content: Optional HTML content

    Returns:
        Tuple of (success, error_message)
    """
    try:
        email_service = EmailService()
        return email_service.send_single_email(
            to_email=to_email,
            subject=subject,
            message=message,
            html_content=html_content
        )
    except Exception as e:
        logger.critical(f"Critical error in send_email: {str(e)}")
        return False, str(e)