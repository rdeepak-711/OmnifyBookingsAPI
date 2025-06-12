from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import BACKEND_CORS_ORIGINS
from routes import api_router

# Create FastAPI app
app = FastAPI(
    title="Fitness Studio Booking API",
    description="API for managing fitness class bookings",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Fitness Studio Booking API"}

app.include_router(router=api_router)