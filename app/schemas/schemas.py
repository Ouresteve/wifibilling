from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.models import PaymentStatus


# ========== Auth ==========
class UserCreate(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ========== Venue ==========
class VenueBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9\-]+$")
    

class VenueCreate(VenueBase):
    
    mpesa_shortcode: Optional[str] = None
    mpesa_consumer_key: Optional[str] = None
    mpesa_consumer_secret: Optional[str] = None
    mpesa_passkey: Optional[str] = None


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    owner_name: Optional[str] = Field(None, min_length=2, max_length=150)
    owner_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    is_active: Optional[bool] = None
    mpesa_shortcode: Optional[str] = None
    mpesa_consumer_key: Optional[str] = None
    mpesa_consumer_secret: Optional[str] = None
    mpesa_passkey: Optional[str] = None


class VenueOut(VenueBase):
    id: int
    owner_name: str
    owner_phone: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ========== Package ==========
class PackageBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    duration_minutes: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    speed_limit_kbps: Optional[int] = Field(None, gt=0)
    max_devices: int = Field(1, ge=1, le=10)  # optional, default 1


class PackageCreate(PackageBase):
    venue_id: int


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, gt=0)
    speed_limit_kbps: Optional[int] = Field(None, gt=0)
    max_devices: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class PackageOut(PackageBase):
    id: int
    venue_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== Payment ==========
class STKPushRequest(BaseModel):
    venue_id: int
    package_id: int
    phone_number: str = Field(..., min_length=10, max_length=15)
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    venue_id: int
    package_id: int
    phone_number: str
    amount: Decimal
    status: PaymentStatus
    checkout_request_id: Optional[str] = None
    mpesa_receipt_number: Optional[str] = None
    mac_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class STKPushResponse(BaseModel):
    message: str
    payment_id: int
    checkout_request_id: Optional[str] = None
    merchant_request_id: Optional[str] = None
    customer_message: Optional[str] = None




class MpesaSettingsUpdate(BaseModel):
    mpesa_shortcode: Optional[str] = None
    mpesa_consumer_key: Optional[str] = None
    mpesa_consumer_secret: Optional[str] = None
    mpesa_passkey: Optional[str] = None


class MpesaSettingsOut(BaseModel):
    mpesa_shortcode: Optional[str] = None
    mpesa_consumer_key: Optional[str] = None
    # We deliberately do NOT return the secret or passkey for security
    has_consumer_secret: bool = False
    has_passkey: bool = False
    is_configured: bool = False

    model_config = ConfigDict(from_attributes=True)