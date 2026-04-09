"""
SMTP email sender — send auto-replies directly from the app.
Supports Gmail SMTP (app password) and generic SMTP.
"""
from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_reply(
    smtp_host: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
    recipient: str,
    subject: str,
    body: str,
    use_tls: bool = True,
) -> tuple[bool, str]:
    """
    Send an email reply via SMTP.
    Returns (success: bool, message: str)
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Re: {subject}"
        msg["From"]    = sender_email
        msg["To"]      = recipient
        msg.attach(MIMEText(body, "plain"))

        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)

        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        return True, "Reply sent successfully."
    except Exception as e:
        return False, str(e)
