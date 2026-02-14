# Architecture Documentation

## System Overview

The Brigada Survey System backend implements **Clean Architecture** principles with clear domain separation between admin control plane and mobile execution plane.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Admin Routes │  │Mobile Routes │  │  Auth Routes │          │
│  │ /admin/*     │  │ /mobile/*    │  │  /auth/*     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┼──────────────────┘                   │
│                            │                                      │
│                    ┌───────▼────────┐                            │
│                    │  Dependencies   │                            │
│                    │  (RBAC + Auth)  │                            │
│                    └───────┬────────┘                            │
└────────────────────────────┼─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                      Service Layer                                │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Auth   │  │  User   │  │  Survey  │  │Assignment│          │
│  │ Service │  │ Service │  │  Service │  │ Service  │          │
│  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬─────┘          │
│       │            │             │              │                 │
└───────┼────────────┼─────────────┼──────────────┼────────────────┘
        │            │             │              │
┌───────▼────────────▼─────────────▼──────────────▼────────────────┐
│                    Repository Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   User   │  │  Survey  │  │Assignment│  │ Response │        │
│  │Repository│  │Repository│  │Repository│  │Repository│        │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘        │
└────────┼─────────────┼─────────────┼─────────────┼───────────────┘
         │             │             │             │
┌────────▼─────────────▼─────────────▼─────────────▼───────────────┐
│                       Database Layer                              │
│  ┌─────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │Users│  │Surveys │  │Assignments│  │ Responses│  │Questions│  │
│  └─────┘  └────────┘  └──────────┘  └──────────┘  └─────────┘  │
│                      PostgreSQL Database                          │
└───────────────────────────────────────────────────────────────────┘
```

## Domain Separation

### Admin Control Plane
- **Purpose**: Survey management, user administration, analytics
- **Routes**: `/admin/*`
- **Roles**: Admin, Encargado
- **Features**:
  - Survey CRUD with versioning
  - User management
  - Assignment creation
  - Response analytics

### Mobile Execution Plane
- **Purpose**: Survey execution, offline sync, data collection
- **Routes**: `/mobile/*`
- **Roles**: Brigadista
- **Features**:
  - Download latest survey versions
  - Submit responses (offline sync with deduplication)
  - View personal submission history

## Key Design Patterns

### 1. Survey Versioning (Immutability)
```
Survey (id: 1, title: "Customer Survey")
  └── Version 1 (published: true)
       ├── Question 1
       ├── Question 2
       └── Question 3
  └── Version 2 (published: false, draft)
       ├── Question 1 (modified)
       ├── Question 2
       ├── Question 3
       └── Question 4 (new)
```

**Benefits**:
- Responses locked to specific versions
- Historical data integrity
- Enable A/B testing
- Safe editing without affecting active surveys

### 2. Offline Sync with Deduplication
```
Mobile App                    Backend
    │                            │
    │  Submit Response           │
    │  (client_id: uuid-123)     │
    ├──────────────────────────►│
    │                            │ Check client_id exists?
    │                            │ No → Create response
    │  ◄200 OK────────────────────┤
    │                            │
    │  [Connection lost]         │
    │  [Connection restored]     │
    │                            │
    │  Submit Same Response      │
    │  (client_id: uuid-123)     │
    ├──────────────────────────►│
    │                            │ Check client_id exists?
    │                            │ Yes → Return existing
    │  ◄200 OK (duplicate)────────┤
```

### 3. RBAC with Dependency Injection
```python
# Route protection
@router.post("/admin/surveys")
def create_survey(
    data: SurveyCreate,
    current_user: AdminUser  # Only allows Admin role
):
    ...

# Multiple roles
@router.post("/assignments")
def create_assignment(
    data: AssignmentCreate,
    current_user: AdminOrEncargado  # Admin OR Encargado
):
    ...
```

## Data Flow Examples

### Creating a Survey
```
Admin → POST /admin/surveys
  └─> SurveyService.create_survey()
      ├─> SurveyRepository.create() [Survey]
      ├─> SurveyRepository.create_version() [Version 1]
      └─> SurveyRepository.create_question() [×N questions]
          └─> SurveyRepository.create_answer_option() [×M options]
```

### Submitting Survey Response (Mobile)
```
Brigadista → POST /mobile/responses
  └─> ResponseService.submit_response()
      ├─> Check duplicate (client_id)
      ├─> Validate version is published
      ├─> ResponseRepository.create_response()
      └─> ResponseRepository.create_answer() [×N answers]
```

## Database Schema Relationships

```
users
  ├─► assignments (user_id)
  └─► survey_responses (user_id)

surveys
  ├─► survey_versions (survey_id)
  └─► assignments (survey_id)

survey_versions
  ├─► questions (version_id)
  └─► survey_responses (version_id)

questions
  ├─► answer_options (question_id)
  └─► question_answers (question_id)

survey_responses
  └─► question_answers (response_id)
```

## Security Features

1. **JWT Authentication**: Stateless token-based auth
2. **Password Hashing**: Bcrypt with salt
3. **RBAC**: Role-based endpoint protection
4. **CORS**: Configurable origins
5. **SQL Injection Protection**: SQLAlchemy ORM
6. **Input Validation**: Pydantic schemas

## Scalability Considerations

1. **Database Indexing**: Key fields indexed (user_id, survey_id, client_id)
2. **Connection Pooling**: SQLAlchemy pool configuration
3. **Pagination**: All list endpoints support skip/limit
4. **Async Support**: FastAPI async-ready (can add async SQLAlchemy)
5. **Horizontal Scaling**: Stateless JWT enables multi-instance deployment

## Future Enhancements

1. **Redis Caching**: Cache survey versions, user sessions
2. **Message Queue**: Async response processing (Celery + Redis)
3. **File Storage**: Cloudinary/S3 for photos/signatures
4. **WebSockets**: Real-time response updates
5. **GraphQL**: Alternative API for complex queries
6. **OCR Integration**: Extract data from document photos
7. **Analytics Dashboard**: Aggregated statistics and charts

## Testing Strategy

1. **Unit Tests**: Services and repositories
2. **Integration Tests**: API endpoints with test database
3. **E2E Tests**: Full user workflows
4. **Load Tests**: Performance under concurrent users

## Deployment Architecture

```
┌─────────────┐
│   Nginx     │ ← SSL/TLS termination, load balancing
└──────┬──────┘
       │
   ┌───▼────┐  ┌────────┐  ┌────────┐
   │FastAPI │  │FastAPI │  │FastAPI │ ← Multiple instances
   └───┬────┘  └───┬────┘  └───┬────┘
       │           │           │
   ┌───▼───────────▼───────────▼────┐
   │       PostgreSQL Primary        │
   │   (with read replicas)          │
   └─────────────────────────────────┘
```
