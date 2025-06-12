from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import desc, exc
import logging

from modelsDB.models import Booking
from schemas.booking_schema import BookingBase, BookingUpdate, Booking as BookingSchema
from services.class_service import ClassService
from config import BOOKING_ALLOWED_STATUSES

logger = logging.getLogger(__name__)

class BookingService:
    """
    Service class for handling booking operations.
    
    This service manages all booking-related operations including:
    - Creating new bookings
    - Updating booking status
    - Managing class capacity
    - Retrieving booking information
    """
    
    def __init__(self, db: Session):
        """
        Initialize the booking service.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
        self.class_service = ClassService(db)
        logger.debug("BookingService initialized with database session")

    def create_booking(self, booking_data: BookingBase) -> BookingSchema:
        """
        Create a new booking for a fitness class.
        
        Args:
            booking_data (BookingCreate): Booking data including class_id, client info
            
        Returns:
            BookingSchema: The created booking object with class details
            
        Raises:
            HTTPException: If class is full, not found, or booking creation fails
        """
        try:
            # First update all class statuses to ensure we have the latest status
            self.class_service.update_classes_status()
            logger.debug("Updated class statuses before creating booking")

            # Check if class exists and has available slots
            try:
                class_obj = self.class_service.get_class(booking_data.class_id)
            except HTTPException as e:
                logger.error(f"Class not found: {str(e)}")
                raise HTTPException(status_code=404, detail=f"Class with ID {booking_data.class_id} not found")
            
            # Validate class status
            if class_obj.status != "upcoming":
                logger.warning(f"Attempted to book class with invalid status: {class_obj.status}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot book a class with status: {class_obj.status}"
                )
            
            # Check available slots
            if class_obj.available_slots <= 0:
                logger.warning(f"Attempted to book class with no available slots: {class_obj.id}")
                raise HTTPException(
                    status_code=400, 
                    detail="No available slots in this class"
                )
            
            existing_booking = self.db.query(Booking).filter(
                Booking.class_id == booking_data.class_id,
                Booking.client_email == booking_data.client_email.lower(),
            ).first()

            if existing_booking:
                raise HTTPException(
                    status_code=409,
                    detail="You have already booked this class."
            )

            # Create new booking
            new_booking = Booking(
                class_id=booking_data.class_id,
                client_name=booking_data.client_name,
                client_email=booking_data.client_email.lower(),
                booking_time=datetime.utcnow(),
                status="confirmed"
            )

            try:
                # Update available slots
                self.class_service.update_available_slots(booking_data.class_id, -1)
                logger.debug(f"Updated available slots for class {booking_data.class_id}")

                # Save booking
                self.db.add(new_booking)
                self.db.commit()
                self.db.refresh(new_booking)
                logger.debug(f"Created new booking with ID: {new_booking.id}")
                
            except exc.SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database error while creating booking: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to create booking")

            # Create response with class details
            return BookingSchema(
                id=new_booking.id,
                class_id=new_booking.class_id,
                client_name=new_booking.client_name,
                client_email=new_booking.client_email,
                booking_time=new_booking.booking_time,
                status=new_booking.status,
                created_at=new_booking.created_at,
                updated_at=new_booking.updated_at,
                class_name=class_obj.name,
                class_type=class_obj.class_type,
                instructor=class_obj.instructor,
                start_time=class_obj.start_time,
                end_time=class_obj.end_time,
                timezone=class_obj.timezone
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_booking: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def get_bookings_by_email(self, email: str, status: Optional[str] = None) -> List[BookingSchema]:
        """
        Fetch all bookings for a given client email, optionally filtering by status.
        
        Args:
            email (str): Client email (assumed normalized to lowercase)
            status (Optional[str]): Optional status to filter by
            
        Returns:
            List[BookingSchema]: Bookings with class details
            
        Raises:
            HTTPException: If any error occurs
        """
        try:
            if not email or '@' not in email:
                logger.warning(f"Invalid email format: {email}")
                raise HTTPException(status_code=400, detail="Invalid email format")

            # Build base query
            query = self.db.query(Booking).filter(Booking.client_email == email)

            if status:
                query = query.filter(Booking.status == status)

            bookings = query.order_by(desc(Booking.booking_time)).all()
            logger.debug(f"Found {len(bookings)} bookings for email {email} with status={status}")

            # Map bookings with class details
            result = []
            for booking in bookings:
                try:
                    class_obj = self.class_service.get_class(booking.class_id)
                    result.append(BookingSchema(
                        id=booking.id,
                        class_id=booking.class_id,
                        client_name=booking.client_name,
                        client_email=booking.client_email,
                        booking_time=booking.booking_time,
                        status=booking.status,
                        created_at=booking.created_at,
                        updated_at=booking.updated_at,
                        class_name=class_obj.name,
                        class_type=class_obj.class_type,
                        instructor=class_obj.instructor,
                        start_time=class_obj.start_time,
                        end_time=class_obj.end_time,
                        timezone=class_obj.timezone
                    ))
                except HTTPException as e:
                    logger.error(f"Skipping booking {booking.id} due to class error: {str(e)}")
                    continue
            
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_bookings_by_email: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
        
    def get_booking(self, booking_id: int) -> Booking:
        """
        Get a booking by its ID.
        
        Args:
            booking_id (int): ID of the booking
            
        Returns:
            Booking: The booking object
            
        Raises:
            HTTPException: If booking is not found or there's a database error
        """
        try:
            # Validate booking ID
            if not booking_id or booking_id <= 0:
                logger.warning(f"Invalid booking ID: {booking_id}")
                raise HTTPException(status_code=400, detail="Invalid booking ID")

            try:
                booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
            except exc.SQLAlchemyError as e:
                logger.error(f"Database error while fetching booking: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to fetch booking")

            if not booking:
                logger.warning(f"Booking not found with ID: {booking_id}")
                raise HTTPException(status_code=404, detail="Booking not found")

            return booking
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_booking: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def update_booking_status(self, booking_id: int, booking_data: BookingUpdate) -> Booking:
        """
        Update a booking's status.
        
        Args:
            booking_id (int): ID of the booking to update
            booking_data (BookingUpdate): New booking data
            
        Returns:
            Booking: The updated booking object
            
        Raises:
            HTTPException: If booking is not found, status change is invalid, or there's a database error
        """
        try:
            # Get existing booking
            booking = self.get_booking(booking_id)
            
            # Handle status changes
            if booking_data.status and booking_data.status != booking.status:
                # Validate status change
                if booking_data.status not in BOOKING_ALLOWED_STATUSES:
                    logger.warning(f"Invalid status change attempted: {booking_data.status}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status. Must be one of: {BOOKING_ALLOWED_STATUSES}"
                    )
                
                try:
                    # Handle slot management
                    if booking_data.status == "cancelled" and booking.status == "confirmed":
                        # Increase available slots when cancelling
                        self.class_service.update_available_slots(booking.class_id, 1)
                        logger.debug(f"Increased available slots for class {booking.class_id}")
                    elif booking_data.status == "confirmed" and booking.status == "cancelled":
                        # Check if slots are available before re-confirming
                        class_obj = self.class_service.get_class(booking.class_id)
                        if class_obj.available_slots <= 0:
                            logger.warning(f"Cannot re-confirm booking: no available slots in class {booking.class_id}")
                            raise HTTPException(
                                status_code=400,
                                detail="Cannot re-confirm booking: no available slots"
                            )
                        # Decrease available slots when re-confirming
                        self.class_service.update_available_slots(booking.class_id, -1)
                        logger.debug(f"Decreased available slots for class {booking.class_id}")
                except HTTPException as e:
                    logger.error(f"Error updating class slots: {str(e)}")
                    raise

            try:
                # Update fields
                update_data = booking_data.dict(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(booking, field, value)

                self.db.commit()
                self.db.refresh(booking)
                logger.debug(f"Updated booking {booking_id}")
                return booking
                
            except exc.SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database error while updating booking: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to update booking")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update_booking: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def delete_booking(self, booking_id: int) -> bool:
        """
        Delete a booking and update class capacity.
        
        Args:
            booking_id (int): ID of the booking to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If booking is not found or there's a database error
        """
        try:
            # Get existing booking
            booking = self.get_booking(booking_id)
            
            try:
                # If booking was confirmed, increase available slots
                if booking.status == "confirmed":
                    self.class_service.update_available_slots(booking.class_id, 1)
                    logger.debug(f"Increased available slots for class {booking.class_id}")
                
                self.db.delete(booking)
                self.db.commit()
                logger.debug(f"Deleted booking {booking_id}")
                return True
                
            except exc.SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Database error while deleting booking: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to delete booking")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_booking: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")