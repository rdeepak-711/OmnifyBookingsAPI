from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator
from modelsDB.models import ClassType
from config import BOOKING_ALLOWED_STATUSES

# Base schema with common attributes
class BookingBase(BaseModel):
    class_id: int = Field(..., gt=0)
    client_name: str
    client_email: EmailStr = Field(..., min_length=1, max_length=100)

    @validator('client_name')
    def name_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Client name cannot be blank")
        return v

# Schema for updating an existing booking
class BookingUpdate(BaseModel):
    status: Optional[str] = None

# Schema for booking response
class Booking(BookingBase):
    id: int
    booking_time: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Class details (from related FitnessClass)
    class_name: str
    class_type: ClassType
    instructor: str
    start_time: datetime
    end_time: datetime
    timezone: str

    class Config:
        from_attributes = True