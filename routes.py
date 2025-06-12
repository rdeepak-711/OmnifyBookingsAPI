from fastapi import APIRouter
from routers import classes, bookings

# Create main API router
api_router = APIRouter()

# Include all routers with their prefixes
api_router.include_router(classes.router, prefix="")
api_router.include_router(bookings.router, prefix="")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        dict: Status of the API
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "classes": "operational",
            "bookings": "operational"
        }
    } 