# Auth-Service

Serviço de autenticação reutilizável focado em login e cadastro usando FastAPI e PostgreSQL.

## Features

- 🔐 **Authentication**: User registration and login with JWT tokens
- 🗄️ **Database**: PostgreSQL with SQLAlchemy ORM
- 🔄 **Resilience**: Retry pattern using Tenacity library for DB connections
- 🔒 **Security**: Password hashing with Bcrypt via Passlib
- 🐳 **Containerization**: Docker and Docker Compose support

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Powerful, open-source relational database
- **SQLAlchemy**: SQL toolkit and ORM
- **PyJWT**: JSON Web Token implementation
- **Passlib + Bcrypt**: Password hashing library
- **Psycopg2**: PostgreSQL adapter for Python
- **Tenacity**: Retry library for resilience
- **Uvicorn**: ASGI server

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/elpidiocabral/Auth-Service.git
cd Auth-Service
```

2. Build and start the services:
```bash
docker-compose up --build
```

3. The API will be available at `http://localhost:8000`

4. Access the interactive API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Register a new user

**POST** `/register`

Request body:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

Response (201 Created):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

### 2. Login

**POST** `/login`

Request body:
```json
{
  "username": "john_doe",
  "password": "securepassword123"
}
```

Response (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Get current user information

**GET** `/me`

Headers:
```
Authorization: Bearer <access_token>
```

Response (200 OK):
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com"
}
```

## Testing with cURL

### Register a user:
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### Login:
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Get user info (replace TOKEN with actual token):
```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer TOKEN"
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
DATABASE_URL=postgresql://auth_user:auth_password@db:5432/auth_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Resilience Pattern

The service implements a retry pattern using the Tenacity library for database connections:
- **Retry attempts**: 5 attempts
- **Retry strategy**: Exponential backoff (2s min, 10s max)
- **Exception handling**: Retries on `OperationalError`

This ensures the application can handle temporary database connection issues gracefully.

## Development

### Local Development (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL and update environment variables

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
Auth-Service/
├── app/
│   ├── main.py         # FastAPI application and endpoints
│   ├── database.py     # Database models and connection with retry
│   ├── auth.py         # Authentication utilities (JWT, password hashing)
│   ├── schemas.py      # Pydantic models for request/response
│   └── config.py       # Configuration settings
├── Dockerfile          # Docker configuration for the app
├── docker-compose.yml  # Docker Compose configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables example
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Security Notes

- Change the `SECRET_KEY` in production
- Use strong passwords for database credentials
- Consider using HTTPS in production
- Implement rate limiting for production use
- Add input validation and sanitization as needed

## License

MIT
