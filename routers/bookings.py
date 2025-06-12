from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import exc

from modelsDB.database import get_db
from services.booking_service import BookingService
from schemas.booking_schema import (
    Booking as BookingSchema,
    BookingBase
)
from utils.logger import logger

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    responses={
        404: {"description": "Booking not found"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"}
    }
)

@router.post("/", response_model=BookingSchema)
def create_booking(
    booking_data: BookingBase,
    db: Session = Depends(get_db)
):
    """
    Create a new booking for a fitness class.
    
    Args:
        booking_data: The booking data including class_id, client_name, and client_email
        db: Database session
        
    Returns:
        The created booking with class details
        
    Raises:
        HTTPException: If class is full, not found, or booking creation fails
    """
    logger.info(f"Creating booking for class {booking_data.class_id} by {booking_data.client_email}")
    logger.debug(f"Booking details: {booking_data}")
    
    try:
        booking_service = BookingService(db)
        new_booking = booking_service.create_booking(booking_data)
        logger.info(f"Successfully created booking with ID: {new_booking.id}")
        return new_booking
        
    except HTTPException as e:
        logger.error(f"Booking creation failed: {str(e)}")
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error during booking creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error during booking creation: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/", response_model=List[BookingSchema])
def get_bookings(
    x_client_email: str = Header(..., example="client@example.com", description="Client's email address"),
    status: Optional[str] = Query(None, description="Filter by booking status"),
    db: Session = Depends(get_db)
):
    """
    Get all bookings for a specific client (via email header), optionally filtered by booking status.
    
    Args:
        x_client_email: Email from request header
        status: Optional filter by booking status (e.g., confirmed, cancelled)
        db: Database session
        
    Returns:
        List of bookings with class details
        
    Raises:
        HTTPException: If email is invalid, or database errors occur
    """
    logger.info(f"Fetching bookings for client: {x_client_email}, status filter: {status}")
    
    try:
        # Validate email format
        if not x_client_email or '@' not in x_client_email:
            logger.warning(f"Invalid email format: {x_client_email}")
            raise HTTPException(status_code=400, detail="Invalid email format in header")
        
        booking_service = BookingService(db)
        bookings = booking_service.get_bookings_by_email(x_client_email.lower(), status)
        
        if not bookings:
            logger.info(f"No bookings found for {x_client_email}")
            raise HTTPException(status_code=404, detail="No bookings found for this email")

        logger.info(f"Successfully retrieved {len(bookings)} bookings for {x_client_email}")
        return bookings
        
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")