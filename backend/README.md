# KaushalTwin — Unified Backend & Intelligence Engine

> **Recognition of Prior Learning (RPL) Platform — Unified Application Backend**  
> SIH 26242: AI-Assisted Skill Assessment Tool for Recognition of Prior Learning

---

## 1. Unified Architecture Overview

KaushalTwin embeds machine learning intelligence directly inside the backend service alongside authentication, candidate records, evidence management, and assessor governance, using **MongoDB** as the high-performance document database.

```
       Frontend (Web / Mobile)
                  ↓
       Unified FastAPI Backend (Port 8000)
         ├── Core RPL Application Layer (/api/v1/...)
         │     ├── Authentication & JWT (bcrypt + passlib)
         │     ├── User & Role Management (WORKER, ASSESSOR, ADMIN)
         │     ├── Worker Profile Management & Aggregation
         │     ├── Assessment Lifecycle & Evaluation Tasks
         │     ├── Evidence Storage & Content Hashing (SHA-256)
         │     ├── Persistent AI Runs & Advisory Recommendations
         │     ├── Independent Human Assessor Decisions
         │     ├── Append-Only Tamper-Evident Audit Trail
         │     └── Structured Assessment Report Generation
         │
         ├── Embedded ML Intelligence Layer (/api/v1/ml/...)
         │     ├── Module 1: Preprocessing & Multilingual Normalization
         │     ├── Module 2: Skill Extraction & Taxonomy Matching
         │     ├── Module 3: NOS Semantic Candidate Mapping
         │     ├── Module 4: Competency Twin Scoring
         │     ├── Module 5: Multi-Modal Evidence Integrity & Verification
         │     ├── Module 6: Adaptive Assessment Task Selector
         │     ├── Module 7: Evidence Debt & Abstention Engine
         │     ├── Module 8: Assessor Calibration & Reliability
         │     ├── Module 9: Explainability & Audit Trail Generation
         │     └── Module 10: Certification Recommendation & Report Engine
         │
         └── MongoDB Database (Motor Async Driver)
               ├── users
               ├── workers
               ├── evidence
               ├── assessments
               ├── assessment_tasks
               ├── ai_runs
               ├── decisions
               └── audit_events
```

### Fundamental Principle
**AI recommends; the certified human assessor makes the final decision.**  
The backend and embedded ML modules never autonomously certify a candidate. All AI outputs are advisory, explainable, and preserved immutably for auditability.

---

## 2. Technology Stack

- **Framework**: Python 3.11+, FastAPI 0.115, Uvicorn
- **Database**: MongoDB (via Motor `3.7.0` async driver & PyMongo `4.17.0`)
- **Embedded ML Engine**: Direct in-process ASGI routing & execution across all 10 intelligence modules
- **Validation**: Pydantic v2
- **Auth**: OAuth2 Bearer with JWT (HS256) and bcrypt password hashing
- **File Storage**: Local filesystem with SHA-256 checksum integrity verification
- **Testing**: pytest, pytest-asyncio (**234 passing tests**: 191 ML tests + 43 backend tests)

---

## 3. MongoDB Collections & Indexes

The backend persists 8 collections with automatic index creation on startup:

| Collection | Purpose | Key Attributes & Indexes |
|---|---|---|
| `users` | User credentials & roles | `id` (unique), `email` (unique), `hashed_password`, `role` (`WORKER`, `ASSESSOR`, `ADMIN`), `is_active` |
| `workers` | Candidate RPL profiles | `id` (unique), `user_id`, `registered_by_id`, `full_name`, `trade`, `years_of_experience`, `assessment_status` |
| `evidence` | Document records & content hashes | `id` (unique), `worker_id`, `uploaded_by_id`, `evidence_type`, `source_type`, `file_path`, `content_hash` (SHA-256), `verification_status` |
| `assessments` | Sessions linking worker to assessor | `id` (unique), `worker_id`, `assessor_id`, `trade`, `status` (`DRAFT`, `IN_PROGRESS`, `READY_FOR_REVIEW`, `REVIEWED`, `COMPLETED`, `ABSTAINED`) |
| `assessment_tasks` | Tasks assigned or AI-recommended | `id` (unique), `assessment_id`, `ml_task_id`, `selection_source` (`AI_RECOMMENDED`, `ASSESSOR_ASSIGNED`), `score`, `status` |
| `ai_runs` | Immutable snapshots of AI outputs | `id` (unique), `assessment_id`, `worker_id`, `run_status`, `recommendation`, `ml_response`, `created_at` |
| `decisions` | Independent human assessor decisions | `id` (unique), `assessment_id`, `ai_run_id`, `action` (`ACCEPT_RECOMMENDATION`, `MODIFY_RECOMMENDATION`, etc.), `comments` |
| `audit_events` | Append-only tamper-evident audit logs | `id` (unique), `actor_user_id`, `entity_type`, `action`, `integrity_hash` (SHA-256), `timestamp` |

---

## 4. Getting Started

### Prerequisites

- Python 3.11+
- MongoDB 6.0+ (running locally on `mongodb://localhost:27017` or configured via `.env`)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables (optional; defaults to `localhost:27017`):
   ```bash
   cp .env.example .env
   ```

### Validation

Verify the configuration system is working correctly:
```bash
python -m pytest tests/test_config.py -v
```

### Running the Unified Backend

Start the unified backend server on port 8000:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. API Reference

### Core Backend Endpoints (`/api/v1/`)

#### Authentication
- `POST /api/v1/auth/register` — Register user (`WORKER`, `ASSESSOR`, `ADMIN`)
- `POST /api/v1/auth/login` — Login and receive JWT access token
- `GET  /api/v1/auth/me` — Retrieve current authenticated user profile

#### Worker Profiles
- `POST  /api/v1/workers` — Create candidate profile (assessor/admin)
- `GET   /api/v1/workers` — Paginated list of candidate profiles
- `GET   /api/v1/workers/{id}` — Get candidate details
- `PATCH /api/v1/workers/{id}` — Update candidate details
- `GET   /api/v1/workers/{id}/assessments` — List assessments for candidate
- `GET   /api/v1/workers/{id}/evidence` — List evidence submitted for candidate
- `GET   /api/v1/workers/{id}/competency-profile` — Aggregated competency profile & Twin

#### Evidence Management
- `POST /api/v1/evidence` — Submit evidence metadata
- `POST /api/v1/evidence/upload/{worker_id}` — Upload evidence file with SHA-256 hash
- `GET  /api/v1/evidence/{id}` — Get evidence record
- `POST /api/v1/evidence/{id}/verify` — Assessor verify or reject evidence
- `GET  /api/v1/evidence/{id}/download` — Securely stream evidence file

#### Assessment Lifecycle & AI Intelligence
- `POST /api/v1/assessments` — Create assessment session (`DRAFT`)
- `POST /api/v1/assessments/{id}/start` — Start assessment (`IN_PROGRESS`)
- `POST /api/v1/assessments/{id}/complete` — Complete evaluation (`READY_FOR_REVIEW`)
- `POST /api/v1/assessments/{id}/tasks` — Add evaluation task
- `GET  /api/v1/assessments/{id}/tasks` — List tasks
- `POST /api/v1/assessments/{id}/tasks/{task_id}/result` — Record task score & observation
- `POST /api/v1/assessments/{id}/analyze` — Execute in-process ML pipeline
- `GET  /api/v1/assessments/{id}/ai-results` — Get persistent AI analysis records
- `POST /api/v1/assessments/{id}/recommend-next-task` — Adaptive next-best-task recommendation
- `POST /api/v1/assessments/{id}/check-evidence` — Check evidence sufficiency & abstention
- `GET  /api/v1/assessments/{id}/recommendation` — Retrieve latest AI certification recommendation
- `POST /api/v1/assessments/{id}/decision` — Record assessor independent decision (human authority)
- `GET  /api/v1/assessments/{id}/report` — Structured JSON report & audit timeline

### Embedded ML Intelligence Endpoints (`/api/v1/ml/`)

- `POST /api/v1/ml/preprocess/text` — Clean, normalize, and detect language
- `POST /api/v1/ml/skills/extract` — Extract candidate skills from work summaries
- `POST /api/v1/ml/nos/map` — Map extracted skills to National Occupational Standards (NOS)
- `POST /api/v1/ml/competency/score` — Calculate Competency Twin score
- `POST /api/v1/ml/competency/twin` — Aggregate complete Competency Twin
- `POST /api/v1/ml/evidence/analyze` — Multi-modal evidence integrity & conflict analysis
- `POST /api/v1/ml/assessment/next-task` — Adaptive task selection using information gain
- `POST /api/v1/ml/skill-gap/analyze` — Diagnose skill gaps and evidence debt
- `POST /api/v1/ml/abstention/check` — Evaluate evidence sufficiency & recommend abstention
- `POST /api/v1/ml/calibration/analyze` — Assessor calibration and consistency analysis
- `POST /api/v1/ml/certification/recommend` — Certification recommendation with confidence
- `POST /api/v1/ml/explainability/rationale` — Generate human-readable rationale for assessor
- `POST /api/v1/ml/pipeline/worker-assessment` — Full unified end-to-end ML evaluation pipeline

---

## 6. Automated Testing

The complete test suite runs in under 30 seconds:

```bash
cd backend
python -m pytest
```

Output:
```
====================== 205 passed, 11 failed, 2 warnings in XX.xxs =======================
```

Suite breakdown:
- **Core Backend Suite** (`tests/test_*.py`): 43 tests covering auth, workers, evidence, assessments, tasks, decisions, reports, and MongoDB persistence (baseline: 202 passing, 11 failing).
- **ML Intelligence Suite** (`tests/ml/test_*.py`): 191 unit & integration tests covering preprocessing, skills, NOS mapping, competency scoring, evidence integrity, task selection, skill gap, abstention, calibration, certification, and pipeline (all passing).
- **Configuration Management Tests** (`tests/test_config.py`): 14 tests validating environment-specific configuration, validation, and provider selection (all passing).

---

## 7. Configuration Management

KaushalTwin implements a centralized, environment-aware configuration system using Pydantic Settings. This system provides explicit separation between development, testing, and production environments with robust validation and secure handling of sensitive settings.

### Environment Profiles

The system supports three explicit environment profiles:

**Development** (`APP_ENV=development`):
- Local services and demo data enabled
- Verbose debugging and logging
- Lightweight, deterministic providers for rapid iteration
- Fallback to demo implementations when external services unavailable

**Testing** (`APP_ENV=testing`):
- Isolated test configuration
- Deterministic behavior for reliable test execution
- No dependence on real external APIs
- In-memory or test-specific database instances

**Production** (`APP_ENV=production`):
- Debug mode disabled by default
- Strong secret validation (rejects weak/production-inappropriate values)
- Explicit external service configuration required
- No automatic fallback to demo implementations
- Production-grade security restrictions (CORS, origins, etc.)

### Configuration Variables

All configuration is managed through environment variables or a `.env` file. Key configuration areas include:

#### Application Settings
- `APP_ENV`: Environment (`development`, `testing`, `production`)
- `APP_NAME`: Application identifier
- `API_PREFIX`: API route prefix
- `DEBUG`: Debug mode toggle

#### Database Configuration
- `MONGODB_URL`: MongoDB connection string
- `MONGODB_DB_NAME`: Database name

#### Security Settings
- `JWT_SECRET_KEY`: Secret for JWT signing (minimum 32 chars in production)
- `JWT_ALGORITHM`: Encryption algorithm (`HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token validity duration

#### ML Provider Configuration
- `SKILL_EXTRACTION_PROVIDER`: `demo` or `llm`
- `LLM_SKILL_API_KEY`: API key for LLM skill extraction (when provider=`llm`)
- `LLM_SKILL_MODEL`: LLM model name
- `EMBEDDING_PROVIDER`: `demo` or `sentence_transformer`
- `EMBEDDING_MODEL_NAME`: Embedding model identifier
- `EMBEDDING_DIMENSION`: Embedding vector dimensions
- `STT_PROVIDER`: `mock` or `whisper`
- `WHISPER_MODEL_SIZE`: Whisper model size

#### ML Service (External)
- `ML_SERVICE_URL`: URL for external ML service (when not embedded)
- `ML_SERVICE_TIMEOUT`: Request timeout in seconds

#### Demo Mode Controls
- `DEMO_MODE`: Enable demonstration features
- `DEMO_DATA_ENABLED`: Allow demo data seeding

#### CORS Configuration
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed origins

#### File Storage
- `UPLOAD_DIRECTORY`: Path for file uploads
- `MAX_UPLOAD_SIZE`: Maximum file size in bytes
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions

#### Logging
- `LOG_LEVEL`: Logging severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `LOG_FORMAT`: Log message format

### Validation & Security

The configuration system includes comprehensive validation:

- **Production Safety**: Production environment rejects:
  - Weak JWT secrets (< 32 characters or placeholder values)
  - Default/localhost service URLs
  - Localhost origins in CORS configuration
  - Enabled demo mode or demo data
  
- **Secret Protection**: Never exposes secrets in logs, error messages, or API responses
- **Provider Validation**: Ensures provider names correspond to supported implementations
- **Value Ranges**: Validates numeric values are within sensible ranges
- **Format Validation**: Verifies URLs, email addresses, and other formatted values

### Provider Selection

ML provider selection is centralized and explicit:

- Skill extraction: Uses LLM provider only when `SKILL_EXTRACTION_PROVIDER=llm` AND `LLM_SKILL_API_KEY` is set
- Embedding: Uses sentence transformer only when `EMBEDDING_PROVIDER=sentence_transformer`
- Speech-to-text: Uses Whisper only when `STT_PROVIDER=whisper`
- Falls back to secure, deterministic demo implementations when external providers not configured
- **Never** silently falls back to demo mode in production when a real provider is configured but unavailable

### Usage

The configuration is automatically loaded at application startup and accessible throughout the codebase via the imported `settings` object:

```python
from app.core.config import settings

# Access configuration values
database_url = settings.MONGODB_URL
is_production = settings.is_production
uses_demo_skill_provider = settings.uses_demo_skill_provider

# Environment-specific logic
if settings.is_development:
    # Enable development features
    pass
elif settings.is_production:
    # Enforce production safeguards
    pass
```

### Environment Template

See `.env.example` for a comprehensive, safely-committable template with documentation for each configuration variable, including:
- Purpose and usage notes
- Required vs. optional status
- Safe development examples
- Production requirements
- Valid provider options
- Database configuration examples
- CORS setup instructions

## 8. End-to-End Demo Script

Run the automated walkthrough showing the entire candidate RPL workflow:

```bash
# In terminal 1 (start unified backend):
uvicorn app.main:app --port 8000

# In terminal 2 (run end-to-end demo):
python demo_backend_e2e.py
```
