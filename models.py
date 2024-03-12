from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
from pydantic import BaseModel
from sqlalchemy import create_engine
import os
from typing import List, Optional


basedir = os.path.abspath(os.path.dirname(__file__))


DATABASE_URL = "sqlite:///" + os.path.join(basedir, "database.db")

database = Database(DATABASE_URL)

Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DownloadURLs(Base):
    __tablename__ = "download_urls"
    id = Column(Integer, primary_key=True, index=True)
    windows = Column(String(255))
    mac = Column(String(255))
    linux = Column(String(255))
    android = Column(String(255))
    ios = Column(String(255))
    vpn_id = Column(Integer, ForeignKey("vpn_apps.id"))
    vpn = relationship("VPN", back_populates="download_urls")


class VPN(Base):
    __tablename__ = "vpn_apps"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), unique=True)
    name = Column(String(50), unique=True)
    description_text = Column(Text)
    description_html = Column(Text)
    supported_os = Column(String(255))
    website_url = Column(String(255))
    is_free = Column(Boolean)
    rate = Column(Integer)
    download_urls = relationship("DownloadURLs", back_populates="vpn")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    email = Column(String(120), unique=True)
    telegram_id = Column(Integer, unique=True)


# pydantic models
class UserCreate(BaseModel):
    telegram_id: int


class DownloadURLsCreate(BaseModel):
    windows: Optional[List[str]] = None
    mac: Optional[List[str]] = None
    linux: Optional[List[str]] = None
    android: Optional[List[str]] = None
    ios: Optional[List[str]] = None


class VPNCreate(BaseModel):
    name: str
    title: Optional[str] = None
    description_text: Optional[str] = None
    description_html: Optional[str] = None
    website_url: Optional[str] = None
    is_free: Optional[bool] = None
    rate: Optional[int] = None
    supported_os: List[str]
    download_urls: DownloadURLsCreate


class DownloadURLsCreate(BaseModel):
    windows: List[str]
    mac: List[str]
    linux: List[str]
    android: List[str]
    ios: List[str]


from sqlalchemy.orm import Session


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
