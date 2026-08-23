from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import Venue, User, Package
from app.schemas.schemas import VenueCreate, VenueUpdate, VenueOut
from app.core.deps import get_current_user

from pydantic import BaseModel
from app.config import get_settings


class VenueSetupInfo(BaseModel):
    portal_path: str
    radius_server: str
    radius_secret: str
    radius_auth_port: int = 1812
    radius_acct_port: int = 1813
    payments_configured: bool
    packages_count: int


router = APIRouter(prefix="/venues", tags=["Venues"])


@router.post("/", response_model=VenueOut, status_code=status.HTTP_201_CREATED)
def create_venue(
    venue: VenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    # Check if slug already exists
    existing = db.query(Venue).filter(Venue.slug == venue.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue with this slug already exists"
        )

    db_venue = Venue(
        **venue.model_dump(),
        owner_id=current_user.id,
        owner_name=current_user.full_name,
        owner_phone=current_user.phone
    )
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue

@router.get("/", response_model=List[VenueOut])
def list_venues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    venues = db.query(Venue).filter(Venue.owner_id == current_user.id).all()
    return venues


@router.get("/{venue_id}", response_model=VenueOut)
def get_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.owner_id == current_user.id
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.patch("/{venue_id}", response_model=VenueOut)
def update_venue(
    venue_id: int,
    venue_update: VenueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.owner_id == current_user.id
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    update_data = venue_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(venue, key, value)

    db.commit()
    db.refresh(venue)
    return venue



@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.owner_id == current_user.id
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    db.delete(venue)
    db.commit()
    return None





@router.get("/{venue_id}/setup", response_model=VenueSetupInfo)
def get_venue_setup(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.owner_id == current_user.id,
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    packages_count = db.query(Package).filter(
        Package.venue_id == venue.id,
        Package.is_active == True,
    ).count()

    owner = current_user
    payments_configured = bool(
        owner.mpesa_shortcode
        and owner.mpesa_consumer_key
        and owner.mpesa_consumer_secret
        and owner.mpesa_passkey
    )

    settings = get_settings()

    return VenueSetupInfo(
        portal_path=f"/portal/{venue.slug}",
        # Placeholder until you deploy — replace with real VPS IP later
        radius_server=getattr(settings, "RADIUS_PUBLIC_HOST", "YOUR_VPS_IP"),
        radius_secret=getattr(settings, "RADIUS_SECRET", "testing123"),
        payments_configured=payments_configured,
        packages_count=packages_count,
    )