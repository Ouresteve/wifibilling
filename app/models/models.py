from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    #mpesa_credentials 
    mpesa_shortcode = Column(String(20), nullable=True)
    mpesa_consumer_key = Column(String(255), nullable=True)
    mpesa_consumer_secret = Column(String(255), nullable=True)
    mpesa_passkey = Column(String(255), nullable=True)

    venues = relationship("Venue", back_populates="owner")

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_name = Column(String(150), nullable=False)
    owner_phone = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)

    # M-Pesa credentials (each venue has its own)
    mpesa_shortcode = Column(String(20), nullable=True)
    mpesa_consumer_key = Column(String(255), nullable=True)
    mpesa_consumer_secret = Column(String(255), nullable=True)
    mpesa_passkey = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="venues")
    packages = relationship("Package", back_populates="venue")
    payments = relationship("Payment", back_populates="venue")
    sessions = relationship("WifiSession", back_populates="venue")


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    name = Column(String(100), nullable=False)          # e.g. "1 Hour"
    duration_minutes = Column(Integer, nullable=False)  # 60, 1440, etc.
    price = Column(Numeric(10, 2), nullable=False)      # KES
    speed_limit_kbps = Column(Integer, nullable=True)
    max_devices = Column(Integer, nullable=False, default=1)        # optional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    venue = relationship("Venue", back_populates="packages")
    payments = relationship("Payment", back_populates="package")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)

    phone_number = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)

    # M-Pesa fields
    checkout_request_id = Column(String(100), unique=True, nullable=True, index=True)
    merchant_request_id = Column(String(100), nullable=True)
    mpesa_receipt_number = Column(String(50), nullable=True)
    result_code = Column(String(10), nullable=True)
    result_desc = Column(Text, nullable=True)

    # Device info (from captive portal)
    mac_address = Column(String(30), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    venue = relationship("Venue", back_populates="payments")
    package = relationship("Package", back_populates="payments")
    session = relationship("WifiSession", back_populates="payment", uselist=False)


class WifiSession(Base):
    __tablename__ = "wifi_sessions"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), unique=True, nullable=False)

    mac_address = Column(String(30), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    username = Column(String(100), nullable=True)  # for Mikrotik user

    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    venue = relationship("Venue", back_populates="sessions")
    payment = relationship("Payment", back_populates="session")