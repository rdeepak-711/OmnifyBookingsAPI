import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS")
BACKEND_CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(",")]

# Timezone configuration
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE")

# Class configuration
CLASS_MAX_DURATION_HOURS = int(os.getenv("CLASS_MAX_DURATION_HOURS"))
CLASS_MAX_CAPACITY = int(os.getenv("CLASS_MAX_CAPACITY"))
CLASS_MIN_CAPACITY = int(os.getenv("CLASS_MIN_CAPACITY"))

# Status configuration
CLASS_ALLOWED_STATUSES = os.getenv("CLASS_ALLOWED_STATUSES").split(",")
BOOKING_ALLOWED_STATUSES = os.getenv("BOOKING_ALLOWED_STATUSES").split(",")