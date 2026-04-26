"""
SQLAlchemy Models
Defines the database schema for the records table.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func
from database import Base

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(120), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    category = Column(String(50), nullable=False, index=True)
    amount = Column(Float, nullable=True, default=0.0)
    date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Record(id={self.id}, name='{self.name}', category='{self.category}')>"
