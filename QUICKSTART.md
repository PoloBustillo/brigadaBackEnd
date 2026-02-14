# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd brigadaBackEnd
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Your `.env` file is already configured with Neon PostgreSQL! ✅

The database connection string is set to:
```
DATABASE_URL=postgresql://neondb_owner:...@ep-tiny-flower-aitww2p1-pooler.c-4.us-east-1.aws.neon.tech/neondb
```

**Note**: Using Neon cloud database - no need to create local PostgreSQL! 🎉

### 3. Setup Database

Run migrations:
```bash
alembic upgrade head
```

Seed test data:
```bash
python scripts/seed_data.py
```

### 4. Start Server
```bash
uvicorn app.main:app --reload
```

## Test the API

### 1. Login (get JWT token)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@brigada.com",
    "password": "admin123"
  }'
```

Save the `access_token` from response.

### 2. Create a Survey
```bash
curl -X POST http://localhost:8000/admin/surveys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "Customer Satisfaction Survey",
    "description": "Quick customer feedback survey",
    "questions": [
      {
        "question_text": "How satisfied are you?",
        "question_type": "single_choice",
        "order": 1,
        "is_required": true,
        "options": [
          {"option_text": "Very satisfied", "order": 1},
          {"option_text": "Satisfied", "order": 2},
          {"option_text": "Neutral", "order": 3},
          {"option_text": "Dissatisfied", "order": 4}
        ]
      },
      {
        "question_text": "Additional comments",
        "question_type": "text",
        "order": 2,
        "is_required": false
      }
    ]
  }'
```

### 3. Access API Docs

Open browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Test Users

| Email | Password | Role |
|-------|----------|------|
| admin@brigada.com | admin123 | Admin |
| encargado@brigada.com | encargado123 | Encargado |
| brigadista@brigada.com | brigadista123 | Brigadista |

## Common Tasks

### Create Migration
```bash
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

### Reset Database
```bash
alembic downgrade base
alembic upgrade head
python scripts/seed_data.py
```

### Run with Specific Host/Port
```bash
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

## Troubleshooting

**Database connection error**: Check DATABASE_URL in `.env`

**Import errors**: Make sure venv is activated

**Migration errors**: Try `alembic downgrade base` then `upgrade head`

**JWT errors**: Generate new SECRET_KEY: `openssl rand -hex 32`
