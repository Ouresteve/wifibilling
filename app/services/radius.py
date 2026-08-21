import secrets
import string
from sqlalchemy.orm import Session
from app.models.radius import RadCheck, RadReply


def generate_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_radius_user(
    db: Session,
    username: str,
    password: str,
    session_timeout: int,          # in seconds
    max_devices: int = 1
):
    """
    Create a RADIUS user with password, session timeout and device limit.
    """

    # Remove old entries for this username (in case of re-purchase)
    db.query(RadCheck).filter(RadCheck.username == username).delete()
    db.query(RadReply).filter(RadReply.username == username).delete()

    # Password
    db.add(RadCheck(
        username=username,
        attribute="Cleartext-Password",
        op=":=",
        value=password
    ))

    # Session Timeout (seconds)
    db.add(RadReply(
        username=username,
        attribute="Session-Timeout",
        op=":=",
        value=str(session_timeout)
    ))

    # Device limit
    db.add(RadReply(
        username=username,
        attribute="Simultaneous-Use",
        op=":=",
        value=str(max_devices)
    ))

    db.commit()
    return True


def delete_radius_user(db: Session, username: str):
    db.query(RadCheck).filter(RadCheck.username == username).delete()
    db.query(RadReply).filter(RadReply.username == username).delete()
    db.commit()