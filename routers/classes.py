from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modelsDB.database import get_db
from services.class_service import ClassService
from schemas.class_schema import FitnessClass, FitnessClassBase
from modelsDB.models import ClassType
from utils.logger import logger

router = APIRouter(
    prefix="/classes",
    tags=["classes"],
    responses={
        404: {"description": "Class not found"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"}
    }
)

@router.post("/", response_model=FitnessClass)
def create_class(
    class_data: FitnessClass,
    db: Session = Depends(get_db)
):
    """
    Create a new fitness class.
    
    Args:
        class_data: The class data to create
        db: Database session
        
    Returns:
        The created fitness class
        
    Raises:
        HTTPException: If class creation fails
    """
    logger.info(f"Creating new class: {class_data.name} ({class_data.class_type})")
    logger.debug(f"Class details: {class_data}")
    
    try:
        class_service = ClassService(db)
        new_class = class_service.create_class(class_data)
        logger.info(f"Successfully created class with ID: {new_class.id}")
        return new_class
        
    except Exception as e:
        logger.error(f"Failed to create class: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[FitnessClass])
async def get_upcoming_classes(
    class_type: Optional[ClassType] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of all upcoming fitness classes.
    
    This endpoint returns a list of all upcoming fitness classes with their details.
    You can optionally filter the results by class type.
    
    Args:
        class_type: Optional filter by class type (yoga, zumba, hiit)
        db: Database session
        
    Returns:
        List of upcoming classes with their details including:
        - Name
        - Date/time
        - Instructor
        - Available slots
        - Class type
        - Status
    """
    logger.info(f"Fetching upcoming classes" + (f" of type: {class_type}" if class_type else ""))
    
    try:
        class_service = ClassService(db)
        classes = class_service.get_upcoming_classes(class_type)
        logger.info(f"Successfully retrieved {len(classes)} classes")
        return classes
        
    except Exception as e:
        logger.error(f"Failed to fetch classes: {str(e)}")
        raise
