"""
KaushalTwin ML Service -- Complete End-to-End Demo (ASCII-safe)
"""
import sys
import json
import base64
import urllib.request

BASE = "http://localhost:8000"


def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.request.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
        return None


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())


def hr(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


hr("STEP 0 -- Health Check")
print(json.dumps(get("/health"), indent=2))

hr("STEP 1 -- Preprocess Hindi Transcript")
transcript = (
    "Main saat saalon se electrician ka kaam kar raha hoon. "
    "Ghar ki wiring karta hoon, switch aur pankha lagata hoon, "
    "aur line tester se fault dhundhta hoon. "
    "MCB bhi fit karta hoon aur DB board bhi dekhta hoon."
)
pre = post("/api/v1/ml/preprocess/text", {"text": transcript, "language": "hi"})
print(f"  Language    : {pre['language']}")
print(f"  Sentences   : {pre['sentence_count']}")
print(f"  Tokens      : {pre['token_count']}")

hr("STEP 2 -- Skill Extraction")
skill_res = post("/api/v1/ml/skills/extract", {
    "text": pre["normalized_text"],
    "language": pre["language"],
    "trade": "electrician",
    "provider": "demo",
})
print(f"  Skills found: {skill_res['count']}")
for s in skill_res["skills"]:
    print(f"    [{s['confidence']:.2f}] {s['normalized_name']}  <- '{s['evidence_text']}'")

hr("STEP 3 -- NOS Mapping (Candidates Only)")
nos_res = post("/api/v1/ml/nos/map", {"skills": skill_res["skills"], "top_k": 3})
for m in nos_res["mappings"]:
    skill = m["skill"]["normalized_name"]
    if m["candidates"]:
        top = m["candidates"][0]
        print(f"  {skill!r} => {top['nos_id']} [{top['title']}] sim={top['similarity']:.3f} [{top['mapping_status']}]")

hr("STEP 4 -- Competency Twin")
twin = post("/api/v1/ml/competency/twin", {
    "worker_id": "W001",
    "competencies": [
        {
            "nos_id": "DEMO_NOS_004", "mandatory": True, "importance": 1.0,
            "criteria": [
                {"name": "Identify isolation point",    "score": 3, "weight": 0.25, "max_score": 5},
                {"name": "Operate isolator",             "score": 4, "weight": 0.30, "max_score": 5},
                {"name": "Test for absence of voltage", "score": 4, "weight": 0.30, "max_score": 5},
                {"name": "Apply warning notices",        "score": None, "weight": 0.15, "max_score": 5},
            ],
        },
        {
            "nos_id": "DEMO_NOS_005", "mandatory": True, "importance": 0.9,
            "criteria": [
                {"name": "Safe approach",    "score": None, "weight": 0.20, "max_score": 5},
                {"name": "Instrument use",   "score": None, "weight": 0.30, "max_score": 5},
                {"name": "Fault identified", "score": None, "weight": 0.50, "max_score": 5},
            ],
        },
        {
            "nos_id": "DEMO_NOS_009", "mandatory": False, "importance": 0.5,
            "criteria": [
                {"name": "PPE selection", "score": 4, "weight": 0.35, "max_score": 5},
                {"name": "PPE worn",      "score": 5, "weight": 0.30, "max_score": 5},
                {"name": "Hazards ID",    "score": 4, "weight": 0.35, "max_score": 5},
            ],
        },
    ],
})
print(f"  Worker: {twin['worker_id']}  Total NOS: {twin['summary']['total_nos']}")
for c in twin["competencies"]:
    conf = c["evidence_confidence"] if c["evidence_confidence"] is not None else "null (future module)"
    print(f"  {c['nos_id']}  score={c['competency_score']}  coverage={c['evidence_coverage']:.0%}  "
          f"confidence={conf}  status={c['status']}")

hr("STEP 5 -- Evidence Conflict Detection")
cf = post("/api/v1/ml/evidence/conflict", {"evidence": [
    {"source": "SELF_DECLARATION", "supports": True,  "notes": "Claims 7 yrs experience"},
    {"source": "PRACTICAL",        "supports": False, "notes": "Incorrect isolation observed"},
]})
print(f"  Conflict  : {cf['conflict']}")
print(f"  Severity  : {cf['severity']}")
print(f"  Reason    : {cf['reason']}")

hr("STEP 6 -- File Hashing")
fake_content = b"DEMO_VIDEO_BYTES_FOR_INTEGRITY_CHECK"
h = post("/api/v1/ml/evidence/hash", {
    "content_base64": base64.b64encode(fake_content).decode()
})
print(f"  SHA-256   : {h['sha256']}")
print(f"  Status    : {h['integrity_status']}")

hr("STEP 7 -- Next Best Assessment Task")
states = [
    {"nos_id": c["nos_id"], "mandatory": c["mandatory"], "importance": c["importance"],
     "weight": c["importance"], "evidence_confidence": c["evidence_confidence"],
     "evidence_coverage": c["evidence_coverage"], "competency_score": c["competency_score"]}
    for c in twin["competencies"]
]
nt = post("/api/v1/ml/assessment/next-task", {"competency_states": states})
if nt and nt["selected_task"]:
    t = nt["selected_task"]
    print(f"  Selected  : {t['id']} -- {t['title']}")
    print(f"  Score     : {nt['priority_score']:.4f}")
    print(f"  Reasons   : {nt['reason']}")
    print(f"  Top alts  : {[a['id'] for a in nt.get('alternatives', [])[:3]]}")

hr("STEP 8 -- Task Variant Selection")
if nt and nt["selected_task"]:
    vr = post("/api/v1/ml/assessment/select-variant", {
        "task_id": nt["selected_task"]["id"], "seed": 42
    })
    if vr and vr.get("variant"):
        print(f"  Task    : {vr['task_title']}")
        print(f"  Variant : [{vr['variant']['code']}] {vr['variant']['label']}")
    else:
        print(f"  No variants defined for {nt['selected_task']['id']}")

hr("STEP 9 -- Should Assessment Continue?")
cont = post("/api/v1/ml/assessment/should-continue", {
    "competency_states": states, "coverage_threshold": 0.8
})
print(f"  Should continue : {cont['should_continue']}")
print(f"  Reason          : {cont['reason']}")
print(f"  Mandatory gaps  : {cont['mandatory_gaps']}")

hr("STEP 10 -- Unified Pipeline")
pipe = post("/api/v1/ml/pipeline/worker-assessment", {
    "worker_id": "W001",
    "language": "hi",
    "trade": "electrician",
    "transcript": transcript,
    "competencies": [],
    "evidence": [
        {"source": "SELF_DECLARATION", "supports": True},
        {"source": "PRACTICAL", "supports": False},
    ],
})
if pipe:
    print(f"  Skills extracted : {len(pipe['skills'])}")
    print(f"  NOS candidates   : {len(pipe['nos_candidates'])}")
    if pipe.get("evidence_features"):
        print(f"  Evidence conflict: {pipe['evidence_features']['conflict']}")
    print(f"  Should continue  : {pipe['continuation']['should_continue']}")
    if pipe.get("next_task"):
        print(f"  Next task        : {pipe['next_task']['id']}")

print("\n" + "="*60)
print("  END-TO-END DEMO COMPLETE")
print("="*60)
