"""
Unit and Integration Tests: Evidence Management & Storage APIs
"""

import io
import uuid
import pytest
from httpx import AsyncClient

from app.db.models.user import UserRole


@pytest.fixture
async def sample_worker_id(client: AsyncClient, assessor_auth) -> str:
    resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Evidence Test Worker", "trade": "electrician", "years_of_experience": 3},
        headers=assessor_auth["headers"],
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_evidence_metadata(client: AsyncClient, assessor_auth, sample_worker_id: str):
    payload = {
        "worker_id": sample_worker_id,
        "evidence_type": "SELF_DECLARATION",
        "source_type": "SELF",
        "description": "Worker claims 5 years experience installing ceiling fans.",
        "nos_id": "DEMO_NOS_001",
    }
    resp = await client.post("/api/v1/evidence", json=payload, headers=assessor_auth["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["worker_id"] == sample_worker_id
    assert data["evidence_type"] == "SELF_DECLARATION"
    assert data["verification_status"] == "UNVERIFIED"
    assert data["file_name"] is None


@pytest.mark.asyncio
async def test_upload_evidence_file_success(client: AsyncClient, assessor_auth, sample_worker_id: str):
    file_content = b"%PDF-1.4 Fake test certificate content for RPL assessment"
    files = {
        "file": ("certificate.pdf", io.BytesIO(file_content), "application/pdf")
    }
    data = {
        "evidence_type": "CERTIFICATE",
        "source_type": "EMPLOYER",
        "description": "Apprenticeship certificate from local contractor",
        "nos_id": "DEMO_NOS_002",
    }
    resp = await client.post(
        f"/api/v1/evidence/upload/{sample_worker_id}",
        files=files,
        data=data,
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 201
    result = resp.json()
    assert result["file_name"] == "certificate.pdf"
    assert result["verification_status"] == "UNVERIFIED"
    assert result["content_hash"] is not None
    assert len(result["content_hash"]) == 64  # SHA-256 length
    assert result["file_size_bytes"] == len(file_content)


@pytest.mark.asyncio
async def test_upload_disallowed_extension(client: AsyncClient, assessor_auth, sample_worker_id: str):
    files = {
        "file": ("malicious.exe", io.BytesIO(b"binary data"), "application/x-msdownload")
    }
    data = {
        "description": "Disallowed file upload test",
    }
    resp = await client.post(
        f"/api/v1/evidence/upload/{sample_worker_id}",
        files=files,
        data=data,
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_verify_evidence_by_assessor(client: AsyncClient, assessor_auth, sample_worker_id: str):
    # Submit evidence
    create_resp = await client.post(
        "/api/v1/evidence",
        json={
            "worker_id": sample_worker_id,
            "evidence_type": "CERTIFICATE",
            "source_type": "EMPLOYER",
            "description": "ITI certificate",
        },
        headers=assessor_auth["headers"],
    )
    ev_id = create_resp.json()["id"]

    # Assessor verifies
    verify_resp = await client.post(
        f"/api/v1/evidence/{ev_id}/verify",
        json={
            "verification_status": "VERIFIED",
            "verification_notes": "Certificate verified against state council registry",
        },
        headers=assessor_auth["headers"],
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verification_status"] == "VERIFIED"
    assert verify_resp.json()["verification_notes"] == "Certificate verified against state council registry"


@pytest.mark.asyncio
async def test_verify_evidence_forbidden_for_worker(client: AsyncClient, worker_auth, sample_worker_id: str):
    # Worker attempts to verify
    ev_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/evidence/{ev_id}/verify",
        json={"verification_status": "VERIFIED"},
        headers=worker_auth["headers"],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_download_evidence_file(client: AsyncClient, assessor_auth, sample_worker_id: str):
    file_bytes = b"Hello world evidence text file"
    files = {
        "file": ("test_doc.txt", io.BytesIO(file_bytes), "text/plain")
    }
    data = {
        "description": "Text document evidence",
    }
    upload_resp = await client.post(
        f"/api/v1/evidence/upload/{sample_worker_id}",
        files=files,
        data=data,
        headers=assessor_auth["headers"],
    )
    ev_id = upload_resp.json()["id"]

    # Download file
    download_resp = await client.get(
        f"/api/v1/evidence/{ev_id}/download",
        headers=assessor_auth["headers"],
    )
    assert download_resp.status_code == 200
    assert download_resp.content == file_bytes
