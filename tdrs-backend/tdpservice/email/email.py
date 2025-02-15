"""Wrapper to send emails with Django."""

from celery import shared_task
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import get_template
from django.contrib.admin.models import LogEntry, ContentType, CHANGE

import logging

logger = logging.getLogger()


def log(msg, logger_context=None, level='info'):
    """Create a log in the terminal and django admin console, for email tasks."""
    from tdpservice.users.models import User

    log_func = logger.info

    match level:
        case 'info':
            log_func = logger.info
        case 'warn':
            log_func = logger.warn
        case 'error':
            log_func = logger.error
        case 'critical':
            log_func = logger.critical
        case 'exception':
            log_func = logger.exception

    log_func(msg)

    if logger_context:
        LogEntry.objects.log_action(
            user_id=logger_context['user_id'],
            change_message=msg,
            action_flag=CHANGE,
            content_type_id=ContentType.objects.get_for_model(User).pk,
            object_id=logger_context['object_id'],
            object_repr=logger_context['object_repr']
        )


@shared_task
def automated_email(email_path, recipient_email, subject, email_context, text_message, logger_context=None):
    """
    Send email to user.

    recipient_email can be either a string (single recipient) or a array of strings.
    """
    recipients = [recipient_email] if type(recipient_email) == str else recipient_email
    logger.info(f"Starting celery task to send email to {recipients}")

    html_message = get_template(email_path).render(email_context)
    valid_emails = filter_valid_emails(recipients, logger_context)

    try:
        send_email(subject, text_message, html_message, valid_emails)
        log(
            f"Email sent to {valid_emails} with subject \"{subject}\".",
            logger_context=logger_context
        )
    except Exception:
        log(
            f'Emails were attempted to the following email list {valid_emails}, but none were sent.',
            logger_context=logger_context
        )


def send_email(subject, message, html_message, recipient_list):
    """Send an email to a list of recipients."""
    email = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=recipient_list,
    )
    email.attach_alternative(html_message, "text/html")

    num_emails_sent = email.send()
    if num_emails_sent == 0:
        raise Exception(
            f"Emails were attempted to the following email list: {recipient_list}. \
        But none were sent. They may be invalid."
        )


def filter_valid_emails(emails, logger_context=None):
    """Validate email addresses."""
    valid_emails = []
    for email in emails:
        try:
            validate_email(email)
            valid_emails.append(email)
        except ValidationError:
            log(
                f"{email} is not a valid email address. An email will not be sent to this address.",
                logger_context=logger_context
            )
    if len(valid_emails) == 0:
        raise ValidationError("No valid emails provided.")

    return valid_emails
