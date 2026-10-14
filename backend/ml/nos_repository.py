"""
KaushalTwin ML Service — NOS Repository
Abstraction layer for loading and managing NOS data from various sources.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import logging

from ml.ingestion.pipeline import NOSRecord
from ml.services.exceptions import NOSMappingError

logger = logging.getLogger(__name__)


class NOSRepository:
    """Repository for managing NOS data with support for multiple sources."""

    def __init__(self):
        self._nos_cache: Optional[List[Dict[str, Any]]] = None
        self._nos_embeddings_cache: Optional[List[List[float]]] = None
        self._dataset_source: Optional[str] = None
        self._dataset_hash: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
        # Path to default demo data for backward compatibility
        self._demo_data_path = Path(__file__).parent / "data" / "demo_nos.json"
        # Path to official data acquired from government sources
        self._official_data_path = Path(__file__).parent / "data" / "official_nos.json"

    def load_official_data(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Load official NOS dataset if present, with graceful fallback to demo if missing.

        Returns:
            List of official NOS records as dictionaries
        """
        if not self._official_data_path.exists():
            logger.warning(
                f"Official NOS data file not found at {self._official_data_path}; falling back to demo data."
            )
            return self.load_demo_data(refresh=refresh)
        return self.load_nos_data(self._official_data_path, source_type="OFFICIAL", refresh=refresh)

    def load_demo_data(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Load synthetic demo NOS dataset.

        Returns:
            List of demo NOS records as dictionaries
        """
        return self.load_nos_data(self._demo_data_path, source_type="DEMO", refresh=refresh)

    def set_active_dataset(self, dataset_type: str) -> List[Dict[str, Any]]:
        """
        Explicitly set active dataset to 'official' or 'demo'.

        Args:
            dataset_type: 'official' or 'demo'

        Returns:
            Loaded records
        """
        if dataset_type.lower() == "official":
            return self.load_official_data(refresh=True)
        elif dataset_type.lower() == "demo":
            return self.load_demo_data(refresh=True)
        else:
            raise ValueError(f"Unknown dataset_type: '{dataset_type}'. Expected 'official' or 'demo'.")

    def load_nos_data(self,
                     data_source: Union[str, Path],
                     source_type: str = "auto",
                     refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Load NOS data from a specified source.

        Args:
            data_source: Path to NOS data file (JSON format)
            source_type: Type of source ("OFFICIAL", "DEMO", or "auto" to detect)
            refresh: Whether to force reload even if cached

        Returns:
            List of NOS records as dictionaries
        """
        data_source = Path(data_source)

        # Handle backward compatibility: if no specific source is provided and we have cached data, use it
        if not refresh and self._nos_cache is not None and self._dataset_source == str(data_source):
            logger.debug(f"Returning cached NOS data from {data_source}")
            return self._nos_cache

        # If no data source is provided, fall back to demo data for backward compatibility
        if str(data_source) == "" or str(data_source) == ".":
            data_source = self._demo_data_path

        if not data_source.exists():
            raise FileNotFoundError(f"NOS data file not found: {data_source}")

        try:
            with open(data_source, 'r', encoding='utf-8') as f:
                nos_data = json.load(f)
        except json.JSONDecodeError as e:
            raise NOSMappingError(f"Invalid NOS data format in {data_source}: {e}")

        # Handle different JSON structures
        if isinstance(nos_data, dict) and 'nos_records' in nos_data:
            nos_records = nos_data['nos_records']
            # Extract metadata
            self._metadata = {k: v for k, v in nos_data.items() if k != 'nos_records'}
        elif isinstance(nos_data, list):
            nos_records = nos_data
            self._metadata = {}
        else:
            nos_records = [nos_data]
            self._metadata = {}

        # Validate and normalize records
        validated_records = []
        for i, record in enumerate(nos_records):
            try:
                # Ensure required fields exist with sensible defaults
                nos_id = record.get('nos_id', record.get('id', f'UNKNOWN_{i}'))
                normalized_record = {
                    'id': record.get('id', nos_id),
                    'nos_id': nos_id,
                    'code': record.get('code', record.get('nos_id', record.get('id', f'UNKNOWN_{i}'))),
                    'title': record.get('title', ''),
                    'description': record.get('description', ''),
                    'mandatory': bool(record.get('mandatory', False)),
                    'weight': float(record.get('weight', 1.0)),
                    'trade': record.get('trade', 'unknown'),
                    'source_type': record.get('source_type', source_type.upper() if source_type != "auto" else "UNKNOWN"),
                    'performance_criteria': record.get('performance_criteria', []),
                    'keywords': record.get('keywords', []),
                }

                # Preserve provenance fields if present
                for prov_field in ['source_name', 'source_url', 'source_version', 'source_published_at',
                                   'retrieved_at', 'imported_at', 'content_hash']:
                    if prov_field in record:
                        normalized_record[prov_field] = record[prov_field]

                # Handle list fields that might be strings
                for field in ['performance_criteria', 'keywords']:
                    if isinstance(normalized_record[field], str):
                        try:
                            parsed = json.loads(normalized_record[field])
                            if isinstance(parsed, list):
                                normalized_record[field] = parsed
                        except (json.JSONDecodeError, TypeError):
                            normalized_record[field] = [item.strip() for item in normalized_record[field].split(',') if item.strip()]

                validated_records.append(normalized_record)

            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid NOS record at index {i}: {e}")
                continue

        self._nos_cache = validated_records
        self._dataset_source = str(data_source)
        self._nos_embeddings_cache = None  # Invalidate embeddings cache

        # Extract or compute dataset hash
        if isinstance(nos_data, dict) and '_metadata' in nos_data and 'content_hash' in nos_data['_metadata']:
            self._dataset_hash = nos_data['_metadata']['content_hash']
        else:
            try:
                import hashlib
                with open(data_source, 'rb') as f:
                    self._dataset_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                self._dataset_hash = None

        logger.info(f"Loaded {len(validated_records)} NOS records from {data_source}")
        return validated_records

    def clear_cache(self) -> None:
        """Clear all cached NOS data and reset state."""
        self._nos_cache = None
        self._nos_embeddings_cache = None
        self._dataset_source = None
        self._dataset_hash = None
        self._metadata = {}

    def get_nos_by_id(self, nos_id: str) -> Optional[Dict[str, Any]]:
        """Get a single NOS record by ID."""
        nos_list = self.load_nos_data(self._dataset_source or self._demo_data_path)
        for nos in nos_list:
            if nos.get('nos_id') == nos_id or nos.get('id') == nos_id or nos.get('code') == nos_id:
                return nos
        return None

    def get_all_nos(self) -> List[Dict[str, Any]]:
        """Get all NOS records."""
        # Use demo data as fallback if no source is set
        data_source = self._dataset_source or self._demo_data_path
        return self.load_nos_data(data_source)

    def search_nos(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search NOS records (delegates to skill service for actual implementation)."""
        # This is a placeholder - the actual search logic remains in skill_service.py
        # but now it will use data loaded through this repository
        from ml.services.skill_service import search_nos
        return search_nos(query, top_k)

    def get_dataset_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded dataset."""
        return {
            'source': self._dataset_source,
            'record_count': len(self._nos_cache) if self._nos_cache else 0,
            'hash': self._dataset_hash,
            'metadata': self._metadata
        }

    def is_official_data(self) -> bool:
        """Check if the currently loaded data is official."""
        if not self._nos_cache:
            return False
        # Check if any record has OFFICIAL source type
        official_count = sum(1 for record in self._nos_cache
                           if record.get('source_type', '').upper() == 'OFFICIAL')
        return official_count > 0

    def get_source_type_distribution(self) -> Dict[str, int]:
        """Get distribution of source types in the dataset."""
        if not self._nos_cache:
            return {}

        distribution = {}
        for record in self._nos_cache:
            source_type = record.get('source_type', 'UNKNOWN').upper()
            distribution[source_type] = distribution.get(source_type, 0) + 1

        return distribution


# Global repository instance
_nos_repository: Optional[NOSRepository] = None


def get_nos_repository() -> NOSRepository:
    """Get the global NOS repository instance."""
    global _nos_repository
    if _nos_repository is None:
        _nos_repository = NOSRepository()
    return _nos_repository