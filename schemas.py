"""
Pydantic Schemas
Validates incoming/outgoing data.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class RecordBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    category: str = Field(..., min_length=1, max_length=50, description="Category")
    amount: Optional[float] = Field(0.0, ge=0, description="Amount/value")
    date: Optional[datetime] = Field(None, description="Record date")
    status: str = Field("active", pattern="^(active|inactive|pending)$")
    notes: Optional[str] = Field(None, max_length=1000)

class RecordCreate(RecordBase):
    pass

class RecordUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    amount: Optional[float] = Field(None, ge=0)
    date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|pending)$")
    notes: Optional[str] = Field(None, max_length=1000)

class RecordResponse(RecordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
