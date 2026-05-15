import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_report(
    html_body: str,
    gmail_user: str,
    gmail_app_password: str,
    recipient: str,
) -> None:
    """
    Send the HTML report via Gmail SMTP.
    Requires a Gmail App Password (not your regular Gmail password).
    Generate one at: myaccount.google.com → Security → App passwords
    """
    week_num = datetime.now().strftime("%W")
    subject = f"Week {week_num} training report"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = recipient

    # Plain text fallback
    plain = f"Your week {week_num} training report is best viewed in an HTML-capable email client."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, recipient, msg.as_string())

    print(f"✅ Report sent to {recipient}")
