# KaushalTwin ML Service

> **"The RPL system that knows when it doesn't know."**
>
> AI/ML intelligence layer for the KaushalTwin Recognition of Prior Learning (RPL) platform.

---

## What Is This?

This is the **standalone ML + FastAPI service** for KaushalTwin — the first 5 modules of the platform.

It converts raw worker transcripts into structured competency assessments by:

1. **Preprocessing** raw Hindi/English/Hinglish text
2. **Extracting skills** from natural language descriptions
3. **Mapping skills to NOS** (National Occupational Standards) elements
4. **Building a Competency Twin** from assessment evidence
5. **Selecting the next best assessment task** using a transparent algorithm

> **IMPORTANT**: This service assists human assessors. It **never certifies a worker** and never produces a final Commit/Abstain decision. All certification logic belongs to future modules.

---

## Architecture

```
ml_service/
├── app/
│   ├── main.py                     ← FastAPI application
│   ├── api/                        ← Route handlers (thin, call services)
│   │   ├── preprocessing.py
│   │   ├── skills.py
│   │   ├── competency.py
│   │   ├── evidence.py
│   │   ├── assessment.py
│   │   └── pipeline.py
│   ├── schemas/                    ← Pydantic request/response models
│   ├── services/                   ← Business logic layer
│   ├── algorithms/                 ← Pure ML/math functions (no FastAPI)
│   │   ├── similarity.py           ← Cosine, TF-IDF, keyword, hybrid scoring
│   │   ├── competency_score.py     ← Weighted criterion scoring
│   │   ├── evidence_features.py    ← Source weighting, conflict detection
│   │   └── task_selector.py        ← Deterministic task value & ranking
│   ├── providers/                  ← Replaceable ML providers
│   │   ├── skill_provider.py       ← DemoSkillExtraction + LLM interface
│   │   ├── embedding_provider.py   ← Demo TF-IDF + SentenceTransformer
│   │   └── stt_provider.py         ← STT interface (Mock + Whisper)
│   ├── data/                       ← Demo JSON data (clearly labelled DEMO)
│   │   ├── demo_nos.json
│   │   ├── demo_tasks.json
│   │   ├── demo_glossary.json
│   │   └── demo_workers.json
│   └── utils/
│       └── normalisation.py        ← Unicode, whitespace, tokenisation
├── tests/                          ← 155 pytest tests (all passing)
├── evaluation/
│   └── evaluate.py                 ← Evaluation scripts (SYNTHETIC/DEMO)
├── demo_e2e.py                     ← End-to-end demo script
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## The Five Modules

### Module 1 — ML Data Preprocessing

Converts raw worker text into clean ML-ready input.

- Unicode normalisation (handles Devanagari + Latin)
- Whitespace normalisation
- Mixed Hindi/English/Hinglish support
- Sentence splitting, tokenisation
- Language detection (script heuristics)

**API:** `POST /api/v1/ml/preprocess/text`

---

### Module 2 — Skill Intelligence & NOS Mapping

Extracts structured skills from natural language and maps them to NOS elements.

- **Deterministic rule-based extraction** (no random confidence values)
- Trade glossary normalisation (`"line tester"` → `"voltage tester"`)
- Hybrid NOS matching: exact match + keyword overlap + TF-IDF + embedding
- Returns **CANDIDATE mappings only** — never certified

**APIs:**
- `POST /api/v1/ml/skills/extract`
- `POST /api/v1/ml/nos/map`
- `POST /api/v1/ml/nos/search`
- `GET  /api/v1/ml/nos`
- `GET  /api/v1/ml/nos/{nos_id}`

---

### Module 3 — Competency Twin & Scoring

Builds a live competency state representation for a worker.

- Weighted criterion scoring: `SUM(score × weight) / SUM(weight)` normalised to 0–100
- Evidence coverage: fraction of criteria actually observed
- **Keeps `competency_score` and `evidence_confidence` strictly separate**
- `evidence_confidence = null` until the future Bayesian engine (Module 7)
- Statuses: `UNASSESSED`, `IN_PROGRESS`, `EVIDENCE_AVAILABLE`

**APIs:**
- `POST /api/v1/ml/competency/score`
- `POST /api/v1/ml/competency/twin`

---

### Module 4 — Evidence Feature & Integrity Analysis

Analyses evidence metadata — does NOT store files.

- Configurable source reliability weights (prototype, not empirically validated)
- Conflict detection: self-declaration vs. practical evidence
- SHA-256 hashing helper
- Exact duplicate detection

**APIs:**
- `POST /api/v1/ml/evidence/analyze`
- `POST /api/v1/ml/evidence/conflict`
- `POST /api/v1/ml/evidence/hash`
- `POST /api/v1/ml/evidence/duplicates`

---

### Module 5 — Adaptive Assessment / Next-Best-Task

Deterministically selects the most valuable assessment task.

Formula:
```
TaskValue = SUM( importance_i × uncertainty_i × coverage_i ) / duration
uncertainty = 1 - confidence  (or 1 - evidence_coverage as fallback)
```

- **No LLM in the decision loop** — fully deterministic and explainable
- Returns reasons alongside the score
- Task variants (fault types) supported
- Simple coverage-based early-stopping placeholder

**APIs:**
- `POST /api/v1/ml/assessment/next-task`
- `POST /api/v1/ml/assessment/rank-tasks`
- `POST /api/v1/ml/assessment/select-variant`
- `POST /api/v1/ml/assessment/should-continue`

---

### Unified Pipeline

- `POST /api/v1/ml/pipeline/worker-assessment`

Runs all 5 modules in sequence: transcript → preprocess → skills → NOS map → competency twin → evidence analysis → next task.

---

## All FastAPI Endpoints

| Method | Path | Module | Description |
|--------|------|--------|-------------|
| GET  | `/health` | — | Liveness check |
| POST | `/api/v1/ml/preprocess/text` | 1 | Preprocess raw text |
| POST | `/api/v1/ml/skills/extract` | 2 | Extract skills from transcript |
| POST | `/api/v1/ml/nos/map` | 2 | Map skills to NOS candidates |
| POST | `/api/v1/ml/nos/search` | 2 | Free-text NOS search |
| GET  | `/api/v1/ml/nos` | 2 | List all NOS elements |
| GET  | `/api/v1/ml/nos/{nos_id}` | 2 | Get NOS by ID |
| POST | `/api/v1/ml/competency/score` | 3 | Score a single NOS competency |
| POST | `/api/v1/ml/competency/twin` | 3 | Build multi-NOS Competency Twin |
| POST | `/api/v1/ml/evidence/analyze` | 4 | Analyse evidence features |
| POST | `/api/v1/ml/evidence/conflict` | 4 | Detect evidence conflicts |
| POST | `/api/v1/ml/evidence/hash` | 4 | SHA-256 hash content |
| POST | `/api/v1/ml/evidence/duplicates` | 4 | Find duplicate hashes |
| POST | `/api/v1/ml/assessment/next-task` | 5 | Select next best task |
| POST | `/api/v1/ml/assessment/rank-tasks` | 5 | Rank all tasks by value |
| POST | `/api/v1/ml/assessment/select-variant` | 5 | Select task variant |
| POST | `/api/v1/ml/assessment/should-continue` | 5 | Early-stopping check |
| POST | `/api/v1/ml/pipeline/worker-assessment` | All | Full unified pipeline |

Swagger UI: **http://localhost:8000/docs**
ReDoc: **http://localhost:8000/redoc**

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
python -m pytest tests/ -v

# Run evaluation (SYNTHETIC/DEMO)
python evaluation/evaluate.py

# Run end-to-end demo
python demo_e2e.py
```

---

## Running with Docker

```bash
docker build -t kaushaltwin-ml .
docker run -p 8000:8000 kaushaltwin-ml
```

---

## Demo Mode

The service works completely without:
- OpenAI API key
- Cloud GPU
- PostgreSQL
- External database

**Demo mode** uses:
- `app/data/demo_nos.json` — 10 electrician NOS elements (labelled `"source_type": "DEMO"`)
- `app/data/demo_tasks.json` — 8 assessment tasks with NOS coverage
- `app/data/demo_glossary.json` — 15 Hindi/English trade terms
- `app/data/demo_workers.json` — 2 demo worker profiles
- Deterministic TF-IDF embedding provider (no heavy model download required)

> **IMPORTANT**: Demo NOS IDs (`DEMO_NOS_001` … `DEMO_NOS_010`) are NOT official NCVET/NSQF codes. They must be replaced with verified data before production use.

---

## AI Provider Configuration

Set in `.env` (copy `.env.example`):

```env
DEMO_MODE=true
SKILL_EXTRACTION_PROVIDER=demo       # or: llm
EMBEDDING_PROVIDER=demo              # or: sentence_transformer
```

For real semantic embeddings (optional):
```bash
pip install sentence-transformers
# then set EMBEDDING_PROVIDER=sentence_transformer
```

For LLM skill extraction (optional):
```env
SKILL_EXTRACTION_PROVIDER=llm
OPENAI_API_KEY=sk-...
```

If any provider is unavailable, the service automatically falls back to demo mode.

---

## Example API Requests

### Preprocess text
```bash
curl -X POST http://localhost:8000/api/v1/ml/preprocess/text \
  -H "Content-Type: application/json" \
  -d '{"text": "I install switches and fans. I do house wiring.", "language": "en"}'
```

### Extract skills
```bash
curl -X POST http://localhost:8000/api/v1/ml/skills/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "I install switches, do house wiring, find faults using a tester", "language": "en", "trade": "electrician"}'
```

### Next best task
```bash
curl -X POST http://localhost:8000/api/v1/ml/assessment/next-task \
  -H "Content-Type: application/json" \
  -d '{
    "competency_states": [
      {"nos_id": "DEMO_NOS_004", "mandatory": true, "importance": 1.0, "weight": 1.0,
       "evidence_confidence": 0.35, "evidence_coverage": 0.2, "competency_score": 40},
      {"nos_id": "DEMO_NOS_005", "mandatory": true, "importance": 0.9, "weight": 0.9,
       "evidence_confidence": null, "evidence_coverage": 0.0, "competency_score": 0}
    ]
  }'
```

Response:
```json
{
  "selected_task": {
    "id": "TASK_004",
    "title": "Electrical Fault Diagnosis",
    "priority_score": 0.125
  },
  "reason": [
    "DEMO_NOS_005: mandatory competency with high uncertainty",
    "DEMO_NOS_005: high NOS coverage by this task",
    "task is mandatory in qualification"
  ],
  "note": "Task selection is deterministic. No LLM was used to choose this task."
}
```

---

## How the Main Backend Calls This Service

The KaushalTwin backend (`kaushal_twin/`) calls this service over HTTP:

```python
import httpx

async def get_next_task(competency_states: list[dict]) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml-service:8000/api/v1/ml/assessment/next-task",
            json={"competency_states": competency_states}
        )
        return response.json()
```

The ML service is **stateless** — the backend manages persistence.

---

## Test Results

```
155 passed, 0 failed  (as of last run)
```

Tests cover:
- Module 1: normalisation, tokenisation, language detection, preprocessing service
- Module 2: skill extraction, glossary, NOS mapping, similarity algorithms, NOS repository
- Module 3: weighted scoring, coverage, status derivation, twin building
- Module 4: source weights, feature extraction, conflict detection, SHA-256, duplicates
- Module 5: task value, ranking, next-task selection, variant selection, early stopping
- API: all endpoints, validation errors, unified pipeline

---

## Current Limitations

1. **Demo NOS data only** — must replace with official NCVET/NSQF data before production
2. **Rule-based skill extraction** — works well for the electrician trade; other trades need pattern extension
3. **Embedding uses TF-IDF fallback** — install `sentence-transformers` for better semantic matching
4. **No STT** — accepts text input directly; Whisper integration is a future step
5. **Evidence confidence = null** — the full Bayesian confidence engine is Module 7 (future)
6. **Final Commit/Abstain** — reserved for future Module 7; current module only checks coverage

---

## Future Integration (Modules 6–10)

This service is designed for extension:

| Future Module | Integration Point |
|---|---|
| Module 6 — Confidence Engine | Replace `evidence_confidence=null` with real values |
| Module 7 — Commit/Abstain | Replace `should_continue` with probabilistic decision |
| Module 8 — Assessor Calibration | Add calibration endpoint to evidence service |
| Module 9 — Skill-Gap Recommendations | New router using competency twin output |
| Module 10 — Final Certification | Separate service, reads from this service's output |
