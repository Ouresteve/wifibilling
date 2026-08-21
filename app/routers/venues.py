from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import Venue, User
from app.schemas.schemas import VenueCreate, VenueUpdate, VenueOut
from app.core.deps import get_current_user

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