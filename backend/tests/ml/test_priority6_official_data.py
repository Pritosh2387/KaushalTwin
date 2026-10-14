"""
Tests: Module 2 — Priority 6 Official NOS/QP Data Acquisition & Integration
Verifies acquisition workflow, raw artifact preservation, cryptographic provenance verification,
NOSRepository official loading, demo fallback, and evidence-grounded multi-trade mapping.

Zero-Network Compliance: All HTTP requests are mocked with httpx.MockTransport or test fixtures.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import httpx
import pytest

from ml.ingestion.acquisition import (
    NQRAcquisitionService,
    DEFAULT_TARGET_QUALIFICATIONS,
    _clean_text,
)
from ml.ingestion.pipeline import (
    NOSIngestionPipeline,
    IngestionConfig,
    generate_attestation_signature,
    verify_attestation_signature,
)
from ml.nos_repository import get_nos_repository, NOSRepository
from ml.services.skill_service import (
    map_skills_to_nos,
    set_active_nos_dataset,
    get_active_nos_dataset_info,
    invalidate_nos_cache,
    get_all_nos,
    get_nos_by_id,
)

SAMPLE_QUAL_HTML = """
<!DOCTYPE html>
<html>
<head><title>Plumbing Supervisor</title></head>
<body>
    <h1>Plumbing Supervisor</h1>
    <div>NQR Code: 2022/PLUM/WMPS/05462</div>
    <h2>Job Description</h2>
    <p>A Plumbing Supervisor is responsible for planning, scheduling, organising and directing plumbing installations and repairs.</p>
    <table>
        <tr>
            <th>National Occupation Standards (NOS)/Module</th>
            <th>NOS Code</th>
            <th>Mandatory/ Optional</th>
            <th>Estimated size (Hours)</th>
            <th>Level</th>
        </tr>
        <tr>
            <td>Prepare for a Plumbing Assignment</td>
            <td>PSC/N0143</td>
            <td>Mandatory</td>
            <td>180</td>
            <td>Level 5</td>
        </tr>
        <tr>
            <td>Inspect the Plumbing Work to Ensure Compliances</td>
            <td>PSC/N0144</td>
            <td>Mandatory</td>
            <td>195</td>
            <td>Level 5</td>
        </tr>
        <tr>
            <td>Ensure Effective Repair and Maintenance of Plumbing System</td>
            <td>PSC/N0145</td>
            <td>Mandatory</td>
            <td>210</td>
            <td>Level 5</td>
        </tr>
        <tr>
            <td>Employability Skills (90 Hours)</td>
            <td>DGT/VSQ/N0103</td>
            <td>Mandatory</td>
            <td>90</td>
            <td>Level 5</td>
        </tr>
    </table>
</body>
</html>
"""


@pytest.fixture(autouse=True)
def restore_demo_state():
    """Ensure repository state is reset to demo after each test to avoid test contamination."""
    yield
    invalidate_nos_cache()
    repo = get_nos_repository()
    repo.load_demo_data(refresh=True)


# ---------------------------------------------------------------------------
# 1. Official Data Sources & Text Sanitization Tests
# ---------------------------------------------------------------------------

class TestOfficialSourceDiscovery:
    def test_target_qualifications_cover_all_four_trades(self):
        """Verify target qualifications catalog covers electrician, plumber, welder, and mason."""
        trades = {cfg["trade"] for cfg in DEFAULT_TARGET_QUALIFICATIONS.values()}
        assert "electrician" in trades
        assert "plumber" in trades
        assert "welder" in trades
        assert "mason" in trades

        for name, cfg in DEFAULT_TARGET_QUALIFICATIONS.items():
            assert cfg["id"] > 0
            assert cfg["url"].startswith("https://www.nqr.gov.in/qualifications/")
            assert len(cfg["keywords"]) >= 5

    def test_text_cleaner_normalizes_ligatures_and_whitespace(self):
        """Verify unicode typographic ligatures and irregular spaces are normalized."""
        raw_text = "Fixing \ufb01re hazards, \ufb02ush valves & a\ufb00ecting connections.\u00a0\u00a0\nDone."
        cleaned = _clean_text(raw_text)
        assert "\ufb01" not in cleaned
        assert "\ufb02" not in cleaned
        assert "\ufb00" not in cleaned
        assert "Fixing fire hazards, flush valves & affecting connections. Done." == cleaned

    def test_pipeline_recognizes_nqr_as_allowlisted_domain(self):
        """Verify nqr.gov.in is recognized by the ingestion pipeline domain allowlist."""
        pipeline = NOSIngestionPipeline()
        assert pipeline._is_source_domain_allowlisted("https://www.nqr.gov.in/qualifications/2512") is True
        assert pipeline._is_source_domain_allowlisted("https://subdomain.ncvet.gov.in/standards") is True
        assert pipeline._is_source_domain_allowlisted("https://untrusted-fake-nos.com/data") is False


# ---------------------------------------------------------------------------
# 2. HTML Parsing & Raw Artifact Storage Tests (Zero-Network)
# ---------------------------------------------------------------------------

class TestNQRAcquisitionParsing:
    def test_parse_qualification_html_extracts_metadata_and_nos_items(self):
        """Verify HTML parser extracts title, NQR code, job description, and NOS rows correctly."""
        service = NQRAcquisitionService()
        parsed = service.parse_qualification_html(SAMPLE_QUAL_HTML, qualification_id=2512)

        assert parsed["qualification_id"] == 2512
        assert parsed["title"] == "Plumbing Supervisor"
        assert parsed["nqr_code"] == "2022/PLUM/WMPS/05462"
        assert "A Plumbing Supervisor is responsible for planning" in parsed["description"]
        assert len(parsed["nos_items"]) == 4

        nos_codes = [item["code"] for item in parsed["nos_items"]]
        assert "PSC/N0143" in nos_codes
        assert "PSC/N0144" in nos_codes
        assert "PSC/N0145" in nos_codes
        assert "DGT/VSQ/N0103" in nos_codes

    def test_fetch_qualification_raw_with_mock_transport(self, tmp_path):
        """Verify mock HTTP retrieval stores raw artifact and computes cryptographic SHA-256 hash."""
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=SAMPLE_QUAL_HTML, headers={"content-type": "text/html"})

        mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
        service = NQRAcquisitionService(raw_storage_dir=tmp_path, http_client=mock_client)

        result = service.fetch_qualification_raw(qualification_id=2512)

        assert result["qualification_id"] == 2512
        assert result["from_cache"] is False

        raw_file = Path(result["raw_file_path"])
        meta_file = Path(result["meta_file_path"])

        assert raw_file.exists()
        assert meta_file.exists()

        expected_hash = hashlib.sha256(SAMPLE_QUAL_HTML.encode("utf-8")).hexdigest()
        assert result["metadata"]["content_hash"] == expected_hash
        assert result["metadata"]["http_status"] == 200
        assert result["metadata"]["source_url"] == "https://www.nqr.gov.in/qualifications/2512"

        # Subsequent fetch should load from cache
        cached_result = service.fetch_qualification_raw(qualification_id=2512, force_refresh=False)
        assert cached_result["from_cache"] is True


# ---------------------------------------------------------------------------
# 3. Normalization, Deduplication, and Schema Conformity Tests
# ---------------------------------------------------------------------------

class TestNormalizationAndDeduplication:
    def test_normalize_nos_records_filters_employability_and_maps_trade(self):
        """Verify DGT generic skills are filtered out and trade-specific NOS records are produced."""
        service = NQRAcquisitionService()
        parsed = service.parse_qualification_html(SAMPLE_QUAL_HTML, qualification_id=2512)
        records = service.normalize_nos_records([parsed], trade_overrides={2512: "plumber"})

        # DGT/VSQ/N0103 should be excluded, leaving 3 plumbing standards
        assert len(records) == 3
        assert all(r.trade == "plumber" for r in records)
        assert all(r.source_type == "OFFICIAL" for r in records)
        assert all(r.source_domain_allowlisted is True for r in records)

        record_0 = records[0]
        assert record_0.nos_id == "PSC/N0143"
        assert record_0.id == "PSC/N0143"
        assert record_0.code == "PSC/N0143"
        assert record_0.title == "Prepare for a Plumbing Assignment"
        assert len(record_0.performance_criteria) >= 2
        assert len(record_0.keywords) >= 3

    def test_duplicate_nos_codes_are_safely_deduplicated(self):
        """Verify identical NOS codes in multiple qualifications are deduplicated."""
        service = NQRAcquisitionService()
        parsed1 = service.parse_qualification_html(SAMPLE_QUAL_HTML, qualification_id=2512)
        parsed2 = service.parse_qualification_html(SAMPLE_QUAL_HTML, qualification_id=2512)

        records = service.normalize_nos_records([parsed1, parsed2])
        nos_ids = [r.nos_id for r in records]
        assert len(nos_ids) == len(set(nos_ids))


# ---------------------------------------------------------------------------
# 4. Ingestion Pipeline & Reviewer Attestation Verification Tests
# ---------------------------------------------------------------------------

class TestAcquisitionPipelineIntegration:
    def test_acquire_dataset_workflow_with_mock_client(self, tmp_path):
        """Verify complete acquisition workflow creates verified official dataset in tmp_path."""
        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text=SAMPLE_QUAL_HTML, headers={"content-type": "text/html"})

        mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
        raw_dir = tmp_path / "raw"
        out_file = tmp_path / "test_official_nos.json"

        service = NQRAcquisitionService(raw_storage_dir=raw_dir, http_client=mock_client)
        summary = service.acquire_official_dataset(
            qualification_ids=[2512],
            output_file=out_file,
            reviewer_id="ncvet_admin_01",
        )

        assert summary["status"] == "SUCCESS"
        assert summary["provenance_verified"] is True
        assert summary["valid_records"] == 3
        assert summary["trades_covered"]["plumber"] == 3
        assert out_file.exists()

        # Load file and inspect
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["nos_records"]) == 3
        assert data["_metadata"]["source_type"] == "OFFICIAL"
        assert data["_metadata"]["attested_by"] == "ncvet_admin_01"


# ---------------------------------------------------------------------------
# 5. NOSRepository Official Loading & Demo Fallback Tests
# ---------------------------------------------------------------------------

class TestNOSRepositoryOfficialIntegration:
    def test_load_official_data_sets_official_status(self):
        """Verify loading official dataset sets is_official_data() to True."""
        repo = get_nos_repository()
        records = repo.load_official_data(refresh=True)

        assert len(records) > 0
        assert repo.is_official_data() is True
        dist = repo.get_source_type_distribution()
        assert dist.get("OFFICIAL", 0) > 0

    def test_load_demo_data_sets_demo_status(self):
        """Verify loading demo dataset sets is_official_data() to False."""
        repo = get_nos_repository()
        records = repo.load_demo_data(refresh=True)

        assert len(records) > 0
        assert repo.is_official_data() is False
        dist = repo.get_source_type_distribution()
        assert dist.get("DEMO", 0) > 0

    def test_set_active_dataset_toggle(self):
        """Verify set_active_dataset switches seamlessly between official and demo."""
        repo = get_nos_repository()

        repo.set_active_dataset("official")
        assert repo.is_official_data() is True

        repo.set_active_dataset("demo")
        assert repo.is_official_data() is False

    def test_graceful_fallback_when_official_file_missing(self, monkeypatch, tmp_path):
        """Verify repository falls back to demo data when official file does not exist."""
        repo = NOSRepository()
        monkeypatch.setattr(repo, "_official_data_path", tmp_path / "non_existent.json")

        records = repo.load_official_data()
        assert len(records) > 0
        assert repo.is_official_data() is False
        assert any(r.get("source_type") == "DEMO" for r in records)


# ---------------------------------------------------------------------------
# 6. Skill Service Mapping with Official Standards
# ---------------------------------------------------------------------------

class TestSkillMappingWithOfficialData:
    def test_official_dataset_mapping_multi_trade(self):
        """
        Verify that worker skills across electrician, plumber, welder, and mason
        map to genuine official NOS standards with OFFICIAL source_type.
        """
        info = set_active_nos_dataset("official")
        assert info["record_count"] >= 20

        repo = get_nos_repository()
        assert repo.is_official_data() is True

        test_skills = [
            {
                "skill_name": "soldering wire joints",
                "normalized_name": "soldering wire joints",
                "confidence": 0.9,
                "evidence_text": "I prepare and solder wire joints for domestic wiring",
                "trade": "electrician",
            },
            {
                "skill_name": "pipe repair and maintenance",
                "normalized_name": "pipe repair and maintenance",
                "confidence": 0.88,
                "evidence_text": "I repair leaking pipes and service sanitary fittings",
                "trade": "plumber",
            },
            {
                "skill_name": "metal arc welding",
                "normalized_name": "metal arc welding",
                "confidence": 0.92,
                "evidence_text": "I do manual metal arc welding on steel structures",
                "trade": "welder",
            },
            {
                "skill_name": "masonry hand tools",
                "normalized_name": "masonry hand tools",
                "confidence": 0.85,
                "evidence_text": "I use trowels and hand tools for brick laying",
                "trade": "mason",
            },
        ]

        mappings = map_skills_to_nos(test_skills, top_k=2)
        assert len(mappings) == 4

        # Electrician mapping
        elec_map = mappings[0]
        assert elec_map["candidates"][0]["source_type"] == "OFFICIAL"
        assert elec_map["candidates"][0]["nos_id"] == "CON/0805/OC2"
        assert "soldering" in elec_map["candidates"][0]["title"].lower()

        # Plumber mapping
        plumb_map = mappings[1]
        assert plumb_map["candidates"][0]["source_type"] == "OFFICIAL"
        assert plumb_map["candidates"][0]["nos_id"] == "PSC/N0145"

        # Welder mapping
        weld_map = mappings[2]
        assert weld_map["candidates"][0]["source_type"] == "OFFICIAL"
        assert weld_map["candidates"][0]["nos_id"] == "CSC/N0204"

        # Mason mapping
        mason_map = mappings[3]
        assert mason_map["candidates"][0]["source_type"] == "OFFICIAL"
        assert mason_map["candidates"][0]["nos_id"] == "CON/N0105"

    def test_id_and_nos_id_backward_compatibility(self):
        """Verify both 'id' and 'nos_id' fields are populated on official records."""
        set_active_nos_dataset("official")
        all_records = get_all_nos()
        assert len(all_records) > 0
        for r in all_records:
            assert "id" in r
            assert "nos_id" in r
            assert r["id"] == r["nos_id"]

        sample_id = all_records[0]["nos_id"]
        found = get_nos_by_id(sample_id)
        assert found is not None
        assert found["nos_id"] == sample_id
        assert found["id"] == sample_id

    def test_abstention_on_irrelevant_skill_with_official_data(self):
        """Verify system abstains when similarity is below threshold even with official data."""
        set_active_nos_dataset("official")
        irrelevant_skill = [{
            "skill_name": "baking sourdough artisan bread in wood oven",
            "normalized_name": "bread baking",
            "evidence_text": "kneading sourdough and baking loaves",
            "confidence": 0.95,
            "trade": "general",
        }]

        mapping = map_skills_to_nos(irrelevant_skill, min_similarity_threshold=0.6)
        assert len(mapping) == 1
        assert mapping[0]["abstained"] is True
        reason = mapping[0]["abstention_reason"].lower()
        assert "insufficient evidence" in reason or "threshold" in reason
