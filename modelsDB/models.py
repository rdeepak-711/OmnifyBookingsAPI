from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from modelsDB.base import Base
from config import DEFAULT_TIMEZONE

class ClassType(str, enum.Enum):
    YOGA = "yoga"
    ZUMBA = "zumba"
    HIIT = "hiit"

class ClassStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"

class FitnessClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    class_type = Column(Enum(ClassType))
    instructor = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    capacity = Column(Integer)
    available_slots = Column(Integer)
    status = Column(Enum(ClassStatus), default=ClassStatus.UPCOMING)
    timezone = Column(String, default=DEFAULT_TIMEZONE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with bookings
    bookings = relationship("Booking", back_populates="fitness_class")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    client_name = Column(String)
    client_email = Column(String, index=True)
    booking_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # confirmed, cancelled, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with fitness class
    fitness_class = relationship("FitnessClass", back_populates="bookings") 