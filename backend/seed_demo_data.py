"""
KaushalTwin — Database Seeder for SIH 2026 Evaluation Demo
Seeds MongoDB with demo assessor, admin, worker accounts, sample candidates,
active assessments, and verified evidence using deterministic UUIDs.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.user import UserRole
from app.db.mongodb import get_safe_mongodb_target

# Fixed namespace for deterministic, idempotent UUID generation
SEED_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")


def deterministic_id(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


async def seed():
    client = AsyncIOMotorClient(settings.MONGODB_URL, uuidRepresentation="standard")
    db = client[settings.MONGODB_DB_NAME]

    print(f"Connecting to {get_safe_mongodb_target(settings.MONGODB_URL)} | DB: {settings.MONGODB_DB_NAME}")

    # 1. Seed Users
    users_data = [
        {
            "id": deterministic_id("user:assessor@kaushaltwin.gov.in"),
            "name": "Lead Assessor Sharma",
            "email": "assessor@kaushaltwin.gov.in",
            "hashed_password": hash_password("assessor123"),
            "role": "ASSESSOR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("user:admin@kaushaltwin.gov.in"),
            "name": "System Administrator",
            "email": "admin@kaushaltwin.gov.in",
            "hashed_password": hash_password("admin123"),
            "role": "ADMIN",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("user:worker@kaushaltwin.gov.in"),
            "name": "Ramesh Kumar",
            "email": "worker@kaushaltwin.gov.in",
            "hashed_password": hash_password("worker123"),
            "role": "WORKER",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]

    for u in users_data:
        existing = await db.users.find_one({"email": u["email"]})
        if not existing:
            await db.users.insert_one(u)
            print(f"Created user: {u['email']} ({u['role']})")
        else:
            await db.users.update_one(
                {"email": u["email"]},
                {"$set": {"hashed_password": u["hashed_password"], "name": u["name"], "role": u["role"]}}
            )
            print(f"Updated user: {u['email']}")

    assessor_doc = await db.users.find_one({"email": "assessor@kaushaltwin.gov.in"})
    assessor_id = assessor_doc["id"]
    worker_user = await db.users.find_one({"email": "worker@kaushaltwin.gov.in"})
    worker_user_id = worker_user["id"]

    # 2. Seed Workers
    workers_data = [
        {
            "id": deterministic_id("worker:Suraj Kumar Nishad"),
            "user_id": assessor_id,
            "full_name": "Suraj Kumar Nishad",
            "phone": "+91 98765 43210",
            "email": "suraj.nishad@example.com",
            "trade": "Welding & Fabrication",
            "years_of_experience": 5,
            "education_level": "10th Standard",
            "declared_skills": ["Arc Welding", "Gas Cutting", "TIG Welding", "Blueprint Reading", "Safety Compliance"],
            "languages": ["Hindi", "Bhojpuri"],
            "experience_summary": "5 years informal experience in structural welding at local engineering fabrication workshop.",
            "education_summary": "Matriculation (10th pass), informal apprenticeship under master welder.",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("worker:Ramesh Kumar Verma"),
            "user_id": worker_user_id,
            "full_name": "Ramesh Kumar Verma",
            "phone": "+91 98111 22334",
            "email": "worker@kaushaltwin.gov.in",
            "trade": "Electrical Installation",
            "years_of_experience": 6,
            "education_level": "12th Standard",
            "declared_skills": ["Domestic Wiring", "MCB Distribution", "Inverter Installation", "Fault Finding", "Earth Testing"],
            "languages": ["Hindi", "English"],
            "experience_summary": "6 years residential and light commercial wiring contractor experience.",
            "education_summary": "12th Standard, on-the-job training.",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("worker:Sunita Devi"),
            "user_id": assessor_id,
            "full_name": "Sunita Devi",
            "phone": "+91 97222 33445",
            "email": "sunita.devi@example.com",
            "trade": "Solar PV Technician",
            "years_of_experience": 3,
            "education_level": "10th Standard",
            "declared_skills": ["Solar Panel Mounting", "Inverter Wiring", "Battery Bank Maintenance", "Tilt Angle Alignment"],
            "languages": ["Hindi"],
            "experience_summary": "3 years installing rooftop solar arrays with rural electrification contractor.",
            "education_summary": "10th Standard.",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]

    for w in workers_data:
        existing = await db.workers.find_one({"full_name": w["full_name"]})
        if not existing:
            await db.workers.insert_one(w)
            print(f"Created worker: {w['full_name']} ({w['trade']})")
        else:
            await db.workers.update_one(
                {"full_name": w["full_name"]},
                {"$set": {
                    "trade": w["trade"],
                    "years_of_experience": w["years_of_experience"],
                    "declared_skills": w["declared_skills"],
                    "experience_summary": w["experience_summary"],
                    "user_id": w["user_id"],
                    "email": w.get("email"),
                    "phone": w.get("phone"),
                }}
            )

    suraj = await db.workers.find_one({"full_name": "Suraj Kumar Nishad"})
    ramesh = await db.workers.find_one({"full_name": "Ramesh Kumar Verma"})

    # 3. Seed Assessments
    assessments_data = [
        {
            "id": deterministic_id("assessment:Suraj Kumar Nishad"),
            "worker_id": suraj["id"],
            "assessor_id": assessor_id,
            "trade": "Welding & Fabrication",
            "status": "READY_FOR_REVIEW",
            "notes": "RPL walk-in assessment candidate with extensive practical fabrication background.",
            "candidate_competencies": [
                {
                    "nos_id": "CSC/N0204",
                    "competency_name": "Perform SMAW / MMAW (Arc) Welding",
                    "score": 0.88,
                    "evidence_count": 2,
                },
                {
                    "nos_id": "CSC/N1335",
                    "competency_name": "Workplace Health, Safety & Environmental Protocols",
                    "score": 0.92,
                    "evidence_count": 2,
                },
                {
                    "nos_id": "CSC/N0205",
                    "competency_name": "Engineering Drawing & Joint Blueprint Interpretation",
                    "score": 0.65,
                    "evidence_count": 1,
                },
                {
                    "nos_id": "CSC/N0206",
                    "competency_name": "Visual Inspection & Weld Defect Rectification",
                    "score": 0.78,
                    "evidence_count": 1,
                },
            ],
            "tasks": [
                {
                    "id": str(deterministic_id("task:suraj:smaw_test")),
                    "task_name": "Butt Joint Horizontal 3G SMAW Test",
                    "description": "Execute single V-butt weld on 10mm MS plate following standard WPS and safety protocols.",
                    "status": "COMPLETED",
                    "score": 85,
                    "priority_score": 0.95,
                    "comments": "Uniform bead width and proper root penetration observed.",
                },
                {
                    "id": str(deterministic_id("task:suraj:blueprint")),
                    "task_name": "Joint Blueprint Measurement & Tolerances",
                    "description": "Interpret welding symbols and mark workpiece according to technical drawings.",
                    "status": "PENDING",
                    "priority_score": 0.88,
                },
            ],
            "ai_recommendation": "RECOMMEND_CERTIFICATION",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("assessment:Ramesh Kumar Verma"),
            "worker_id": ramesh["id"],
            "assessor_id": assessor_id,
            "trade": "Electrical Installation",
            "status": "IN_PROGRESS",
            "notes": "Domestic electrical installer seeking formal NSQF Level 4 certification.",
            "candidate_competencies": [
                {
                    "nos_id": "ELE/N5801",
                    "competency_name": "Residential Distribution & Circuit Wiring",
                    "score": 0.82,
                    "evidence_count": 1,
                },
                {
                    "nos_id": "ELE/N5802",
                    "competency_name": "Earthing & Fault Protection Setup",
                    "score": 0.75,
                    "evidence_count": 1,
                },
            ],
            "tasks": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]

    for a in assessments_data:
        existing = await db.assessments.find_one({"worker_id": a["worker_id"]})
        if not existing:
            await db.assessments.insert_one(a)
            print(f"Created assessment for worker: {a['trade']}")
        else:
            await db.assessments.update_one(
                {"worker_id": a["worker_id"]},
                {"$set": {
                    "status": a["status"],
                    "candidate_competencies": a["candidate_competencies"],
                    "tasks": a["tasks"],
                    "updated_at": datetime.now(timezone.utc)
                }}
            )

    # 4. Seed Evidence
    evidence_data = [
        {
            "id": deterministic_id("evidence:suraj:work_sample"),
            "worker_id": suraj["id"],
            "evidence_type": "WORK_SAMPLE",
            "source_type": "DIRECT_ENTRY",
            "description": "Welded steel frame corner joint using Shielded Metal Arc Welding (SMAW).",
            "nos_id": "CSC/N0204",
            "verification_status": "VERIFIED",
            "verification_notes": "Clean weld bead with no porosity or undercut observed upon visual inspection.",
            "verified_by_id": assessor_id,
            "verified_by_user_id": assessor_id,
            "verified_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("evidence:suraj:photograph"),
            "worker_id": suraj["id"],
            "evidence_type": "PHOTOGRAPH",
            "source_type": "UPLOAD",
            "description": "Candidate wearing full PPE (welding shield, leather apron, heat-resistant gloves).",
            "nos_id": "CSC/N1335",
            "verification_status": "VERIFIED",
            "verification_notes": "Adheres to workshop safety standard ISO 45001.",
            "verified_by_id": assessor_id,
            "verified_by_user_id": assessor_id,
            "verified_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {
            "id": deterministic_id("evidence:ramesh:experience"),
            "worker_id": ramesh["id"],
            "uploaded_by_id": worker_user_id,
            "evidence_type": "EXPERIENCE_DECLARATION",
            "source_type": "DIRECT_ENTRY",
            "description": "Supervisor reference letter from Verma Electricals certifying 6 years site experience.",
            "nos_id": "ELE/N5801",
            "verification_status": "PENDING_REVIEW",
            "verification_notes": "Awaiting assessor verification of supervisor credentials.",
            "verified_by_id": None,
            "verified_by_user_id": None,
            "verified_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    ]

    for ev in evidence_data:
        existing = await db.evidence.find_one({"description": ev["description"]})
        if not existing:
            await db.evidence.insert_one(ev)
            print(f"Created evidence item: {ev['description'][:40]}...")
        else:
            await db.evidence.update_one(
                {"description": ev["description"]},
                {"$set": {
                    "verification_status": ev["verification_status"],
                    "verification_notes": ev["verification_notes"],
                    "verified_by_id": ev.get("verified_by_id"),
                    "verified_by_user_id": ev.get("verified_by_user_id"),
                    "verified_at": ev.get("verified_at"),
                }}
            )

    # Ensure worker user_id link is saved for Ramesh
    await db.workers.update_one(
        {"full_name": "Ramesh Kumar Verma"},
        {"$set": {"user_id": worker_user_id}}
    )

    print("Seeding complete! All demo data successfully populated in MongoDB.")


if __name__ == "__main__":
    asyncio.run(seed())
