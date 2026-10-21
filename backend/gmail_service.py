"""
Gmail IMAP Ingestion and SMTP Auto-responder Service.

Monitors an inbox (e.g. aditya.krishnan2829@gmail.com) for incoming emails containing
invoice attachments (PDF, PNG, JPG), downloads the attachment, triggers the watsonx
Orchestrate IDP Pipeline, and replies back to the sender with the extraction result.
"""

import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import os
import smtplib
import ssl
from typing import Any, Callable, Dict, List, Optional, Tuple

# Load optional .env file if available
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


class GmailService:
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        imap_host: str = "imap.gmail.com",
        smtp_host: str = "smtp.gmail.com",
        imap_port: int = 993,
        smtp_port: int = 465,
    ):
        self.user = user or os.environ.get("GMAIL_USER", "aditya.krishnan2829@gmail.com")
        self.password = password or os.environ.get("GMAIL_APP_PASSWORD", "")
        self.imap_host = imap_host
        self.smtp_host = smtp_host
        self.imap_port = imap_port
        self.smtp_port = smtp_port
        self._processed_msg_ids: set = set()

    def _clean_header(self, text: Optional[str]) -> str:
        if not text:
            return ""
        decoded_parts = decode_header(text)
        res = []
        for part, enc in decoded_parts:
            if isinstance(part, bytes):
                res.append(part.decode(enc or "utf-8", errors="ignore"))
            else:
                res.append(str(part))
        return "".join(res)

    def check_for_invoice_emails(
        self, process_callback: Optional[Callable[[bytes, str, str, str], Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan UNSEEN emails in INBOX for invoice attachments (PDF, PNG, JPG).
        When found:
          1. Calls process_callback(file_bytes, filename, sender, subject)
          2. Sends an automated confirmation email back to the sender.
        """
        if not self.user or not self.password:
            raise RuntimeError("Gmail credentials (GMAIL_USER, GMAIL_APP_PASSWORD) not configured")

        context = ssl.create_default_context()
        results: List[Dict[str, Any]] = []

        with imaplib.IMAP4_SSL(self.imap_host, self.imap_port, ssl_context=context) as mail:
            mail.login(self.user, self.password)
            mail.select("INBOX")

            # Search for unread emails or emails with 'invoice' in subject
            status, data = mail.search(None, "UNSEEN")
            if status != "OK" or not data or not data[0]:
                return []

            msg_ids = data[0].split()
            for mid in msg_ids[-10:]:  # Inspect up to 10 most recent unread messages
                mid_str = mid.decode()
                if mid_str in self._processed_msg_ids:
                    continue

                res, msg_data = mail.fetch(mid, "(RFC822)")
                if res != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = self._clean_header(msg.get("Subject", "No Subject"))
                sender = self._clean_header(msg.get("From", ""))
                sender_addr = email.utils.parseaddr(sender)[1] or sender

                # Look for attachments
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" in content_disposition or part.get_filename():
                        filename = self._clean_header(part.get_filename() or "")
                        if not filename:
                            continue

                        ext = os.path.splitext(filename)[1].lower()
                        if ext in (".png", ".jpg", ".jpeg", ".pdf", ".tiff"):
                            file_bytes = part.get_payload(decode=True)
                            if not file_bytes:
                                continue

                            run_result: Dict[str, Any] = {}
                            if process_callback:
                                run_result = process_callback(file_bytes, filename, sender_addr, subject)

                            # Send email confirmation
                            self.send_confirmation_email(
                                recipient=sender_addr,
                                filename=filename,
                                subject=subject,
                                result=run_result,
                            )

                            self._processed_msg_ids.add(mid_str)
                            results.append(
                                {
                                    "status": "processed",
                                    "msg_id": mid_str,
                                    "sender": sender_addr,
                                    "subject": subject,
                                    "filename": filename,
                                    "file_size": len(file_bytes),
                                    "pipeline_result": run_result,
                                }
                            )
                            # Mark email as read/seen
                            mail.store(mid, "+FLAGS", "\\Seen")
                            break  # Process first invoice attachment in email

        return results

    def send_confirmation_email(
        self, recipient: str, filename: str, subject: str, result: Dict[str, Any]
    ) -> bool:
        """Send automated confirmation email via Gmail SMTP."""
        if not recipient or not self.user or not self.password:
            return False
        if "noreply" in recipient.lower() or "no-reply" in recipient.lower() or "mailer-daemon" in recipient.lower():
            # Skip automated bounce/noreply senders
            return False

        msg = MIMEMultipart()
        msg["From"] = f"watsonx Orchestrate IDP <{self.user}>"
        msg["To"] = recipient
        msg["Subject"] = f"Re: {subject} — Invoice Processed via watsonx Orchestrate"

        inv = result.get("invoice") or {}
        odoo_bill = result.get("odoo_bill") or {}

        inv_num = inv.get("invoice_number", "N/A")
        vendor = inv.get("vendor_name", "N/A")
        total = f"{inv.get('currency', 'USD')} {inv.get('total_amount', '0.00')}"
        tier = inv.get("approval_tier", "AUTO_APPROVED")
        odoo_id = odoo_bill.get("id") or "N/A"
        odoo_url = odoo_bill.get("odoo_url", "https://invoiceprocessing.odoo.com")

        body_html = f"""
        <html>
        <body style="font-family: -apple-system, sans-serif; color: #0f172a; line-height: 1.5;">
          <div style="border-left: 4px solid #0f62fe; padding-left: 14px; margin-bottom: 16px;">
            <h2 style="margin: 0; color: #0f62fe;">IBM watsonx Orchestrate — Intelligent Invoice Intake</h2>
            <p style="margin: 4px 0 0; color: #64748b;">Automated confirmation for attached invoice: <strong>{filename}</strong></p>
          </div>
          <table style="border-collapse: collapse; width: 100%; max-width: 580px; margin-bottom: 18px;">
            <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 8px 0; font-weight: 600; color: #475569;">Invoice Number:</td><td style="padding: 8px 0;"><strong>{inv_num}</strong></td></tr>
            <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 8px 0; font-weight: 600; color: #475569;">Vendor / Supplier:</td><td style="padding: 8px 0;">{vendor}</td></tr>
            <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 8px 0; font-weight: 600; color: #475569;">Total Amount:</td><td style="padding: 8px 0; font-weight: 700; color: #0f62fe;">{total}</td></tr>
            <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 8px 0; font-weight: 600; color: #475569;">Audit Approval Tier:</td><td style="padding: 8px 0;"><code>{tier}</code></td></tr>
            <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 8px 0; font-weight: 600; color: #475569;">Odoo ERP Vendor Bill ID:</td><td style="padding: 8px 0;">#{odoo_id}</td></tr>
          </table>
          <p><a href="{odoo_url}" style="background: #0f62fe; color: #fff; padding: 10px 16px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">View in Odoo Cloud ERP</a></p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
          <p style="font-size: 0.8rem; color: #94a3b8;">Processed autonomously by watsonx Document Understanding (docproc) + Python Logic Block + GenAI Controller.</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body_html, "html"))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                server.login(self.user, self.password)
                server.sendmail(self.user, [recipient], msg.as_string())
            return True
        except Exception:
            return False
