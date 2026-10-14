"""
KaushalTwin ML Service — NOS/QP Data Ingestion Pipeline
Handles ingestion, validation, and normalization of NOS/QP data from various sources.
"""

from __future__ import annotations

import json
import csv
import hashlib
import hmac
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, asdict, field
from urllib.parse import urlparse

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from ml.schemas.skills import NOSMappingResponse, SkillNOSMapping, NOSCandidate, ExtractedSkill
from ml.services.exceptions import NOSMappingError

logger = logging.getLogger(__name__)

# Trusted authorized reviewer registry (administrative trust boundary)
DEFAULT_AUTHORIZED_REVIEWERS: Set[str] = {
    "lead_quality_assessor_01",
    "ncvet_admin_01",
    "director_audit_01",
    "nsdc_curriculum_reviewer_01",
}


def generate_attestation_signature(
    reviewer_id: str,
    content_hash: str,
    source_url: str,
    secret_key: Optional[str] = None
) -> str:
    """
    Generate an HMAC-SHA256 signature for reviewer attestation.
    Cryptographically binds the authorized reviewer identity to the specific dataset hash and source URL.
    """
    secret = secret_key
    if not secret:
        try:
            from app.core.config import settings
            secret = getattr(settings, 'JWT_SECRET_KEY', None)
        except Exception:
            secret = None
    if not secret:
        secret = "kaushaltwin-nos-attestation-default-secret-key-32b"

    message = f"kaushaltwin:nos-attestation:{reviewer_id}:{content_hash}:{source_url}".encode('utf-8')
    return hmac.new(secret.encode('utf-8'), message, hashlib.sha256).hexdigest()


def verify_attestation_signature(
    reviewer_id: str,
    content_hash: str,
    source_url: str,
    provided_signature: str,
    secret_key: Optional[str] = None
) -> bool:
    """Verify that an attestation signature matches the cryptographic HMAC-SHA256 digest."""
    if not provided_signature or not str(provided_signature).strip():
        return False
    expected = generate_attestation_signature(reviewer_id, content_hash, source_url, secret_key)
    return hmac.compare_digest(expected, str(provided_signature).strip())



# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class NOSRecord(BaseModel):
    """Normalized NOS record schema."""
    nos_id: str = Field(..., description="Unique NOS identifier")
    code: str = Field(..., description="Official NOS code")
    id: Optional[str] = Field(None, description="Backward compatibility identifier")
    title: str = Field(..., description="NOS title/name")

    @model_validator(mode="before")
    @classmethod
    def populate_ids(cls, values: Any) -> Any:
        if isinstance(values, dict):
            nos_id = values.get("nos_id") or values.get("id") or values.get("code")
            if nos_id:
                values.setdefault("nos_id", nos_id)
                values.setdefault("id", nos_id)
                values.setdefault("code", nos_id)
        return values
    description: str = Field(..., description="Detailed NOS description")
    mandatory: bool = Field(default=False, description="Whether NOS is mandatory")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="NOS weight/priority")
    trade: str = Field(..., description="Occupational/trade category")
    source_type: str = Field(..., description="Source type: OFFICIAL, DEMO, or USER_PROVIDED_UNVERIFIED")
    performance_criteria: List[str] = Field(default_factory=list, description="List of performance criteria")
    keywords: List[str] = Field(default_factory=list, description="List of keywords")
    competency_criteria: Optional[List[str]] = Field(None, description="Competency criteria if different from performance")
    evidence_requirements: Optional[List[str]] = Field(None, description="Evidence requirements")

    # Provenance fields
    source_name: Optional[str] = Field(None, description="Source organization or dataset name")
    source_url: Optional[str] = Field(None, description="Official source URL")
    source_version: Optional[str] = Field(None, description="Dataset version or release identifier")
    source_published_at: Optional[datetime] = Field(None, description="Publication or revision date")
    retrieved_at: Optional[datetime] = Field(None, description="When the data was retrieved")
    imported_at: Optional[datetime] = Field(None, description="When the record was imported")
    content_hash: Optional[str] = Field(None, description="Hash of original content for change detection")
    source_domain_allowlisted: bool = Field(default=False, description="Whether the claimed source URL domain is on the approved official registry")
    verification_evidence: Optional[Dict[str, Any]] = Field(None, description="Defensible verification evidence if authenticity was confirmed")

    @field_validator('nos_id', 'code')
    @classmethod
    def validate_ids_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('ID fields cannot be empty')
        return v.strip()

    @field_validator('title', 'description', 'trade')
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Text fields cannot be empty')
        return v.strip()


class IngestionResult(BaseModel):
    """Result of the ingestion process."""
    total_records: int = Field(..., description="Total records processed")
    valid_records: int = Field(..., description="Number of valid records")
    invalid_records: int = Field(..., description="Number of invalid records")
    duplicate_records: int = Field(..., description="Number of duplicate records detected")
    conflicting_records: int = Field(..., description="Number of conflicting records")
    missing_required_fields: List[str] = Field(default_factory=list, description="List of missing field errors")
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed validation errors")
    source_domain_allowlisted: bool = Field(default=False, description="Whether claimed source domain is on approved allowlist")
    provenance_verified: bool = Field(default=False, description="Whether provenance and integrity were defensibly verified")
    verification_details: Optional[Dict[str, Any]] = Field(None, description="Details of defensible verification evidence")
    output_dataset_hash: Optional[str] = Field(None, description="Hash of the generated dataset for change detection")
    processing_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChangeReport(BaseModel):
    """Report showing changes between dataset versions."""
    added_records: List[str] = Field(default_factory=list, description="NOS IDs of added records")
    modified_records: List[str] = Field(default_factory=list, description="NOS IDs of modified records")
    removed_records: List[str] = Field(default_factory=list, description="NOS IDs of removed records")
    unchanged_records: List[str] = Field(default_factory=list, description="NOS IDs of unchanged records")
    dataset_version: str = Field(..., description="Version identifier of the new dataset")
    change_summary: Dict[str, int] = Field(default_factory=dict, description="Summary of changes")


# ---------------------------------------------------------------------------
# Ingestion Pipeline
# ---------------------------------------------------------------------------

@dataclass
class IngestionConfig:
    """Configuration for the ingestion pipeline."""
    preserve_original_fields: bool = True
    normalize_whitespace: bool = True
    validate_references: bool = True
    detect_duplicates: bool = True
    generate_content_hash: bool = True
    fail_on_validation_errors: bool = False
    dry_run: bool = False
    authorized_reviewers: Set[str] = field(default_factory=lambda: set(DEFAULT_AUTHORIZED_REVIEWERS))
    attestation_secret_key: Optional[str] = None
    timeout: float = 30.0
    http_client: Optional[Any] = None



class NOSIngestionPipeline:
    """Main ingestion pipeline for NOS/QP data."""

    def __init__(self, config: Optional[IngestionConfig] = None):
        self.config = config or IngestionConfig()
        self.logger = logging.getLogger(__name__)

    def ingest_json(self, file_path: Union[str, Path],
                   source_metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[NOSRecord], IngestionResult]:
        """
        Ingest NOS data from JSON file.

        Args:
            file_path: Path to JSON file containing NOS data
            source_metadata: Metadata about the source (organization, URL, version, etc.)

        Returns:
            Tuple of (normalized records, ingestion result)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        self.logger.info(f"Starting JSON ingestion from {file_path}")

        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        file_content_hash = hashlib.sha256(raw_bytes).hexdigest()

        try:
            raw_data = json.loads(raw_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        # Handle both array and object formats
        if isinstance(raw_data, dict) and 'nos_records' in raw_data:
            raw_records = raw_data['nos_records']
        elif isinstance(raw_data, list):
            raw_records = raw_data
        else:
            raw_records = [raw_data]  # Single record

        return self._process_records(
            raw_records,
            file_path,
            source_metadata,
            'json',
            file_content_hash=file_content_hash,
            internal_retrieval_evidence=None,
            is_https_direct_source=False
        )

    def ingest_csv(self, file_path: Union[str, Path],
                  source_metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[NOSRecord], IngestionResult]:
        """
        Ingest NOS data from CSV file.

        Args:
            file_path: Path to CSV file containing NOS data
            source_metadata: Metadata about the source (organization, URL, version, etc.)

        Returns:
            Tuple of (normalized records, ingestion result)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        self.logger.info(f"Starting CSV ingestion from {file_path}")

        with open(file_path, 'rb') as f:
            raw_bytes = f.read()

        file_content_hash = hashlib.sha256(raw_bytes).hexdigest()

        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding='utf-8')
            raw_records = df.to_dict('records')
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {e}")

        return self._process_records(
            raw_records,
            file_path,
            source_metadata,
            'csv',
            file_content_hash=file_content_hash,
            internal_retrieval_evidence=None,
            is_https_direct_source=False
        )

    def ingest_url(self, url: str,
                   source_metadata: Optional[Dict[str, Any]] = None,
                   http_client: Optional[Any] = None) -> Tuple[List[NOSRecord], IngestionResult]:
        """
        Directly retrieve and ingest NOS data from an approved official HTTPS endpoint.
        Performs genuine HTTPS retrieval, records final redirected URL, timestamp, and hashes downloaded bytes.

        Args:
            url: HTTPS URL pointing to official NOS dataset
            source_metadata: Optional metadata supplied by caller
            http_client: Optional HTTP client / transport for testing

        Returns:
            Tuple of (normalized records, ingestion result)
        """
        import httpx

        parsed = urlparse(url)
        if parsed.scheme.lower() != 'https':
            raise ValueError(f"Direct HTTPS retrieval requires an 'https://' endpoint, got: '{url}'")

        domain_allowlisted = self._is_source_domain_allowlisted(url)
        retrieved_at = datetime.now(timezone.utc)

        self.logger.info(f"Starting direct HTTPS ingestion from {url} (domain_allowlisted={domain_allowlisted})")

        # Perform actual HTTP retrieval
        client = http_client or self.config.http_client
        if client is None:
            with httpx.Client(follow_redirects=True, timeout=self.config.timeout) as auto_client:
                response = auto_client.get(url)
        else:
            response = client.get(url)

        if response.status_code != 200:
            raise ValueError(f"HTTPS retrieval failed with HTTP status {response.status_code}: {response.text}")

        final_url = str(response.url)
        final_domain_allowlisted = self._is_source_domain_allowlisted(final_url)
        raw_bytes = response.content
        downloaded_content_hash = hashlib.sha256(raw_bytes).hexdigest()

        # Parse content
        content_type = response.headers.get("content-type", "").lower()
        if "csv" in content_type or url.lower().endswith(".csv") or final_url.lower().endswith(".csv"):
            format_type = "csv"
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding='utf-8')
                raw_records = df.to_dict('records')
            except Exception as e:
                raise ValueError(f"Error reading downloaded CSV content: {e}")
        else:
            format_type = "json"
            try:
                raw_data = json.loads(raw_bytes.decode('utf-8'))
                if isinstance(raw_data, dict) and 'nos_records' in raw_data:
                    raw_records = raw_data['nos_records']
                elif isinstance(raw_data, list):
                    raw_records = raw_data
                else:
                    raw_records = [raw_data]
            except Exception as e:
                raise ValueError(f"Error reading downloaded JSON content: {e}")

        # Construct genuine retrieval evidence only if both origin and final redirected domain are allowlisted
        if domain_allowlisted and final_domain_allowlisted:
            internal_retrieval_evidence = {
                "verification_method": "https_direct",
                "source_domain_allowlisted": True,
                "source_name": (source_metadata.get('source_name') if source_metadata else None) or parsed.netloc,
                "source_url": final_url,
                "downloaded_content_hash": downloaded_content_hash,
                "retrieved_at": retrieved_at.isoformat(),
                "http_status": response.status_code,
                "bytes_downloaded": len(raw_bytes),
            }
        else:
            internal_retrieval_evidence = None

        return self._process_records(
            raw_records,
            Path(final_url),
            source_metadata,
            format_type,
            file_content_hash=downloaded_content_hash,
            internal_retrieval_evidence=internal_retrieval_evidence,
            is_https_direct_source=True,
            final_url=final_url
        )

    def _process_records(self, raw_records: List[Dict[str, Any]],
                        source_path: Path,
                        source_metadata: Optional[Dict[str, Any]],
                        format_type: str,
                        file_content_hash: Optional[str] = None,
                        internal_retrieval_evidence: Optional[Dict[str, Any]] = None,
                        is_https_direct_source: bool = False,
                        final_url: Optional[str] = None) -> Tuple[List[NOSRecord], IngestionResult]:
        """Process raw records through the ingestion pipeline."""

        result = IngestionResult(
            total_records=len(raw_records),
            valid_records=0,
            invalid_records=0,
            duplicate_records=0,
            conflicting_records=0
        )

        normalized_records = []
        seen_ids = set()
        id_conflicts = {}  # Track conflicts by ID
        verification_reasons: List[str] = []

        for idx, raw_record in enumerate(raw_records):
            try:
                # Normalize the record
                normalized = self._normalize_record(
                    raw_record, source_path, source_metadata, format_type, idx,
                    file_content_hash=file_content_hash,
                    internal_retrieval_evidence=internal_retrieval_evidence,
                    is_https_direct_source=is_https_direct_source,
                    final_url=final_url,
                    verification_reasons=verification_reasons
                )

                # Validate the normalized record
                validation_errors = self._validate_record(normalized)

                if validation_errors:
                    result.invalid_records += 1
                    result.validation_errors.extend([
                        {
                            'record_index': idx,
                            'record_id': raw_record.get('id', raw_record.get('code', f'unknown_{idx}')),
                            'errors': validation_errors
                        }
                    ])
                    if self.config.fail_on_validation_errors:
                        raise ValueError(f"Validation failed for record {idx}: {validation_errors}")
                else:
                    # Check for duplicates
                    if normalized.nos_id in seen_ids:
                        result.duplicate_records += 1
                        id_conflicts.setdefault(normalized.nos_id, []).append(idx)
                    else:
                        seen_ids.add(normalized.nos_id)
                        normalized_records.append(normalized)
                        result.valid_records += 1

            except Exception as e:
                result.invalid_records += 1
                result.validation_errors.append({
                    'record_index': idx,
                    'record_id': raw_record.get('id', raw_record.get('code', f'unknown_{idx}')),
                    'errors': [str(e)]
                })
                if self.config.fail_on_validation_errors:
                    raise

        # Process conflicts
        if id_conflicts and self.config.detect_duplicates:
            result.conflicting_records = len(id_conflicts)
            for nos_id, indices in id_conflicts.items():
                self.logger.warning(f"Duplicate NOS ID {nos_id} found at indices: {indices}")

        # Separate source_domain_allowlisted from provenance_verified
        if normalized_records:
            result.source_domain_allowlisted = any(r.source_domain_allowlisted for r in normalized_records)
            result.provenance_verified = any(
                r.source_type == 'OFFICIAL' and r.verification_evidence is not None
                for r in normalized_records
            )
        else:
            result.source_domain_allowlisted = False
            result.provenance_verified = False

        if result.provenance_verified:
            verified_ev = next((r.verification_evidence for r in normalized_records if r.verification_evidence), None)
            result.verification_details = verified_ev
        else:
            latest_reason = verification_reasons[0] if verification_reasons else None
            if latest_reason:
                status = "UNVERIFIED"
                if "not recognized in the authorized reviewer registry" in latest_reason:
                    status = "UNAUTHORIZED_REVIEWER"
                elif "lacks required cryptographic authorization signature" in latest_reason:
                    status = "MISSING_ATTESTATION_SIGNATURE"
                elif "Cryptographic attestation signature" in latest_reason:
                    status = "INVALID_ATTESTATION_SIGNATURE"
                elif "Caller-supplied 'https_direct'" in latest_reason:
                    status = "REJECTED_LOCAL_RETRIEVAL_CLAIM"
                elif result.source_domain_allowlisted:
                    status = "ALLOWLISTED_DOMAIN_UNVERIFIED_CONTENT"

                result.verification_details = {
                    "source_domain_allowlisted": result.source_domain_allowlisted,
                    "provenance_verified": False,
                    "status": status,
                    "reason": latest_reason
                }
            elif result.source_domain_allowlisted:
                result.verification_details = {
                    "source_domain_allowlisted": True,
                    "provenance_verified": False,
                    "status": "ALLOWLISTED_DOMAIN_UNVERIFIED_CONTENT",
                    "notice": "Claimed source domain is on approved allowlist, but local file lacks defensible verification evidence."
                }
            else:
                result.verification_details = {
                    "source_domain_allowlisted": False,
                    "provenance_verified": False,
                    "status": "UNVERIFIED"
                }

        # Generate dataset hash (identifies content for change detection; does NOT establish authenticity)
        if self.config.generate_content_hash and normalized_records:
            result.output_dataset_hash = self._generate_dataset_hash(normalized_records)

        result.processing_timestamp = datetime.now(timezone.utc)

        self.logger.info(
            f"Ingestion complete: {result.valid_records} valid, "
            f"{result.invalid_records} invalid, {result.duplicate_records} duplicates, "
            f"{result.conflicting_records} conflicts, "
            f"domain_allowlisted={result.source_domain_allowlisted}, "
            f"provenance_verified={result.provenance_verified}"
        )

        return normalized_records, result

    def _is_source_domain_allowlisted(self, source_url: Optional[str]) -> bool:
        """Check whether a claimed source URL uses an approved official domain."""
        if not source_url:
            return False

        try:
            parsed = urlparse(str(source_url))
            domain = (parsed.netloc or '').lower()

            trusted_domains = (
                "ncvet.gov.in",
                "nsdcindia.org",
                "skillindia.gov.in",
                "dgt.gov.in",
                "msde.gov.in",
            )
            return any(
                domain == td or domain.endswith("." + td) or domain.endswith(".gov.in")
                for td in trusted_domains
            )
        except Exception:
            return False

    def _verify_provenance_evidence(
        self,
        source_metadata: Optional[Dict[str, Any]],
        raw_record: Dict[str, Any],
        file_content_hash: Optional[str] = None,
        internal_retrieval_evidence: Optional[Dict[str, Any]] = None,
        is_https_direct_source: bool = False,
        final_url: Optional[str] = None
    ) -> Tuple[bool, bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Evaluate provenance claims and separate domain allowlisting from actual provenance verification.

        A caller-supplied URL, organization name, source_type: OFFICIAL, or allowlisted domain
        must NEVER independently establish that a local file is authentic.
        Validation of a file schema or calculating content hash does NOT prove its source is authentic.

        Returns:
            (domain_allowlisted: bool, provenance_verified: bool, evidence: Optional[dict], reason: Optional[str])
        """
        meta = source_metadata or {}
        source_url = final_url or meta.get('source_url') or raw_record.get('source_url')
        source_name = meta.get('source_name') or raw_record.get('source_name')

        domain_allowlisted = self._is_source_domain_allowlisted(source_url)

        # -------------------------------------------------------------
        # Case 1: Direct HTTPS Retrieval via pipeline.ingest_url()
        # -------------------------------------------------------------
        if is_https_direct_source:
            if internal_retrieval_evidence:
                return True, True, internal_retrieval_evidence, None
            else:
                return domain_allowlisted, False, None, f"Direct retrieval endpoint '{source_url}' is not on an approved official domain allowlist."

        # -------------------------------------------------------------
        # Case 2: Local file claiming 'https_direct' retrieval (Issue 2)
        # -------------------------------------------------------------
        retrieval_method = meta.get('retrieval_method') or meta.get('verification_method')
        attestation = meta.get('attestation') or raw_record.get('attestation')
        if isinstance(attestation, dict) and not retrieval_method:
            retrieval_method = attestation.get('verification_method')

        if retrieval_method == 'https_direct' or meta.get('downloaded_content_hash') or raw_record.get('downloaded_content_hash'):
            reason = (
                "Caller-supplied 'https_direct' retrieval claims or downloaded content hashes for a local file "
                "are rejected. Direct HTTPS retrieval verification is only granted when the pipeline performs "
                "the retrieval directly from an approved HTTPS source via ingest_url()."
            )
            return domain_allowlisted, False, None, reason

        # -------------------------------------------------------------
        # Case 3: Reviewer Attestation with Trust Boundary (Issue 1)
        # -------------------------------------------------------------
        attested_by = meta.get('attested_by') or (attestation.get('attested_by') if isinstance(attestation, dict) else None)
        if attested_by and str(attested_by).strip():
            attested_by_clean = str(attested_by).strip()

            # Trust boundary check 1: Authorized reviewer registry
            if attested_by_clean not in self.config.authorized_reviewers:
                reason = f"Reviewer '{attested_by_clean}' is not recognized in the authorized reviewer registry."
                return domain_allowlisted, False, None, reason

            # Trust boundary check 2: Cryptographic signature / token
            signature = (
                meta.get('attestation_signature')
                or meta.get('attestation_token')
                or (attestation.get('signature') if isinstance(attestation, dict) else None)
                or (attestation.get('attestation_token') if isinstance(attestation, dict) else None)
            )
            if not signature or not str(signature).strip():
                reason = (
                    f"Reviewer attestation for '{attested_by_clean}' lacks required cryptographic authorization signature "
                    f"(--attestation-token / --attestation-signature)."
                )
                return domain_allowlisted, False, None, reason

            # Trust boundary check 3: Cryptographic signature verification over content hash
            hash_to_verify = file_content_hash or raw_record.get('content_hash')
            if not hash_to_verify:
                hash_to_verify = self._generate_record_hash(raw_record)

            is_valid_sig = verify_attestation_signature(
                reviewer_id=attested_by_clean,
                content_hash=hash_to_verify,
                source_url=str(source_url or ''),
                provided_signature=str(signature).strip(),
                secret_key=self.config.attestation_secret_key
            )
            if not is_valid_sig:
                reason = (
                    f"Cryptographic attestation signature for '{attested_by_clean}' is invalid or does not match "
                    f"the dataset content hash ({hash_to_verify}) and source URL ({source_url})."
                )
                return domain_allowlisted, False, None, reason

            # Trust boundary check 4: Approved official domain allowlist
            if not domain_allowlisted:
                return False, False, None, f"Attested source URL '{source_url}' is not on an approved official domain allowlist."

            # Defensible verification evidence established
            evidence = {
                "verification_method": "reviewer_attestation",
                "attested_by": attested_by_clean,
                "source_domain_allowlisted": True,
                "source_name": source_name,
                "source_url": source_url,
                "file_content_hash": hash_to_verify,
                "verified_at": meta.get('attested_at') or datetime.now(timezone.utc).isoformat(),
                "signature_verified": True,
                "review_decision": (attestation.get('review_decision') if isinstance(attestation, dict) else None) or "APPROVED"
            }
            return True, True, evidence, None

        # -------------------------------------------------------------
        # Case 4: Allowlisted domain but no defensible verification evidence
        # -------------------------------------------------------------
        if domain_allowlisted:
            reason = (
                "Claimed source URL is on an approved official domain, but the file lacks defensible verification evidence "
                "(e.g., direct ingest_url() retrieval or cryptographically signed reviewer attestation). "
                "Caller-supplied claims alone do not establish authenticity."
            )
            return True, False, None, reason

        # -------------------------------------------------------------
        # Case 5: Neither allowlisted nor verified
        # -------------------------------------------------------------
        return False, False, None, "Source URL domain is not on the approved official domain allowlist and lacks verification evidence."

    def _normalize_record(self, raw_record: Dict[str, Any],
                         source_path: Path,
                         source_metadata: Optional[Dict[str, Any]],
                         format_type: str,
                         record_index: int,
                         file_content_hash: Optional[str] = None,
                         internal_retrieval_evidence: Optional[Dict[str, Any]] = None,
                         is_https_direct_source: bool = False,
                         final_url: Optional[str] = None,
                         verification_reasons: Optional[List[str]] = None) -> NOSRecord:
        """Normalize a raw record to the NOSRecord schema."""

        # Start with raw data
        normalized_data = dict(raw_record)

        # Handle field mapping variations
        field_mappings = {
            # ID fields
            'nos_id': ['nos_id', 'id', 'code', 'NOS_ID'],
            'code': ['code', 'NOS_Code', 'nos_code'],
            # Text fields
            'title': ['title', 'Title', 'nos_title', 'name'],
            'description': ['description', 'Description', 'nos_description', 'details'],
            # Boolean fields
            'mandatory': ['mandatory', 'Mandatory', 'is_mandatory', 'required'],
            # Numeric fields
            'weight': ['weight', 'Weight', 'nos_weight', 'priority'],
            # Trade field
            'trade': ['trade', 'Trade', 'occupation', 'sector', 'job_role'],
            # List fields
            'performance_criteria': ['performance_criteria', 'Performance_Criteria', 'criteria', 'performance'],
            'keywords': ['keywords', 'Keywords', 'tags', 'key_words'],
        }

        # Apply field mappings
        for target_field, source_fields in field_mappings.items():
            if target_field not in normalized_data or not normalized_data[target_field]:
                for source_field in source_fields:
                    if source_field in raw_record and raw_record[source_field] is not None:
                        normalized_data[target_field] = raw_record[source_field]
                        break

        # Ensure ID consistency and backward compatibility
        nos_id = normalized_data.get('nos_id') or raw_record.get('id') or normalized_data.get('code')
        normalized_data['nos_id'] = nos_id
        normalized_data['id'] = raw_record.get('id') or nos_id
        normalized_data['code'] = normalized_data.get('code') or nos_id

        # Ensure list fields are actually lists
        list_fields = ['performance_criteria', 'keywords', 'competency_criteria', 'evidence_requirements']
        for field in list_fields:
            if field in normalized_data and isinstance(normalized_data[field], str):
                # Try to parse as JSON array first
                try:
                    parsed = json.loads(normalized_data[field])
                    if isinstance(parsed, list):
                        normalized_data[field] = parsed
                except (json.JSONDecodeError, TypeError):
                    # Treat as comma-separated string
                    normalized_data[field] = [item.strip() for item in normalized_data[field].split(',') if item.strip()]
            elif field not in normalized_data:
                normalized_data[field] = [] if field in ['performance_criteria', 'keywords'] else None

        # Determine provenance and domain allowlisting independently
        domain_allowlisted, is_verified, evidence, reason = self._verify_provenance_evidence(
            source_metadata,
            raw_record,
            file_content_hash=file_content_hash,
            internal_retrieval_evidence=internal_retrieval_evidence,
            is_https_direct_source=is_https_direct_source,
            final_url=final_url
        )
        if reason and verification_reasons is not None:
            verification_reasons.append(reason)

        normalized_data['source_domain_allowlisted'] = domain_allowlisted
        normalized_data['verification_evidence'] = evidence

        # Handle source_type normalization with defensible provenance verification
        if is_https_direct_source and is_verified:
            raw_source_type = 'OFFICIAL'
        else:
            raw_source_type = raw_record.get('source_type')
            if not raw_source_type and source_metadata and source_metadata.get('source_type'):
                raw_source_type = source_metadata['source_type']
            if not raw_source_type:
                raw_source_type = 'USER_PROVIDED_UNVERIFIED'
            raw_source_type = str(raw_source_type).upper()


        # If caller claims OFFICIAL, verify whether defensible verification evidence exists.
        # A caller-supplied URL, organization name, source_type: OFFICIAL, or allowlisted domain
        # must NEVER independently establish that a local file is authentic.
        if raw_source_type == 'OFFICIAL':
            if not is_verified:
                self.logger.warning(
                    f"Record '{nos_id}' claims 'OFFICIAL' source_type, but official provenance "
                    f"lacks defensible verification evidence: {reason}. "
                    f"Reclassifying as 'USER_PROVIDED_UNVERIFIED'."
                )
                raw_source_type = 'USER_PROVIDED_UNVERIFIED'

        normalized_data['source_type'] = raw_source_type

        # Normalize whitespace if configured
        if self.config.normalize_whitespace:
            text_fields = ['title', 'description', 'trade']
            for field in text_fields:
                if field in normalized_data and isinstance(normalized_data[field], str):
                    normalized_data[field] = ' '.join(normalized_data[field].split())

            # Normalize list fields
            for field in ['performance_criteria', 'keywords']:
                if field in normalized_data and isinstance(normalized_data[field], list):
                    normalized_data[field] = [
                        ' '.join(item.split()) if isinstance(item, str) else item
                        for item in normalized_data[field]
                    ]

        # Set provenance information (does not override source_type)
        provenance_data = self._extract_provenance(source_path, source_metadata, record_index, format_type, final_url=final_url)
        normalized_data.update(provenance_data)

        # Generate content hash if configured
        if self.config.generate_content_hash:
            normalized_data['content_hash'] = self._generate_record_hash(normalized_data)

        # Create and return NOSRecord
        try:
            return NOSRecord(**normalized_data)
        except ValidationError as e:
            # Re-raise with more context
            raise ValueError(f"Failed to create NOSRecord: {e}")

    def _extract_provenance(self, source_path: Union[Path, str],
                           source_metadata: Optional[Dict[str, Any]],
                           record_index: int,
                           format_type: str,
                           final_url: Optional[str] = None) -> Dict[str, Any]:
        """Extract provenance information for a record."""
        now = datetime.now(timezone.utc)

        provenance = {
            'imported_at': now,
            'retrieved_at': now,
        }

        if final_url:
            provenance['source_url'] = final_url

        # Add source metadata if provided
        if source_metadata:
            for key in ['source_name', 'source_url', 'source_version', 'source_published_at']:
                if key in source_metadata and source_metadata[key] is not None:
                    provenance[key] = source_metadata[key]

        # Convert datetime strings to datetime objects if needed
        for date_field in ['source_published_at', 'retrieved_at', 'imported_at']:
            if date_field in provenance and isinstance(provenance[date_field], str):
                try:
                    provenance[date_field] = datetime.fromisoformat(provenance[date_field].replace('Z', '+00:00'))
                except ValueError:
                    # Keep as string if parsing fails
                    pass

        return provenance


    def _validate_record(self, record: NOSRecord) -> List[str]:
        """Validate a normalized NOS record and return list of errors."""
        errors = []

        # Required fields validation (Pydantic handles most, but we can add custom logic)
        required_fields = ['nos_id', 'code', 'title', 'description', 'trade', 'source_type']
        for field in required_fields:
            value = getattr(record, field)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing or empty required field: {field}")

        # Custom validations
        if record.weight < 0.0 or record.weight > 1.0:
            errors.append(f"Weight must be between 0.0 and 1.0, got {record.weight}")

        # Source type validation
        valid_source_types = ['OFFICIAL', 'DEMO', 'USER_PROVIDED_UNVERIFIED']
        if record.source_type not in valid_source_types:
            errors.append(f"Invalid source_type: {record.source_type}. Must be one of {valid_source_types}")

        return errors

    def _generate_record_hash(self, record_data: Dict[str, Any]) -> str:
        """Generate a hash for a record based on its content."""
        # Create a copy without hash and provenance fields that change
        data_for_hash = {k: v for k, v in record_data.items()
                        if k not in ['content_hash', 'imported_at', 'retrieved_at']}

        # Sort keys for consistent hashing
        sorted_data = json.dumps(data_for_hash, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode('utf-8')).hexdigest()

    def _generate_dataset_hash(self, records: List[NOSRecord]) -> str:
        """Generate a hash for the entire dataset."""
        # Sort records by nos_id for consistent hashing
        sorted_records = sorted(records, key=lambda r: r.nos_id)

        # Create hashable representation
        dataset_representation = []
        for record in sorted_records:
            # Exclude fields that change with each import
            record_dict = record.model_dump()
            record_dict.pop('imported_at', None)
            record_dict.pop('content_hash', None)
            dataset_representation.append(record_dict)

        dataset_json = json.dumps(dataset_representation, sort_keys=True, default=str)
        return hashlib.sha256(dataset_json.encode('utf-8')).hexdigest()

    def save_normalized_dataset(self, records: List[NOSRecord],
                               output_path: Union[str, Path]) -> Path:
        """Save normalized records to a JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionaries for JSON serialization
        records_data = [record.model_dump() for record in records]

        # Convert datetime objects to ISO strings
        for record in records_data:
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.isoformat()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Saved {len(records)} normalized records to {output_path}")
        return output_path

    def load_existing_dataset(self, file_path: Union[str, Path]) -> List[NOSRecord]:
        """Load an existing normalized dataset for comparison."""
        file_path = Path(file_path)
        if not file_path.exists():
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            records = []
            for item in data:
                # Convert ISO strings back to datetime objects
                for key, value in item.items():
                    if key.endswith('_at') and isinstance(value, str):
                        try:
                            item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            pass  # Keep as string if parsing fails

                records.append(NOSRecord(**item))

            return records
        except Exception as e:
            self.logger.error(f"Error loading existing dataset: {e}")
            return []

    def generate_change_report(self, old_records: List[NOSRecord],
                              new_records: List[NOSRecord]) -> ChangeReport:
        """Generate a report showing changes between two dataset versions."""
        old_ids = {record.nos_id: record for record in old_records}
        new_ids = {record.nos_id: record for record in new_records}

        added = set(new_ids.keys()) - set(old_ids.keys())
        removed = set(old_ids.keys()) - set(new_ids.keys())
        common = set(old_ids.keys()) & set(new_ids.keys())

        modified = []
        unchanged = []

        for nos_id in common:
            old_record = old_ids[nos_id]
            new_record = new_ids[nos_id]

            # Compare core content (excluding provenance and metadata that changes)
            old_dict = old_record.model_dump()
            new_dict = new_record.model_dump()

            # Remove fields that are expected to change
            for field in ['imported_at', 'content_hash', 'retrieved_at']:
                old_dict.pop(field, None)
                new_dict.pop(field, None)

            if old_dict != new_dict:
                modified.append(nos_id)
            else:
                unchanged.append(nos_id)

        # Generate version identifier
        version = f"v{len(new_records)}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        return ChangeReport(
            added_records=sorted(list(added)),
            modified_records=sorted(list(modified)),
            removed_records=sorted(list(removed)),
            unchanged_records=sorted(list(unchanged)),
            dataset_version=version,
            change_summary={
                'added': len(added),
                'modified': len(modified),
                'removed': len(removed),
                'unchanged': len(unchanged),
                'total_old': len(old_records),
                'total_new': len(new_records)
            }
        )


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    """Main CLI entry point for the NOS ingestion pipeline."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='KaushalTwin NOS/QP Data Ingestion Pipeline')
    parser.add_argument('command', choices=['ingest', 'validate', 'report'],
                       help='Command to execute')
    parser.add_argument('--input', '-i', required=True,
                       help='Input file path (JSON or CSV)')
    parser.add_argument('--output', '-o',
                       help='Output file path for normalized data')
    parser.add_argument('--format', '-f', choices=['json', 'csv'],
                       help='Input file format (auto-detected if not specified)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run validation without saving output')
    parser.add_argument('--fail-on-errors', action='store_true',
                       help='Stop processing on first validation error')
    parser.add_argument('--preserve-fields', action='store_true', default=True,
                       help='Preserve unrecognized fields from source data')
    parser.add_argument('--no-normalize-whitespace', action='store_true',
                       help='Disable whitespace normalization')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--source-type', choices=['OFFICIAL', 'DEMO', 'USER_PROVIDED_UNVERIFIED'],
                       default=None, help='Explicit source classification (default: from data or USER_PROVIDED_UNVERIFIED)')
    parser.add_argument('--source-name', default=None,
                       help='Source organization or dataset name')
    parser.add_argument('--source-url', default=None,
                       help='Official source URL')
    parser.add_argument('--source-version', default=None,
                       help='Dataset release or version identifier')
    parser.add_argument('--attested-by', default=None,
                       help='Identity of reviewer attesting to the authenticity of a manually supplied official dataset')
    parser.add_argument('--attestation-token', '--attestation-signature', dest='attestation_token', default=None,
                       help='Cryptographic HMAC-SHA256 signature / token proving reviewer authorization')
    parser.add_argument('--verification-method', choices=['reviewer_attestation', 'https_direct'], default=None,
                       help='Defensible verification method used to substantiate authenticity')

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create configuration
    config = IngestionConfig(
        preserve_original_fields=args.preserve_fields,
        normalize_whitespace=not args.no_normalize_whitespace,
        fail_on_validation_errors=args.fail_on_errors,
        dry_run=args.dry_run
    )

    pipeline = NOSIngestionPipeline(config)

    # Build source metadata from explicit CLI arguments only (never invent official data)
    source_metadata: Dict[str, Any] = {}
    if args.source_type:
        source_metadata['source_type'] = args.source_type
    if args.source_name:
        source_metadata['source_name'] = args.source_name
    if args.source_url:
        source_metadata['source_url'] = args.source_url
    if args.source_version:
        source_metadata['source_version'] = args.source_version
    if args.attested_by:
        source_metadata['attested_by'] = args.attested_by
        source_metadata['verification_method'] = args.verification_method or 'reviewer_attestation'
    elif args.verification_method:
        source_metadata['verification_method'] = args.verification_method
    if args.attestation_token:
        source_metadata['attestation_signature'] = args.attestation_token

    try:
        if args.command == 'ingest':
            is_url = args.input.lower().startswith(('https://', 'http://'))
            if is_url:
                records, result = pipeline.ingest_url(args.input, source_metadata)
            else:
                # Determine format
                format_type = args.format
                if not format_type:
                    if args.input.lower().endswith('.json'):
                        format_type = 'json'
                    elif args.input.lower().endswith('.csv'):
                        format_type = 'csv'
                    else:
                        raise ValueError("Could not determine file format. Use --format to specify.")

                # Ingest data
                if format_type == 'json':
                    records, result = pipeline.ingest_json(args.input, source_metadata)
                else:
                    records, result = pipeline.ingest_csv(args.input, source_metadata)

            # Print validation report
            print("\n=== INGESTION VALIDATION REPORT ===")
            print(f"Total records processed: {result.total_records}")
            print(f"Valid records: {result.valid_records}")
            print(f"Invalid records: {result.invalid_records}")
            print(f"Duplicate records: {result.duplicate_records}")
            print(f"Conflicting records: {result.conflicting_records}")
            print(f"Missing required fields: {len(result.missing_required_fields)}")
            print(f"Source domain allowlisted: {result.source_domain_allowlisted}")
            print(f"Provenance verified: {result.provenance_verified}")
            if result.verification_details:
                print(f"Verification details: {result.verification_details}")

            if result.validation_errors:
                print(f"\nValidation errors ({len(result.validation_errors)}):")
                for error in result.validation_errors[:5]:  # Show first 5 errors
                    print(f"  Record {error['record_index']} ({error['record_id']}): {error['errors']}")
                if len(result.validation_errors) > 5:
                    print(f"  ... and {len(result.validation_errors) - 5} more errors")

            if result.output_dataset_hash:
                print(f"\nOutput dataset hash: {result.output_dataset_hash}")

            # Save output if requested and not dry run
            if args.output and not args.dry_run:
                output_path = pipeline.save_normalized_dataset(records, args.output)
                print(f"\nNormalized dataset saved to: {output_path}")
            elif args.dry_run:
                print("\nDRY RUN: No output file saved")

            return 0 if result.invalid_records == 0 else 1

        elif args.command == 'validate':
            is_url = args.input.lower().startswith(('https://', 'http://'))
            if is_url:
                records, result = pipeline.ingest_url(args.input, source_metadata)
            else:
                # Validation-only mode
                format_type = args.format
                if not format_type:
                    if args.input.lower().endswith('.json'):
                        format_type = 'json'
                    elif args.input.lower().endswith('.csv'):
                        format_type = 'csv'
                    else:
                        raise ValueError("Could not determine file format. Use --format to specify.")

                if format_type == 'json':
                    records, result = pipeline.ingest_json(args.input, source_metadata)
                else:
                    records, result = pipeline.ingest_csv(args.input, source_metadata)

            print("=== VALIDATION REPORT ===")
            print(f"Total records: {result.total_records}")
            print(f"Valid: {result.valid_records}")
            print(f"Invalid: {result.invalid_records}")
            print(f"Source domain allowlisted: {result.source_domain_allowlisted}")
            print(f"Provenance verified: {result.provenance_verified}")
            if result.verification_details:
                print(f"Verification details: {result.verification_details}")

            return 0 if result.invalid_records == 0 else 1

        elif args.command == 'report':
            # Generate change report between existing and new data
            if not args.output:
                raise ValueError("--output required for report command")

            # Load existing dataset if it exists
            existing_records = []
            if Path(args.output).exists():
                existing_records = pipeline.load_existing_dataset(args.output)
                print(f"Loaded {len(existing_records)} existing records from {args.output}")

            # Ingest new data
            format_type = args.format
            if not format_type:
                if args.input.lower().endswith('.json'):
                    format_type = 'json'
                elif args.input.lower().endswith('.csv'):
                    format_type = 'csv'
                else:
                    raise ValueError("Could not determine file format. Use --format to specify.")

            if format_type == 'json':
                new_records, result = pipeline.ingest_json(args.input, source_metadata)
            else:
                new_records, result = pipeline.ingest_csv(args.input, source_metadata)

            # Generate change report
            change_report = pipeline.generate_change_report(existing_records, new_records)

            print("=== CHANGE REPORT ===")
            print(f"Dataset version: {change_report.dataset_version}")
            print(f"Added records: {len(change_report.added_records)}")
            print(f"Modified records: {len(change_report.modified_records)}")
            print(f"Removed records: {len(change_report.removed_records)}")
            print(f"Unchanged records: {len(change_report.unchanged_records)}")

            # Save new dataset if not dry run
            if not args.dry_run:
                output_path = pipeline.save_normalized_dataset(new_records, args.output)
                print(f"\nUpdated dataset saved to: {output_path}")

            return 0

    except Exception as e:
        logger.error(f"Error during pipeline execution: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())