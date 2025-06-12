# Fitness Class Booking API

A FastAPI-based REST API for managing fitness class bookings. This API allows users to create and manage fitness classes, book classes, and view their bookings with automatic capacity management and comprehensive error handling.

## 🚀 Features

- **Class Management**: Create and manage fitness classes with instructor details
- **Smart Booking System**: Book classes with automatic capacity management
- **Filtering & Search**: View upcoming classes with filtering options
- **Personal Dashboard**: View personal bookings and booking history
- **Robust Error Handling**: Comprehensive error handling and logging
- **Auto Database Management**: Automatic SQLite database setup and management
- **Modular Architecture**: Clean separation with routers, services, and schemas
- **Environment Configuration**: Flexible configuration management

## 📁 Project Structure

```
OmnifyBookingsAPI/
├── routers/          # API route handlers
├── services/         # Business logic layer
├── schemas/          # Pydantic models for request/response
├── modelsDB/         # SQLAlchemy database models
├── utils/            # Utility functions and helpers
├── scripts/          # Utility scripts
├── main.py          # Application entry point
├── routes.py        # Route definitions
├── config.py        # Configuration management
└── requirements.txt # Project dependencies
```

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (comes with Python)
- **Git** - For cloning the repository

## 📦 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd OmnifyBookingsAPI
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration

Create a `.env` file in the root directory:

```env
# Database configuration
DATABASE_URL=sqlite:///./app.db

# CORS configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000

# Timezone configuration
DEFAULT_TIMEZONE=Asia/Kolkata

# Class configuration
CLASS_MAX_DURATION_HOURS=8
CLASS_MAX_CAPACITY=30
CLASS_MIN_CAPACITY=1

# Status configuration
CLASS_ALLOWED_STATUSES=scheduled,active,completed,cancelled
BOOKING_ALLOWED_STATUSES=pending,confirmed,cancelled,completed
```

### Step 5: Run the Application

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

### Step 6: Verify Installation

Open your browser and navigate to:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🔗 API Endpoints

### Classes Endpoints

| Method | Endpoint    | Description                      |
| ------ | ----------- | -------------------------------- |
| GET    | `/classes/` | Get all upcoming fitness classes |
| POST   | `/classes/` | Create a new fitness class       |

### Bookings Endpoints

| Method | Endpoint     | Description                   |
| ------ | ------------ | ----------------------------- |
| POST   | `/bookings/` | Create a new booking          |
| GET    | `/bookings/` | Get all bookings for a client |

## 📋 Sample API Requests

### 1. Create a New Fitness Class

**cURL Request:**

```bash
curl -X POST "http://localhost:8000/classes/" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "Morning Yoga Flow",
           "class_type": "yoga",
           "instructor": "Sarah Johnson",
           "start_time": "2024-03-25T09:00:00",
           "end_time": "2024-03-25T10:00:00",
           "capacity": 15,
           "timezone": "UTC",
           "created_by": "admin@fitnessStudio.com"
         }'
```

**Expected Response:**

```json
{
  "id": 1,
  "name": "Morning Yoga Flow",
  "class_type": "yoga",
  "instructor": "Sarah Johnson",
  "start_time": "2024-03-25T09:00:00",
  "end_time": "2024-03-25T10:00:00",
  "capacity": 15,
  "available_spots": 15,
  "timezone": "UTC",
  "created_by": "admin@fitnessStudio.com"
}
```

### 2. Get All Upcoming Classes

**cURL Request:**

```bash
curl -X GET "http://localhost:8000/classes/"
```

**With Class Type Filter:**

```bash
curl -X GET "http://localhost:8000/classes/?class_type=yoga"
```

**Expected Response:**

```json
[
  {
    "id": 1,
    "name": "Morning Yoga Flow",
    "class_type": "yoga",
    "instructor": "Sarah Johnson",
    "start_time": "2024-03-25T09:00:00",
    "end_time": "2024-03-25T10:00:00",
    "capacity": 15,
    "available_spots": 14,
    "timezone": "UTC"
  }
]
```

### 3. Book a Fitness Class

**cURL Request:**

```bash
curl -X POST "http://localhost:8000/bookings/" \
     -H "Content-Type: application/json" \
     -d '{
           "class_id": 1,
           "client_name": "Alice Cooper",
           "client_email": "alice.cooper@email.com"
         }'
```

**Expected Response:**

```json
{
  "id": 1,
  "class_id": 1,
  "client_name": "Alice Cooper",
  "client_email": "alice.cooper@email.com",
  "booking_time": "2024-03-20T14:30:00",
  "status": "confirmed"
}
```

### 4. Get Client Bookings

**cURL Request:**

```bash
curl -X GET "http://localhost:8000/bookings/" \
     -H "x-client-email: alice.cooper@email.com"
```

**Expected Response:**

```json
[
  {
    "id": 1,
    "class_id": 1,
    "class_name": "Morning Yoga Flow",
    "instructor": "Sarah Johnson",
    "start_time": "2024-03-25T09:00:00",
    "end_time": "2024-03-25T10:00:00",
    "booking_time": "2024-03-20T14:30:00",
    "status": "confirmed"
  }
]
```

## ⚠️ Error Handling

The API provides comprehensive error responses:

### Common Error Responses

**Class Not Found (404):**

```json
{
  "detail": "Class not found"
}
```

**Class Full (400):**

```json
{
  "detail": "Class is full, no available spots"
}
```

**Validation Error (422):**

```json
{
  "detail": [
    {
      "loc": ["body", "client_email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Duplicate Booking (400):**

```json
{
  "detail": "You have already booked this class"
}
```

## 🔧 Testing the API

### Quick Health Check

```bash
curl -X GET "http://localhost:8000/"
```

### Test Complete Workflow

1. **Create a class** using the sample request above
2. **List classes** to verify creation
3. **Book the class** with a client
4. **Check bookings** for that client
5. **Try booking the same class again** (should fail with duplicate error)

## 📝 Request/Response Schema

### Class Creation Schema

```json
{
  "name": "string (required)",
  "class_type": "string (required)",
  "instructor": "string (required)",
  "start_time": "datetime (required)",
  "end_time": "datetime (required)",
  "capacity": "integer (required)",
  "timezone": "string (required)",
  "created_by": "string (required)"
}
```

### Booking Schema

```json
{
  "class_id": "integer (required)",
  "client_name": "string (required)",
  "client_email": "string (required, valid email)"
}
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**

```bash
uvicorn main:app --reload --port 8001
```

**Database Issues:**
Delete the database file and restart:

```bash
rm fitness_studio.db
uvicorn main:app --reload
```

**Virtual Environment Issues:**
Recreate the virtual environment:

```bash
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 📊 Logging

The application logs all activities. Check logs for debugging:

- **DEBUG**: Detailed execution flow
- **INFO**: General information
- **WARNING**: Potential issues
- **ERROR**: Exceptions and errors

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check application logs
4. Open an issue in the repository

---

**Happy Coding! 🏋️‍♀️💪**
