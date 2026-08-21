from sqlalchemy import Column, Integer, String, BigInteger
from app.radius_database import radius_engine
from sqlalchemy.ext.declarative import declarative_base

RadiusBase = declarative_base()


class RadCheck(RadiusBase):
    __tablename__ = "radcheck"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False, default=":=")
    value = Column(String(253), nullable=False)


class RadReply(RadiusBase):
    __tablename__ = "radreply"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False, default=":=")
    value = Column(String(253), nullable=False)