# yourapp/utils/email_helper.py

from django.core.mail import EmailMessage
from django.conf import settings

def send_custom_email(subject, body, to_emails, html_content=None, attachments=None):
    """
    Send an email using Django's EmailMessage class.

    :param subject: Email subject
    :param body: Plain text message
    :param to_emails: List of recipients
    :param html_content: Optional HTML content
    :param attachments: Optional list of file paths or (filename, content, mimetype) tuples
    """
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_emails,
    )

    if html_content:
        email.content_subtype = 'html'  # Mark body as HTML
        email.body = html_content

    if attachments:
        for attachment in attachments:
            email.attach_file(attachment) if isinstance(attachment, str) else email.attach(*attachment)

    email.send(fail_silently=False)