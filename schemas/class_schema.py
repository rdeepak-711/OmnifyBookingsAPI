from datetime import datetime
from pydantic import BaseModel, Field, validator
import pytz

from config import DEFAULT_TIMEZONE
from modelsDB.models import ClassType, ClassStatus

# Base schema with common attributes
class FitnessClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    class_type: ClassType  # Changed to use the enum
    instructor: str = Field(..., min_length=1, max_length=100)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(..., gt=0)
    timezone: str = Field(default=DEFAULT_TIMEZONE)
    status: ClassStatus = Field(default=ClassStatus.UPCOMING) 

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        try:
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {v}")

# Schema for class response
class FitnessClass(FitnessClassBase):
    id: int
    available_slots: int = Field(..., ge=0)  # Ensure available slots are non-negative
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
