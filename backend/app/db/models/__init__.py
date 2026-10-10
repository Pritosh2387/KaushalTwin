"""
KaushalTwin Backend — DB Models Package

Import ALL models here so that Alembic's autogenerate picks up every table.
"""

from app.db.models.user import User, UserRole  # noqa: F401
from app.db.models.worker import WorkerProfile, AssessmentStatus  # noqa: F401
from app.db.models.assessment import (  # noqa: F401
    Assessment,
    AssessmentLifecycle,
    AssessmentTask,
    TaskStatus,
    TaskSelectionSource,
)
from app.db.models.evidence import EvidenceRecord, EvidenceType, EvidenceVerificationStatus  # noqa: F401
from app.db.models.ai_run import AIAssessmentRun, RunStatus  # noqa: F401
from app.db.models.decision import AssessorDecision, DecisionAction  # noqa: F401
from app.db.models.audit import AuditEvent  # noqa: F401
