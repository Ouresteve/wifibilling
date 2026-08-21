from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Venue, Package

router = APIRouter(tags=["Portal"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/portal/{venue_slug}", response_class=HTMLResponse)
def captive_portal(venue_slug: str, request: Request, db: Session = Depends(get_db)):
    venue = db.query(Venue).filter(
        Venue.slug == venue_slug,
        Venue.is_active == True
    ).first()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    packages = db.query(Package).filter(
        Package.venue_id == venue.id,
        Package.is_active == True
    ).order_by(Package.price).all()

    return templates.TemplateResponse(
        request=request,
        name="portal.html",
        context={
            "venue": venue,
            "packages": packages
        }
    )