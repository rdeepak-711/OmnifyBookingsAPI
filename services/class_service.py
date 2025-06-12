import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, exc
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from modelsDB.models import FitnessClass, ClassType, ClassStatus
from config import CLASS_ALLOWED_STATUSES, DEFAULT_TIMEZONE
from schemas.class_schema import FitnessClassBase
from utils.timezone_utils import (
    convert_to_timezone,
    get_timezone
)

logger = logging.getLogger(__name__)

class ClassService:
    """
    Service class for managing fitness classes.
    
    This service handles all class-related operations including:
    - Class status management (upcoming, active, completed)
    - Class capacity and slot management
    - CRUD operations for classes
    - Time-based status transitions
    """
    
    def __init__(self, db: Session):
        """
        Initialize the class service.
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db
        logger.debug("ClassService initialized with database session")

    def create_class(self, class_data: FitnessClassBase) -> FitnessClass:
        """
        Create a new fitness class with enhanced validation.
        
        Args:
            class_data: The class data to create
            
        Returns:
            The created fitness class
            
        Raises:
            HTTPException: 
                - 400: Invalid timezone
                - 400: Invalid class type
                - 400: Invalid time configurations
                - 400: Invalid status
                - 500: Database error
        """
        logger.debug(f"Creating new class with data: {class_data}")
        
        try:
            # Validate timezone
            try:
                get_timezone(class_data.timezone)
            except ValueError as e:
                logger.warning(f"Invalid timezone: {class_data.timezone}")
                raise HTTPException(status_code=400, detail=str(e))
            
            # Validate class type
            if class_data.class_type not in ClassType:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid class type. Must be one of: {[type.value for type in ClassType]}"
                )

            # Validate status
            if class_data.status not in ClassStatus:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {[status.value for status in ClassStatus]}"
                )

            # Convert times to specified timezone
            start_time = convert_to_timezone(
                class_data.start_time,
                class_data.timezone
            )
            end_time = convert_to_timezone(
                class_data.end_time,
                class_data.timezone
            )

            # Check for duplicate class (same name and overlapping time)
            existing_class = self.db.query(FitnessClass).filter(
                FitnessClass.name == class_data.name,
                FitnessClass.start_time < end_time,
                FitnessClass.end_time > start_time
            ).first()

            if existing_class:
                raise HTTPException(
                    status_code=409,
                    detail="A class with the same name and overlapping time already exists."
                )


            # Validate time configurations
            current_time = datetime.utcnow()
            
            # Check if created_at is after start or end time
            if hasattr(class_data, 'created_at') and class_data.created_at:
                if class_data.created_at > start_time or class_data.created_at > end_time:
                    raise HTTPException(
                        status_code=400,
                        detail="created_at cannot be after start_time or end_time"
                    )

            # Validate minimum class duration (e.g., 30 minutes)
            min_duration = 30  # minutes
            if (end_time - start_time).total_seconds() / 60 < min_duration:
                raise HTTPException(
                    status_code=400,
                    detail=f"Class duration must be at least {min_duration} minutes"
                )

            # Create new class (removed available_slots from input)
            new_class = FitnessClass(
                name=class_data.name,
                class_type=class_data.class_type,
                instructor=class_data.instructor,
                start_time=start_time,
                end_time=end_time,
                capacity=class_data.capacity,
                available_slots=class_data.capacity,  # Set equal to capacity
                status=class_data.status,
                timezone=class_data.timezone
            )
            
            # Add to database
            self.db.add(new_class)
            self.db.commit()
            self.db.refresh(new_class)
            
            logger.info(f"Successfully created new class with ID: {new_class.id}")
            return new_class
            
        except HTTPException:
            self.db.rollback()
            raise
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in create_class: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error in create_class: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def get_upcoming_classes(self, class_type: Optional[str] = None) -> List[FitnessClass]:
        """
        Get all upcoming classes, optionally filtered by class type.
        All times are converted to the class's specified timezone.
        """
        logger.debug(f"Getting upcoming classes with class_type filter: {class_type}")
        
        try:
            # Validate class_type
            if class_type and class_type not in [ct.value for ct in ClassType]:
                logger.warning(f"Invalid class type: {class_type}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid class type. Must be one of: {[ct.value for ct in ClassType]}"
                )

            # Base query for future upcoming classes
            now_utc = datetime.utcnow()
            # Base query for upcoming classes
            query = self.db.query(FitnessClass).filter(
                FitnessClass.status == ClassStatus.UPCOMING,
                FitnessClass.start_time > now_utc
            )
            
            # Apply class type filter if provided
            if class_type:
                query = query.filter(FitnessClass.class_type == class_type)

            query = query.order_by(FitnessClass.start_time.asc())            
            # Get classes and convert times to their respective timezones
            classes = query.all()
            for class_obj in classes:
                # Convert start and end times to class timezone
                if class_obj.start_time:
                    class_obj.start_time = convert_to_timezone(class_obj.start_time, class_obj.timezone)
                if class_obj.end_time:
                    class_obj.end_time = convert_to_timezone(class_obj.end_time, class_obj.timezone)
            
            logger.debug(f"Found {len(classes)} upcoming classes")
            return classes
            
        except exc.SQLAlchemyError as e:
            logger.error(f"Database error in get_upcoming_classes: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in get_upcoming_classes: {str(e)}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def _get_class_status(self, class_obj: FitnessClass) -> str:
        """
        Determine the effective status of a class based on current time.
        
        Args:
            class_obj (FitnessClass): The class to check
            
        Returns:
            str: The effective status ('upcoming', 'active', or 'completed')
        """
        current_time = datetime.utcnow()
        
        if current_time >= class_obj.end_time:
            return "completed"
        elif current_time >= class_obj.start_time:
            return "active"
        return "upcoming"

    def update_classes_status(self) -> None:
        """
        Update status of all classes based on current time.
        This method is called before any class listing operation to ensure
        accurate status representation.
        """
        current_time = datetime.utcnow()
        
        # Update upcoming to active
        self.db.query(FitnessClass).filter(
            and_(
                FitnessClass.status == ClassStatus.UPCOMING,
                FitnessClass.start_time <= current_time,
                FitnessClass.end_time > current_time
            )
        ).update({"status": "active"})
        
        # Update active to completed
        self.db.query(FitnessClass).filter(
            and_(
                FitnessClass.status == "active",
                FitnessClass.end_time <= current_time
            )
        ).update({"status": "completed"})
        
        self.db.commit()

    def get_active_classes(self) -> List[FitnessClass]:
        """
        Get all currently active classes.
        
        Returns:
            List[FitnessClass]: List of classes with 'active' status
        """
        self.update_classes_status()
        return self.db.query(FitnessClass).filter(
            FitnessClass.status == "active"
        ).all()

    def get_completed_classes(self) -> List[FitnessClass]:
        """
        Get all completed classes.
        
        Returns:
            List[FitnessClass]: List of classes with 'completed' status
        """
        self.update_classes_status()
        return self.db.query(FitnessClass).filter(
            FitnessClass.status == "completed"
        ).all()

    def get_class(self, class_id: int) -> FitnessClass:
        """
        Get a class by its ID and update its status if needed.
        
        Args:
            class_id (int): ID of the class to retrieve
            
        Returns:
            FitnessClass: The requested class
            
        Raises:
            HTTPException: If class is not found
        """
        class_obj = self.db.query(FitnessClass).filter(FitnessClass.id == class_id).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Update status if needed
        new_status = self._get_class_status(class_obj)
        if new_status != class_obj.status:
            class_obj.status = new_status
            self.db.commit()
            self.db.refresh(class_obj)
            
        return class_obj

    def update_available_slots(self, class_id: int, change: int) -> FitnessClass:
        """
        Update the number of available slots for a class.
        Used when bookings are created or cancelled.
        
        Args:
            class_id (int): ID of the class to update
            change (int): Number of slots to add (positive) or remove (negative)
            
        Returns:
            FitnessClass: The updated class
            
        Raises:
            HTTPException: If class is not found or if change would result in negative slots
        """
        class_obj = self.get_class(class_id)
        
        # Calculate new available slots
        new_slots = class_obj.available_slots + change
        
        # Validate
        if new_slots < 0:
            raise HTTPException(status_code=400, detail="Not enough available slots")
        
        # Update
        class_obj.available_slots = new_slots
        self.db.commit()
        self.db.refresh(class_obj)
        
        return class_obj

    def delete_class(self, class_id: int) -> bool:
        """
        Delete a fitness class.
        
        Args:
            class_id (int): ID of the class to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            HTTPException: If class is not found
        """
        class_obj = self.get_class(class_id)
        self.db.delete(class_obj)
        self.db.commit()
        return True