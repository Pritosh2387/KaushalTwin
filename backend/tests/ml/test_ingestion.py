"""
Tests: Module 2 — NOS/QP Ingestion Pipeline & Repository Integration
Forensic verification of Priority 4 requirements.
"""

import json
import hashlib
import pytest
import tempfile
from pathlib import Path
import httpx

from ml.ingestion.pipeline import (
    NOSIngestionPipeline,
    IngestionConfig,
    NOSRecord,
    IngestionResult,
    ChangeReport,
    generate_attestation_signature,
    verify_attestation_signature,
)
from ml.nos_repository import NOSRepository, get_nos_repository
from ml.services.skill_service import (
    search_nos,
    map_skills_to_nos,
    get_all_nos,
    get_nos_by_id,
    invalidate_nos_cache,
)


@pytest.fixture
def sample_valid_record():
    return {
        "nos_id": "TEST_NOS_001",
        "id": "TEST_NOS_001",
        "code": "TEST_NOS_001",
        "title": "Industrial Motor Maintenance",
        "description": "Inspect, maintain, and overhaul three-phase induction motors.",
        "mandatory": True,
        "weight": 0.9,
        "trade": "electrician",
        "source_type": "USER_PROVIDED_UNVERIFIED",
        "performance_criteria": [
            "Checks winding insulation resistance with megohmmeter",
            "Replaces worn bearings following standard clearance specs"
        ],
        "keywords": ["motor", "maintenance", "megohmmeter", "bearings", "three-phase"]
    }


@pytest.fixture
def sample_json_file(sample_valid_record, tmp_path):
    file_path = tmp_path / "valid_nos.json"
    file_path.write_text(json.dumps([sample_valid_record]), encoding="utf-8")
    return file_path


class TestNOSIngestionPipeline:
    def test_ingest_valid_json(self, sample_json_file):
        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_json(sample_json_file)

        assert result.total_records == 1
        assert result.valid_records == 1
        assert result.invalid_records == 0
        assert len(records) == 1

        rec = records[0]
        assert rec.nos_id == "TEST_NOS_001"
        assert rec.id == "TEST_NOS_001"
        assert rec.title == "Industrial Motor Maintenance"
        assert rec.source_type == "USER_PROVIDED_UNVERIFIED"
        assert rec.content_hash is not None
        assert result.output_dataset_hash is not None

    def test_ingest_valid_csv(self, tmp_path):
        csv_file = tmp_path / "valid_nos.csv"
        csv_content = (
            "nos_id,code,title,description,mandatory,weight,trade,source_type,performance_criteria,keywords\n"
            "CSV_NOS_001,CSV_NOS_001,Cable Termination,Terminate LV cables,True,0.85,electrician,USER_PROVIDED_UNVERIFIED,\"['Crimps lugs', 'Applies heat shrink']\",\"['cable', 'crimp']\"\n"
        )
        csv_file.write_text(csv_content, encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_csv(csv_file)

        assert result.total_records == 1
        assert result.valid_records == 1
        assert len(records) == 1
        assert records[0].nos_id == "CSV_NOS_001"
        assert isinstance(records[0].performance_criteria, list)

    def test_invalid_json_raises_value_error(self, tmp_path):
        bad_json = tmp_path / "malformed.json"
        bad_json.write_text("{malformed: json", encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        with pytest.raises(ValueError, match="Invalid JSON format"):
            pipeline.ingest_json(bad_json)

    def test_missing_required_fields_reported(self, tmp_path):
        incomplete_json = tmp_path / "incomplete.json"
        incomplete_json.write_text(json.dumps([
            {"id": "INCOMPLETE_001"}  # Missing title, description, trade, etc.
        ]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_json(incomplete_json)

        assert result.total_records == 1
        assert result.valid_records == 0
        assert result.invalid_records == 1
        assert len(result.validation_errors) == 1

    def test_duplicate_identifiers_detected(self, sample_valid_record, tmp_path):
        dup_file = tmp_path / "duplicates.json"
        dup_record = dict(sample_valid_record)
        dup_record["title"] = "Conflicting Duplicate Title"
        dup_file.write_text(json.dumps([sample_valid_record, dup_record]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_json(dup_file)

        assert result.total_records == 2
        assert result.valid_records == 1
        assert result.duplicate_records == 1
        assert result.conflicting_records == 1

    def test_provenance_preservation_synthetic_not_official(self, sample_json_file):
        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_json(sample_json_file)

        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        assert result.provenance_verified is False

    def test_unverified_official_claim_downgraded(self, sample_valid_record, tmp_path):
        claimed_official = dict(sample_valid_record)
        claimed_official["source_type"] = "OFFICIAL"
        # No official source_url or trusted domain provided
        unverified_file = tmp_path / "unverified_official.json"
        unverified_file.write_text(json.dumps([claimed_official]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_json(unverified_file)

        assert result.valid_records == 1
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        assert result.source_domain_allowlisted is False
        assert result.provenance_verified is False

    def test_fabricated_local_file_with_allowlisted_url_not_verified(self, sample_valid_record, tmp_path):
        """
        REGRESSION TEST:
        A caller-supplied URL, organization name, source_type: OFFICIAL, or allowlisted domain
        must NEVER independently establish that a local file is authentic.
        Calculating content hash does not establish authenticity.
        """
        fabricated = dict(sample_valid_record)
        fabricated["source_type"] = "OFFICIAL"
        fabricated["source_name"] = "National Council for Vocational Education and Training"
        fabricated["source_url"] = "https://ncvet.gov.in/standards/electrical"

        fabricated_file = tmp_path / "fabricated_official.json"
        fabricated_file.write_text(json.dumps([fabricated]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_json(fabricated_file)

        assert result.valid_records == 1
        # Domain is allowlisted...
        assert result.source_domain_allowlisted is True
        assert records[0].source_domain_allowlisted is True
        # ...but provenance is NOT verified because it lacks defensible verification evidence
        assert result.provenance_verified is False
        assert records[0].verification_evidence is None
        # Must be downgraded to USER_PROVIDED_UNVERIFIED
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        # Content hash was computed, but does not certify provenance
        assert result.output_dataset_hash is not None
        assert result.verification_details["status"] == "ALLOWLISTED_DOMAIN_UNVERIFIED_CONTENT"

    def test_arbitrary_attested_by_cannot_verify_fabricated_file(self, sample_valid_record, tmp_path):
        """
        ISSUE 1 REGRESSION TEST:
        An arbitrary caller cannot claim to be an authorized reviewer simply by supplying a name.
        Untrusted reviewer names must fail authorization and be downgraded to USER_PROVIDED_UNVERIFIED.
        """
        fabricated = dict(sample_valid_record)
        fabricated["source_type"] = "OFFICIAL"
        fabricated["source_url"] = "https://ncvet.gov.in/standards/electrical"

        fabricated_file = tmp_path / "arbitrary_reviewer.json"
        fabricated_file.write_text(json.dumps([fabricated]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        source_metadata = {
            "source_url": "https://ncvet.gov.in/standards/electrical",
            "attested_by": "untrusted_attacker_or_arbitrary_user",
        }
        records, result = pipeline.ingest_json(fabricated_file, source_metadata=source_metadata)

        assert result.valid_records == 1
        assert result.source_domain_allowlisted is True
        assert result.provenance_verified is False
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        assert records[0].verification_evidence is None
        assert result.verification_details["status"] == "UNAUTHORIZED_REVIEWER"
        assert "not recognized in the authorized reviewer registry" in result.verification_details["reason"]

    def test_authorized_reviewer_name_without_signature_rejected(self, sample_valid_record, tmp_path):
        """
        ISSUE 1 TEST:
        Even when an authorized reviewer name is supplied, lack of a cryptographic
        attestation signature (--attestation-token) fails verification.
        """
        fabricated = dict(sample_valid_record)
        fabricated["source_type"] = "OFFICIAL"
        fabricated["source_url"] = "https://ncvet.gov.in/standards/electrical"

        fabricated_file = tmp_path / "missing_sig.json"
        fabricated_file.write_text(json.dumps([fabricated]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        source_metadata = {
            "source_url": "https://ncvet.gov.in/standards/electrical",
            "attested_by": "lead_quality_assessor_01",  # Recognized in authorized registry
            # But NO attestation_signature provided!
        }
        records, result = pipeline.ingest_json(fabricated_file, source_metadata=source_metadata)

        assert result.provenance_verified is False
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        assert result.verification_details["status"] == "MISSING_ATTESTATION_SIGNATURE"
        assert "lacks required cryptographic authorization signature" in result.verification_details["reason"]

    def test_authorized_reviewer_with_invalid_signature_rejected(self, sample_valid_record, tmp_path):
        """
        ISSUE 1 TEST:
        Tampered or invalid attestation signature fails verification.
        """
        fabricated = dict(sample_valid_record)
        fabricated["source_type"] = "OFFICIAL"
        fabricated["source_url"] = "https://ncvet.gov.in/standards/electrical"

        fabricated_file = tmp_path / "invalid_sig.json"
        fabricated_file.write_text(json.dumps([fabricated]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        source_metadata = {
            "source_url": "https://ncvet.gov.in/standards/electrical",
            "attested_by": "lead_quality_assessor_01",
            "attestation_signature": "tampered_or_invalid_signature_hex",
        }
        records, result = pipeline.ingest_json(fabricated_file, source_metadata=source_metadata)

        assert result.provenance_verified is False
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        assert result.verification_details["status"] == "INVALID_ATTESTATION_SIGNATURE"
        assert "signature for 'lead_quality_assessor_01' is invalid" in result.verification_details["reason"]

    def test_verified_official_with_valid_cryptographic_attestation(self, sample_valid_record, tmp_path):
        """
        ISSUE 1 TEST:
        Defensible verification succeeds when an authorized reviewer provides
        a valid cryptographic HMAC-SHA256 attestation signature over the file hash and official URL.
        """
        attested_record = dict(sample_valid_record)
        attested_record["source_type"] = "OFFICIAL"
        attested_record["source_name"] = "National Council for Vocational Education and Training"
        attested_record["source_url"] = "https://ncvet.gov.in/standards/electrical"

        attested_file = tmp_path / "valid_attested.json"
        raw_json = json.dumps([attested_record])
        attested_file.write_text(raw_json, encoding="utf-8")

        # Compute file hash
        file_hash = hashlib.sha256(attested_file.read_bytes()).hexdigest()
        source_url = "https://ncvet.gov.in/standards/electrical"
        reviewer_id = "lead_quality_assessor_01"

        # Generate genuine HMAC-SHA256 signature
        valid_signature = generate_attestation_signature(
            reviewer_id=reviewer_id,
            content_hash=file_hash,
            source_url=source_url
        )

        pipeline = NOSIngestionPipeline()
        source_metadata = {
            "source_name": "National Council for Vocational Education and Training",
            "source_url": source_url,
            "attested_by": reviewer_id,
            "attestation_signature": valid_signature,
            "attestation": {
                "attested_by": reviewer_id,
                "review_decision": "Verified against Gazette notification No. 42"
            }
        }
        records, result = pipeline.ingest_json(attested_file, source_metadata=source_metadata)

        assert result.valid_records == 1
        assert result.source_domain_allowlisted is True
        assert result.provenance_verified is True
        assert records[0].source_type == "OFFICIAL"
        assert records[0].verification_evidence is not None
        assert records[0].verification_evidence["verification_method"] == "reviewer_attestation"
        assert records[0].verification_evidence["attested_by"] == "lead_quality_assessor_01"
        assert records[0].verification_evidence["signature_verified"] is True
        assert records[0].verification_evidence["file_content_hash"] == file_hash

    def test_local_file_claiming_https_direct_rejected(self, sample_valid_record, tmp_path):
        """
        ISSUE 2 TEST:
        A caller cannot claim a local file is verified by simply passing caller-supplied
        retrieval metadata (retrieval_method: https_direct). Local claims are rejected.
        """
        record_data = dict(sample_valid_record)
        record_data["source_type"] = "OFFICIAL"
        record_data["source_name"] = "NCVET"
        record_data["source_url"] = "https://ncvet.gov.in/standards/electrical"

        local_file = tmp_path / "fake_direct.json"
        local_file.write_text(json.dumps([record_data]), encoding="utf-8")

        pipeline = NOSIngestionPipeline()
        source_metadata = {
            "source_url": "https://ncvet.gov.in/standards/electrical",
            "retrieval_method": "https_direct",
            "downloaded_content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "retrieved_at": "2026-10-14T08:00:00+00:00"
        }
        records, result = pipeline.ingest_json(local_file, source_metadata=source_metadata)

        assert result.valid_records == 1
        assert result.source_domain_allowlisted is True
        assert result.provenance_verified is False
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"
        assert result.verification_details["status"] == "REJECTED_LOCAL_RETRIEVAL_CLAIM"
        assert "Caller-supplied 'https_direct' retrieval claims" in result.verification_details["reason"]

    def test_genuine_https_direct_retrieval_with_mocked_transport(self, sample_valid_record):
        """
        ISSUE 2 & 3 TEST:
        Genuine HTTPS direct retrieval retrieves content from an approved HTTPS source,
        records the final URL and retrieval timestamp, and hashes downloaded bytes.
        """
        official_url = "https://ncvet.gov.in/api/v1/standards/electrical_pack.json"
        payload_data = [sample_valid_record]
        payload_bytes = json.dumps(payload_data).encode("utf-8")
        expected_hash = hashlib.sha256(payload_bytes).hexdigest()

        # Controlled mock transport simulating an official HTTPS endpoint
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url == httpx.URL(official_url):
                return httpx.Response(
                    200,
                    content=payload_bytes,
                    headers={"Content-Type": "application/json"}
                )
            return httpx.Response(404, text="Not Found")

        mock_client = httpx.Client(transport=httpx.MockTransport(handler))

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_url(
            official_url,
            source_metadata={"source_name": "National Council for Vocational Education and Training"},
            http_client=mock_client
        )

        assert result.valid_records == 1
        assert result.source_domain_allowlisted is True
        assert result.provenance_verified is True
        assert records[0].source_type == "OFFICIAL"
        assert result.verification_details["verification_method"] == "https_direct"
        assert result.verification_details["source_url"] == official_url
        assert result.verification_details["downloaded_content_hash"] == expected_hash
        assert result.verification_details["http_status"] == 200
        assert result.verification_details["bytes_downloaded"] == len(payload_bytes)
        assert records[0].verification_evidence["downloaded_content_hash"] == expected_hash

    def test_https_direct_unapproved_domain_rejected(self, sample_valid_record):
        """
        ISSUE 2 & 3 TEST:
        Direct retrieval from a non-allowlisted domain cannot achieve official verified status.
        """
        unapproved_url = "https://untrusted-third-party.example.org/standards.json"
        payload_bytes = json.dumps([sample_valid_record]).encode("utf-8")

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=payload_bytes, headers={"Content-Type": "application/json"})

        mock_client = httpx.Client(transport=httpx.MockTransport(handler))

        pipeline = NOSIngestionPipeline()
        records, result = pipeline.ingest_url(unapproved_url, http_client=mock_client)

        assert result.valid_records == 1
        assert result.source_domain_allowlisted is False
        assert result.provenance_verified is False
        assert records[0].source_type == "USER_PROVIDED_UNVERIFIED"

    def test_https_direct_insecure_http_rejected(self):
        """
        ISSUE 2 & 3 TEST:
        Direct retrieval over plain HTTP is rejected for security.
        """
        insecure_url = "http://ncvet.gov.in/standards.json"
        pipeline = NOSIngestionPipeline()
        with pytest.raises(ValueError, match="Direct HTTPS retrieval requires an 'https://' endpoint"):
            pipeline.ingest_url(insecure_url)

    def test_change_report_generation(self, sample_valid_record, tmp_path):
        pipeline = NOSIngestionPipeline()
        old_record = NOSRecord(**sample_valid_record)

        modified_data = dict(sample_valid_record)
        modified_data["title"] = "Updated Motor Maintenance Title"
        new_record = NOSRecord(**modified_data)

        added_data = dict(sample_valid_record)
        added_data["nos_id"] = "TEST_NOS_002"
        added_data["code"] = "TEST_NOS_002"
        added_record = NOSRecord(**added_data)

        report = pipeline.generate_change_report(
            old_records=[old_record],
            new_records=[new_record, added_record]
        )

        assert "TEST_NOS_001" in report.modified_records
        assert "TEST_NOS_002" in report.added_records
        assert report.change_summary["added"] == 1
        assert report.change_summary["modified"] == 1
        assert report.change_summary["removed"] == 0

    def test_dry_run_preserves_output_file(self, sample_json_file, tmp_path):
        output_file = tmp_path / "target_output.json"
        output_file.write_text("PREEXISTING_CONTENT", encoding="utf-8")

        config = IngestionConfig(dry_run=True)
        pipeline = NOSIngestionPipeline(config)
        records, result = pipeline.ingest_json(sample_json_file)

        # Output file must remain untouched in dry-run mode
        assert output_file.read_text(encoding="utf-8") == "PREEXISTING_CONTENT"


class TestNOSRepositoryIntegration:
    def setup_method(self):
        invalidate_nos_cache()

    def teardown_method(self):
        invalidate_nos_cache()

    def test_demo_data_remains_available(self):
        repo = get_nos_repository()
        records = repo.get_all_nos()
        assert len(records) > 0
        assert all(r.get("source_type") == "DEMO" for r in records)
        assert any(r.get("nos_id") == "DEMO_NOS_001" for r in records)

    def test_load_normalized_dataset(self, sample_valid_record, tmp_path):
        normalized_file = tmp_path / "normalized.json"
        pipeline = NOSIngestionPipeline()
        records, _ = pipeline.ingest_json(
            tmp_path / "src.json",
            source_metadata={"source_type": "USER_PROVIDED_UNVERIFIED"}
        ) if False else ([NOSRecord(**sample_valid_record)], None)
        pipeline.save_normalized_dataset(records, normalized_file)

        repo = get_nos_repository()
        loaded = repo.load_nos_data(normalized_file, refresh=True)
        assert len(loaded) == 1
        assert loaded[0]["nos_id"] == "TEST_NOS_001"
        assert loaded[0]["id"] == "TEST_NOS_001"
        assert loaded[0]["source_type"] == "USER_PROVIDED_UNVERIFIED"

    def test_cache_invalidation_when_dataset_changes(self, sample_valid_record, tmp_path):
        repo = get_nos_repository()
        # 1. Load initial demo dataset
        initial_nos = repo.get_all_nos()
        assert any(n["nos_id"] == "DEMO_NOS_001" for n in initial_nos)

        # Run search on demo dataset
        demo_search = search_nos("wiring", top_k=2)
        assert len(demo_search) > 0

        # 2. Switch repository to custom dataset
        custom_file = tmp_path / "custom_nos.json"
        pipeline = NOSIngestionPipeline()
        custom_records = [NOSRecord(**sample_valid_record)]
        pipeline.save_normalized_dataset(custom_records, custom_file)

        # Load new dataset
        repo.load_nos_data(custom_file, refresh=True)

        # 3. Verify search now operates on new dataset without stale cache
        custom_search = search_nos("motor maintenance", top_k=2)
        assert len(custom_search) > 0
        assert custom_search[0]["nos_id"] == "TEST_NOS_001"

        # 4. Verify skill mapping operates on new dataset
        skill_input = [{
            "skill_name": "induction motor overhaul",
            "normalized_name": "motor maintenance",
            "evidence_text": "overhauled three phase motor",
            "confidence": 0.95
        }]
        mapping_result = map_skills_to_nos(skill_input, top_k=1)
        assert len(mapping_result) == 1
        assert mapping_result[0]["candidates"][0]["nos_id"] == "TEST_NOS_001"
        assert mapping_result[0]["candidates"][0]["source_type"] == "USER_PROVIDED_UNVERIFIED"

    def test_api_contract_preserved(self):
        # Verify get_nos_by_id returns dictionary with both id and nos_id
        nos = get_nos_by_id("DEMO_NOS_001")
        assert nos is not None
        assert "id" in nos
        assert "nos_id" in nos
        assert nos["id"] == "DEMO_NOS_001"
        assert nos["nos_id"] == "DEMO_NOS_001"
