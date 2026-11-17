import logging
import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from email.utils import formataddr
from html import escape

from sqlalchemy import event
from sqlalchemy.orm import Session

from models.models import Package, PackageStatus

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST") or "mailpit"
SMTP_PORT = int(os.getenv("SMTP_PORT") or 1025)
SMTP_USER = os.getenv("SMTP_USER") or None
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or None
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME") or "Pagyar Mosta Zrt."
# A Gmail csak a saját címéről enged küldeni, ezért ilyenkor az a feladó.
MAIL_FROM = SMTP_USER or "noreply@pagyarmosta.hu"

STATUS_LABELS: dict[PackageStatus, str] = {
    PackageStatus.CREATED: "Előjegyezve",
    PackageStatus.READY_FOR_PICKUP: "Felvételre kész",
    PackageStatus.ASSIGNED_FOR_PICKUP: "Futár kijelölve a felvételhez",
    PackageStatus.OUT_FOR_PICKUP: "A futár úton van a csomagért",
    PackageStatus.PICKED_UP: "Felvéve",
    PackageStatus.IN_WAREHOUSE: "Raktárban",
    PackageStatus.ASSIGNED_FOR_DELIVERY: "Futár kijelölve a kiszállításhoz",
    PackageStatus.OUT_FOR_DELIVERY: "Kiszállítás alatt",
    PackageStatus.DELIVERED: "Kézbesítve",
    PackageStatus.FAILED_DELIVERY: "Sikertelen kézbesítés",
    PackageStatus.RETURNED_TO_SENDER: "Visszaküldve a feladónak",
    PackageStatus.CANCELLED: "Törölve",
}

_PENDING_KEY = "pending_emails"
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="email")

def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    """Egy levél elküldése SMTP-n. Hiba esetén kivételt dob."""
    msg = EmailMessage()
    msg["From"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        if SMTP_USER:  # Gmail: titkosított kapcsolat + bejelentkezés
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def _send_safely(mail: dict) -> None:
    try:
        send_email(**mail)
    except Exception:
        logger.exception("Nem sikerült elküldeni az e-mailt ide: %s", mail.get("to"))


def _build_mail(package: Package, new_status: PackageStatus) -> dict | None:
    contact = package.delivery_contact
    if contact is None or not contact.email:
        return None

    tracking = str(package.tracking_id)
    label = STATUS_LABELS.get(new_status, new_status.value)

    if new_status == PackageStatus.CREATED:
        subject = "Csomagot adtak fel Önnek"
        lead = "Csomagot adtak fel az Ön részére."
        sender = package.pickup_contact.name if package.pickup_contact else "—"
        rows = [
            ("Követési azonosító", tracking),
            ("Feladó", sender),
            ("Méret", package.size),
            ("Tervezett felvétel", f"{package.pickup_date} ({package.pickup_time_slot})"),
        ]
    else:
        subject = f"Csomagja új állapota: {label}"
        lead = "Csomagja állapota megváltozott."
        rows = [
            ("Követési azonosító", tracking),
            ("Új állapot", label),
        ]

    greeting = f"Kedves {contact.name}!"
    closing = "Üdvözlettel:\nPagyar Mosta Zrt.\n„…ahol csomagja valamikor biztos célba ér!”"

    text = "\n".join(
        [greeting, "", lead, ""]
        + [f"{key}: {value}" for key, value in rows]
        + ["", closing]
    )

    table = "".join(
        f"<tr><td style='padding:4px 16px 4px 0;color:#666'>{escape(key)}</td>"
        f"<td style='padding:4px 0'><b>{escape(str(value))}</b></td></tr>"
        for key, value in rows
    )
    html = (
        "<div style='font-family:Arial,sans-serif;font-size:14px;color:#222'>"
        f"<p>{escape(greeting)}</p><p>{escape(lead)}</p>"
        f"<table>{table}</table>"
        f"<p style='margin-top:24px'>{escape(closing).replace(chr(10), '<br>')}</p>"
        "</div>"
    )

    return {"to": contact.email, "subject": subject, "text": text, "html": html}

def queue_notification(db: Session, package: Package, new_status: PackageStatus) -> None:
    """Értesítés félretétele; csak sikeres commit után megy ki.

    A hívás előtt a csomagnak flush-olva kell lennie (legyen tracking_id
    és betölthető delivery_contact).
    """
    mail = _build_mail(package, new_status)
    if mail:
        db.info.setdefault(_PENDING_KEY, []).append(mail)


@event.listens_for(Session, "after_commit")
def _send_pending(session: Session) -> None:
    for mail in session.info.pop(_PENDING_KEY, []):
        _executor.submit(_send_safely, mail)


@event.listens_for(Session, "after_rollback")
def _drop_pending(session: Session) -> None:
    session.info.pop(_PENDING_KEY, None)