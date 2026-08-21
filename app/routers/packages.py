from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Package, Venue, User
from app.schemas.schemas import PackageCreate, PackageUpdate, PackageOut
from app.core.deps import get_current_user

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.post("/", response_model=PackageOut, status_code=status.HTTP_201_CREATED)
def create_package(
    package: PackageCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check that venue belongs to the current user
    venue = db.query(Venue).filter(
        Venue.id == package.venue_id,
        Venue.owner_id == current_user.id
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    db_package = Package(**package.model_dump())
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    return db_package


@router.get("/", response_model=List[PackageOut])
def list_packages(
    venue_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    query = db.query(Package).join(Venue).filter(Venue.owner_id == current_user.id)
    if venue_id:
        query = query.filter(Package.venue_id == venue_id)

    packages = query.all()
    return packages


@router.get("/{package_id}", response_model=PackageOut)
def get_package(
    package_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    package = db.query(Package).join(Venue).filter(
        Package.id == package_id,
        Venue.owner_id == current_user.id
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


@router.patch("/{package_id}", response_model=PackageOut)
def update_package(
    package_id: int, 
    package_update: PackageUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    package = db.query(Package).join(Venue).filter(
        Package.id == package_id,
        Venue.owner_id == current_user.id
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    update_data = package_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(package, key, value)

    db.commit()
    db.refresh(package)
    return package




@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    package = db.query(Package).join(Venue).filter(
        Package.id == package_id,
        Venue.owner_id == current_user.id
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    db.delete(package)
    db.commit()
    return None