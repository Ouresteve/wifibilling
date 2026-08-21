from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.models.models import Venue, Payment, PaymentStatus, WifiSession, User
from app.core.deps import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardSummary(BaseModel):
    total_venues: int
    total_revenue: float
    successful_payments: int
    active_sessions: int
    total_devices_online: int


class VenueStats(BaseModel):
    venue_id: int
    venue_name: str
    active_sessions: int
    revenue: float


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    venues = db.query(Venue).filter(Venue.owner_id == current_user.id).all()
    venue_ids = [v.id for v in venues]

    total_revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.venue_id.in_(venue_ids),
        Payment.status == PaymentStatus.SUCCESS
    ).scalar()

    successful_payments = db.query(func.count(Payment.id)).filter(
        Payment.venue_id.in_(venue_ids),
        Payment.status == PaymentStatus.SUCCESS
    ).scalar()

    now = datetime.now(timezone.utc)
    active_sessions = db.query(func.count(WifiSession.id)).filter(
        WifiSession.venue_id.in_(venue_ids),
        WifiSession.is_active == True,
        WifiSession.expires_at > now
    ).scalar()

    return DashboardSummary(
        total_venues=len(venues),
        total_revenue=float(total_revenue or 0),
        successful_payments=successful_payments or 0,
        active_sessions=active_sessions or 0,
        total_devices_online=active_sessions or 0
    )


@router.get("/venues-stats", response_model=List[VenueStats])
def get_venues_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    venues = db.query(Venue).filter(Venue.owner_id == current_user.id).all()
    now = datetime.now(timezone.utc)
    result = []

    for venue in venues:
        active = db.query(func.count(WifiSession.id)).filter(
            WifiSession.venue_id == venue.id,
            WifiSession.is_active == True,
            WifiSession.expires_at > now
        ).scalar() or 0

        revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            Payment.venue_id == venue.id,
            Payment.status == PaymentStatus.SUCCESS
        ).scalar() or 0

        result.append(VenueStats(
            venue_id=venue.id,
            venue_name=venue.name,
            active_sessions=active,
            revenue=float(revenue)
        ))

    return result