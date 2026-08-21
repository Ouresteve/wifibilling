from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

radius_engine = create_engine(settings.RADIUS_DATABASE_URL)
RadiusSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=radius_engine)


def get_radius_db():
    db = RadiusSessionLocal()
    try:
        yield db
    finally:
        db.close()