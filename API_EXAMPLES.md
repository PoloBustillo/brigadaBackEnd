# API Testing Examples

Complete API endpoint examples with curl commands.

## Setup

First, start the server:
```bash
uvicorn app.main:app --reload
```

## Authentication

### Login as Admin
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@brigada.com",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Save token for subsequent requests:
```bash
export TOKEN="your_access_token_here"
```

## User Management

### Get Current User Profile
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### Create New User (Admin only)
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "email": "nuevo@brigada.com",
    "password": "password123",
    "full_name": "Nuevo Brigadista",
    "phone": "+1234567893",
    "role": "brigadista"
  }'
```

### List All Users (Admin only)
```bash
curl -X GET "http://localhost:8000/users?skip=0&limit=10&role=brigadista" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Own Profile
```bash
curl -X PATCH http://localhost:8000/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "full_name": "Updated Name",
    "phone": "+9876543210"
  }'
```

## Survey Management (Admin)

### Create Survey with Questions
```bash
curl -X POST http://localhost:8000/admin/surveys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Encuesta de Satisfacción del Cliente",
    "description": "Evaluar la experiencia del cliente",
    "questions": [
      {
        "question_text": "¿Qué tan satisfecho está con nuestro servicio?",
        "question_type": "single_choice",
        "order": 1,
        "is_required": true,
        "options": [
          {"option_text": "Muy satisfecho", "order": 1},
          {"option_text": "Satisfecho", "order": 2},
          {"option_text": "Neutral", "order": 3},
          {"option_text": "Insatisfecho", "order": 4},
          {"option_text": "Muy insatisfecho", "order": 5}
        ]
      },
      {
        "question_text": "¿Cuántas veces ha usado nuestro servicio?",
        "question_type": "number",
        "order": 2,
        "is_required": true,
        "validation_rules": {
          "min": 0,
          "max": 100
        }
      },
      {
        "question_text": "¿Qué aspectos mejoraría?",
        "question_type": "multiple_choice",
        "order": 3,
        "is_required": false,
        "options": [
          {"option_text": "Velocidad", "order": 1},
          {"option_text": "Atención al cliente", "order": 2},
          {"option_text": "Precio", "order": 3},
          {"option_text": "Calidad", "order": 4}
        ]
      },
      {
        "question_text": "Comentarios adicionales",
        "question_type": "text",
        "order": 4,
        "is_required": false
      },
      {
        "question_text": "Foto del establecimiento",
        "question_type": "photo",
        "order": 5,
        "is_required": false
      }
    ]
  }'
```

### List All Surveys
```bash
curl -X GET "http://localhost:8000/admin/surveys?is_active=true" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Survey Details
```bash
curl -X GET http://localhost:8000/admin/surveys/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Publish Survey Version
```bash
curl -X POST http://localhost:8000/admin/surveys/1/versions/1/publish \
  -H "Authorization: Bearer $TOKEN"
```

### Update Survey (creates new version)
```bash
curl -X PUT http://localhost:8000/admin/surveys/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "change_summary": "Added new question about delivery time",
    "questions": [
      {
        "question_text": "¿Qué tan satisfecho está?",
        "question_type": "single_choice",
        "order": 1,
        "is_required": true,
        "options": [
          {"option_text": "Muy satisfecho", "order": 1},
          {"option_text": "Satisfecho", "order": 2}
        ]
      },
      {
        "question_text": "¿Cuánto tiempo tardó la entrega?",
        "question_type": "text",
        "order": 2,
        "is_required": false
      }
    ]
  }'
```

## Assignments

### Create Assignment (Encargado assigns to Brigadista)
```bash
curl -X POST http://localhost:8000/assignments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": 3,
    "survey_id": 1,
    "location": "Zona Norte - Barrio Centro"
  }'
```

### Get My Assignments (Brigadista)
```bash
# Login as brigadista first
export BRIGADISTA_TOKEN="brigadista_token_here"

curl -X GET http://localhost:8000/assignments/me \
  -H "Authorization: Bearer $BRIGADISTA_TOKEN"
```

### Get Assignments for Specific User
```bash
curl -X GET http://localhost:8000/assignments/user/3 \
  -H "Authorization: Bearer $TOKEN"
```

### Update Assignment Status
```bash
curl -X PATCH http://localhost:8000/assignments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "in_progress"
  }'
```

## Mobile App (Brigadista)

### Get Latest Survey Version
```bash
curl -X GET http://localhost:8000/mobile/surveys/1/latest \
  -H "Authorization: Bearer $BRIGADISTA_TOKEN"
```

### Submit Survey Response
```bash
curl -X POST http://localhost:8000/mobile/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIGADISTA_TOKEN" \
  -d '{
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "version_id": 1,
    "started_at": "2026-02-14T10:00:00Z",
    "completed_at": "2026-02-14T10:15:00Z",
    "location": {
      "lat": 19.4326,
      "lng": -99.1332,
      "accuracy": 10,
      "timestamp": "2026-02-14T10:15:00Z"
    },
    "device_info": {
      "platform": "ios",
      "version": "17.0",
      "app_version": "1.0.0"
    },
    "answers": [
      {
        "question_id": 1,
        "answer_value": "Muy satisfecho",
        "answered_at": "2026-02-14T10:05:00Z"
      },
      {
        "question_id": 2,
        "answer_value": 5,
        "answered_at": "2026-02-14T10:07:00Z"
      },
      {
        "question_id": 3,
        "answer_value": ["Velocidad", "Calidad"],
        "answered_at": "2026-02-14T10:10:00Z"
      },
      {
        "question_id": 4,
        "answer_value": "Excelente servicio, muy recomendado",
        "answered_at": "2026-02-14T10:12:00Z"
      },
      {
        "question_id": 5,
        "media_url": "https://cloudinary.com/image123.jpg",
        "answered_at": "2026-02-14T10:14:00Z"
      }
    ]
  }'
```

### Get My Submitted Responses
```bash
curl -X GET http://localhost:8000/mobile/responses/me \
  -H "Authorization: Bearer $BRIGADISTA_TOKEN"
```

## Response Analytics (Admin/Encargado)

### Get All Responses for Survey
```bash
curl -X GET http://localhost:8000/admin/responses/survey/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Get Responses for Specific Version
```bash
curl -X GET http://localhost:8000/admin/responses/version/1 \
  -H "Authorization: Bearer $TOKEN"
```

### Get Response Details
```bash
curl -X GET http://localhost:8000/admin/responses/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Testing Offline Sync (Deduplication)

Submit same response twice with same client_id:

**First submission** (creates new response):
```bash
curl -X POST http://localhost:8000/mobile/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIGADISTA_TOKEN" \
  -d '{
    "client_id": "test-duplicate-123",
    "version_id": 1,
    "completed_at": "2026-02-14T10:00:00Z",
    "answers": [
      {
        "question_id": 1,
        "answer_value": "Test",
        "answered_at": "2026-02-14T10:00:00Z"
      }
    ]
  }'
# Returns 201 Created
```

**Second submission** (returns existing response):
```bash
curl -X POST http://localhost:8000/mobile/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIGADISTA_TOKEN" \
  -d '{
    "client_id": "test-duplicate-123",
    "version_id": 1,
    "completed_at": "2026-02-14T10:00:00Z",
    "answers": [
      {
        "question_id": 1,
        "answer_value": "Test",
        "answered_at": "2026-02-14T10:00:00Z"
      }
    ]
  }'
# Returns 201 Created (but response is same as first)
```

## Postman Collection

Import this JSON into Postman for easier testing:

```json
{
  "info": {
    "name": "Brigada Survey API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"admin@brigada.com\",\n  \"password\": \"admin123\"\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            },
            "url": {
              "raw": "{{baseUrl}}/auth/login",
              "host": ["{{baseUrl}}"],
              "path": ["auth", "login"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000"
    },
    {
      "key": "token",
      "value": ""
    }
  ]
}
```
