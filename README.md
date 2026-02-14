# Brigada Survey System - Backend

FastAPI backend for mobile survey collection system with offline sync support.

## Architecture

Clean architecture with clear domain separation:
- **Models**: SQLAlchemy database models
- **Schemas**: Pydantic validation schemas
- **Repositories**: Data access layer
- **Services**: Business logic layer
- **API**: REST endpoints with RBAC

## Features

- ✅ JWT authentication with role-based access control (RBAC)
- ✅ Survey versioning (immutable versions)
- ✅ Offline sync with deduplication
- ✅ Assignment system (Encargado → Brigadista)
- ✅ Mobile app endpoints (download surveys, submit responses)
- ✅ Admin control plane (survey management, analytics)

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **JWT** - Authentication

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

4. Initialize database:
```bash
# Create database first (in PostgreSQL):
# CREATE DATABASE brigada_db;

# Run migrations
alembic upgrade head
```

5. Seed initial data (optional):
```bash
python scripts/seed_data.py
```

### Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/login` - Login with email/password

### Users
- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update own profile
- `POST /users` - Create user (Admin)
- `GET /users` - List users (Admin)

### Surveys (Admin)
- `POST /admin/surveys` - Create survey
- `GET /admin/surveys` - List surveys
- `GET /admin/surveys/{id}` - Get survey details
- `PUT /admin/surveys/{id}` - Update survey (creates new version)
- `POST /admin/surveys/{id}/versions/{version_id}/publish` - Publish version

### Assignments
- `POST /assignments` - Create assignment (Admin/Encargado)
- `GET /assignments/me` - Get my assignments (Brigadista)
- `GET /assignments/user/{id}` - Get user assignments (Admin/Encargado)

### Mobile App
- `GET /mobile/surveys/{id}/latest` - Get latest published survey
- `POST /mobile/responses` - Submit survey response (offline sync)
- `GET /mobile/responses/me` - Get my submitted responses

### Responses (Admin)
- `GET /admin/responses/survey/{id}` - Get all survey responses
- `GET /admin/responses/{id}` - Get response details

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Project Structure

```
brigadaBackEnd/
├── app/
│   ├── api/              # API routers
│   │   ├── dependencies.py  # RBAC dependencies
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── admin_surveys.py
│   │   ├── assignments.py
│   │   ├── mobile.py
│   │   └── admin_responses.py
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   ├── database.py   # DB setup
│   │   └── security.py   # JWT & password hashing
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── survey.py
│   │   ├── assignment.py
│   │   └── response.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── user.py
│   │   ├── survey.py
│   │   ├── assignment.py
│   │   └── response.py
│   ├── repositories/     # Data access layer
│   │   ├── user_repository.py
│   │   ├── survey_repository.py
│   │   ├── assignment_repository.py
│   │   └── response_repository.py
│   ├── services/         # Business logic
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── survey_service.py
│   │   ├── assignment_service.py
│   │   └── response_service.py
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
├── .env.example
├── requirements.txt
└── README.md
```

## User Roles

- **Admin**: Full system access, survey creation, user management
- **Encargado**: Assign surveys to brigadistas, view responses
- **Brigadista**: Complete assigned surveys via mobile app

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black app/
isort app/
```

Type checking:
```bash
mypy app/
```

## Production Deployment

1. Use environment variables for all secrets
2. Set `ENVIRONMENT=production` in .env
3. Use production WSGI server (e.g., Gunicorn)
4. Setup SSL/TLS
5. Configure proper CORS origins
6. Setup database backups
7. Implement rate limiting
8. Setup monitoring and logging

Example production command:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## License

Private - Brigada Project
