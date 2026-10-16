"""
KaushalTwin Main Backend — Complete End-to-End Workflow Demonstration

This script demonstrates the full Section 21 RPL Assessment workflow
using real HTTP requests against the running KaushalTwin Main Backend (port 8001):

1. Register / Login Assessor
2. Create Worker Profile (walk-in candidate support)
3. Create Assessment & start lifecycle (DRAFT -> IN_PROGRESS)
4. Submit Evidence Record & verify it
5. Trigger AI Assessment Run (calls ML service on port 8000 via backend)
6. Retrieve AI results & competency profile
7. Request Adaptive Next-Best-Task recommendation
8. Submit assessor task evaluation & score
9. Submit independent human assessor decision (AI advisory only)
10. Generate full structured assessment report & audit timeline
"""

import os
import sys
import json
import urllib.request
import urllib.error

BACKEND_BASE = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")


def print_step(title: str):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")


def request(method: str, path: str, payload=None, token=None):
    if path.startswith("/health"):
        url = BACKEND_BASE.replace("/api/v1", "") + path
    else:
        url = f"{BACKEND_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"  HTTP Error {e.code}: {err_body}")
        return None
    except Exception as e:
        print(f"  Connection error: {e}")
        return None


def main():
    print_step("KAUSHALTWIN RPL PLATFORM — UNIFIED BACKEND & MONGODB DEMO")

    # 1. Health check
    print("\n[1] Checking backend health...")
    health = request("GET", "/health")
    print(f"  Backend status: {health}")

    # 2. Register & Login Assessor
    email = "assessor_demo@kaushaltwin.gov.in"
    password = "AssessorPassword123!"
    print(f"\n[2] Registering / Logging in Assessor ({email})...")
    reg = request("POST", "/auth/register", {
        "name": "Certified Assessor Sharma",
        "email": email,
        "password": password,
        "role": "ASSESSOR",
    })
    login = request("POST", "/auth/login", {"email": email, "password": password})
    if not login or "access_token" not in login:
        print("  Failed to obtain token. Exiting.")
        return
    token = login["access_token"]
    print("  Assessor authenticated. JWT Token received.")

    # 3. Create or find Worker Profile
    print("\n[3] Checking / Creating Worker Profile (Ramesh Kumar, Electrician)...")
    workers_list = request("GET", "/workers?limit=50", token=token)
    existing_worker = None
    if workers_list and isinstance(workers_list.get("items"), list):
        for w in workers_list["items"]:
            if w.get("full_name") == "Ramesh Kumar" and w.get("trade") == "electrician":
                existing_worker = w
                break

    if existing_worker:
        worker = existing_worker
        print(f"  Existing Worker Profile Reused: ID={worker['id']}, Trade={worker['trade']}")
    else:
        worker = request("POST", "/workers", {
            "full_name": "Ramesh Kumar",
            "trade": "electrician",
            "years_of_experience": 6,
            "experience_summary": "Main 6 saal se residential wiring, MCB distribution, aur fan installation karta hoon.",
            "education_summary": "10th pass, on-the-job informal training.",
        }, token=token)
        if not worker:
            return
        print(f"  Worker Profile Created: ID={worker['id']}, Trade={worker['trade']}, Exp={worker['years_of_experience']} yrs")
    worker_id = worker["id"]

    # 4. Create Assessment (or resume existing active assessment)
    print("\n[4] Creating / Resuming Assessment Session...")
    assessment = request("POST", "/assessments", {
        "worker_id": worker_id,
        "trade": "electrician",
        "notes": "RPL Assessment candidate registered at ITI Kanpur center.",
    }, token=token)
    assessment_id = assessment["id"]
    print(f"  Assessment Session Active: ID={assessment_id}, Status={assessment['status']}")

    # Start assessment if still in DRAFT
    if assessment.get("status") == "DRAFT":
        started = request("POST", f"/assessments/{assessment_id}/start", token=token)
        print(f"  Assessment Started: Status={started['status']}, StartedAt={started['started_at']}")

    # 5. Submit Evidence (or find existing)
    print("\n[5] Submitting / Checking Evidence...")
    worker_ev = request("GET", f"/workers/{worker_id}/evidence", token=token)
    ev_items = worker_ev.get("items", []) if isinstance(worker_ev, dict) else (worker_ev or [])
    existing_ev = None
    for item in ev_items:
        if item.get("evidence_type") == "SELF_DECLARATION":
            existing_ev = item
            break

    if existing_ev:
        ev_id = existing_ev["id"]
        print(f"  Existing Evidence Record Reused: ID={ev_id}, Status={existing_ev['verification_status']}")
    else:
        ev = request("POST", "/evidence", {
            "worker_id": worker_id,
            "assessment_id": assessment_id,
            "evidence_type": "SELF_DECLARATION",
            "source_type": "SELF",
            "description": "Candidate self-declaration of 6 years residential wiring experience.",
            "nos_id": "DEMO_NOS_004",
        }, token=token)
        ev_id = ev["id"]
        print(f"  Evidence Record ID: {ev_id}, Status={ev['verification_status']}")

    # Assessor reviews and verifies evidence
    print("\n[6] Assessor verifies evidence...")
    verified = request("POST", f"/evidence/{ev_id}/verify", {
        "verification_status": "VERIFIED",
        "verification_notes": "Assessor confirmed practical familiarity with DB board wiring via onsite inspection.",
    }, token=token)
    print(f"  Verification Updated: Status={verified.get('verification_status') if verified else 'Unchanged'}")

    # 6. Check ML Service & Run AI Pipeline
    print("\n[7] Triggering ML Pipeline via Backend (/assessments/{id}/analyze)...")
    ml_check = request("GET", "/ml/health", token=token)
    if ml_check and ml_check.get("status") == "ok":
        ai_run = request("POST", f"/assessments/{assessment_id}/analyze", {
            "language": "hi",
            "claim_for_explanation": "Experienced electrician in house wiring",
        }, token=token)
        if ai_run:
            print(f"  AI Run ID: {ai_run['id']}")
            print(f"  AI Recommendation: {ai_run['recommendation']}")
            print(f"  AI Run Status: {ai_run['run_status']}")
    else:
        print("  Notice: ML Service not running on port 8000. Skipping live ML invocation.")

    # 7. Assessor creates practical task & submits score
    print("\n[8] Assessor assigns practical assessment task...")
    task = request("POST", f"/assessments/{assessment_id}/tasks", {
        "title": "Demonstrate Safe Isolation and Line Testing",
        "description": "Candidate must safely isolate circuit using line tester and MCB disconnect.",
        "target_nos_id": "DEMO_NOS_004",
        "selection_source": "ASSESSOR_ASSIGNED",
    }, token=token)
    task_id = task["id"]
    print(f"  Task Created: ID={task_id}, Title={task['title']}")

    print("\n[9] Submitting Task Evaluation Result...")
    scored = request("POST", f"/assessments/{assessment_id}/tasks/{task_id}/result", {
        "score": 88.0,
        "assessor_comments": "Candidate followed safe isolation steps accurately and tested dead.",
        "evidence_references": [ev_id],
    }, token=token)
    print(f"  Task Evaluated: Status={scored['status']}, Score={scored['score']}%")

    # 8. Complete assessment review state
    print("\n[10] Marking assessment ready for final review...")
    completed = request("POST", f"/assessments/{assessment_id}/complete", token=token)
    print(f"  Assessment Lifecycle: Status={completed['status']}")

    # 9. Independent Assessor Decision (Human Authority)
    print("\n[11] Assessor Submits Independent Final Decision (Human Authority)...")
    decision = request("POST", f"/assessments/{assessment_id}/decision", {
        "action": "ACCEPT_RECOMMENDATION",
        "comments": "Candidate proved solid practical skills and safety compliance under direct observation.",
    }, token=token)
    print(f"  Final Decision Action: {decision['action']}")
    print(f"  Comments: {decision['comments']}")

    # 10. Generate Final Structured Report
    print("\n[12] Generating Complete Assessment Report & Audit Timeline...")
    report = request("GET", f"/assessments/{assessment_id}/report", token=token)
    if report:
        print(f"\n{'='*70}\n  STRUCTURED ASSESSMENT REPORT SUMMARY\n{'='*70}")
        print(f"  Worker: {report['worker']['full_name']} ({report['worker']['trade']})")
        print(f"  Experience: {report['worker']['years_of_experience']} years")
        print(f"  Assessment Status: {report['assessment']['status']}")
        print(f"  Evidence Verified: {report['evidence_summary']['verified']} / {report['evidence_summary']['total']}")
        print(f"  Tasks Completed: {len(report['tasks'])}")
        print(f"  Final Assessor Decision: {report['latest_decision']['action'] if report['latest_decision'] else 'None'}")
        print(f"  Audit Timeline Events: {len(report['audit_timeline'])}")
        print(f"  Advisory Note: {report['note']}")
        print(f"{'='*70}\n  END-TO-END DEMO FINISHED SUCCESSFULLY\n{'='*70}")


if __name__ == "__main__":
    main()
