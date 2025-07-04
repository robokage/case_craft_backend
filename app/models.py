from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class PhoneBrand(Base):
    __tablename__ = "phone_brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    models = relationship("PhoneModel", back_populates="brand", cascade="all, delete")


class PhoneModel(Base):
    __tablename__ = "phone_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand_id = Column(Integer, ForeignKey("phone_brands.id"), nullable=False)

    phone_width = Column(Numeric(5, 2))  
    phone_height = Column(Numeric(5, 2)) 

    s3_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    brand = relationship("PhoneBrand", back_populates="models")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=True)

    auth_provider = Column(String, default="local")
    provider_user_id = Column(String, nullable=True) 

    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())