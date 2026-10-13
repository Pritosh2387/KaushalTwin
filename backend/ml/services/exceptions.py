"""
KaushalTwin ML Service — Domain-Specific Exceptions
Module 0: Shared Infrastructure
"""

from __future__ import annotations


class MLServiceError(Exception):
    """Base exception for all ML service errors."""

    def __init__(self, message: str, error_code: str = "ML_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class SkillExtractionError(MLServiceError):
    """Raised when skill extraction fails."""

    def __init__(self, message: str):
        super().__init__(message, "SKILL_EXTRACTION_ERROR")


class NOSMappingError(MLServiceError):
    """Raised when NOS mapping fails."""

    def __init__(self, message: str):
        super().__init__(message, "NOS_MAPPING_ERROR")


class EvidenceValidationError(MLServiceError):
    """Raised when evidence validation fails."""

    def __init__(self, message: str):
        super().__init__(message, "EVIDENCE_VALIDATION_ERROR")


class InsufficientEvidenceError(MLServiceError):
    """Raised when there is insufficient evidence for assessment."""

    def __init__(self, message: str):
        super().__init__(message, "INSUFFICIENT_EVIDENCE_ERROR")


class AssessmentConfigurationError(MLServiceError):
    """Raised when assessment configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(message, "ASSESSMENT_CONFIGURATION_ERROR")


class MLProviderError(MLServiceError):
    """Raised when an ML provider fails."""

    def __init__(self, message: str, provider_name: str = "unknown"):
        super().__init__(message, "ML_PROVIDER_ERROR")
        self.provider_name = provider_name


class InvalidInputError(MLServiceError):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message, "INVALID_INPUT")


class ConfigurationError(MLServiceError):
    """Raised when service configuration is invalid or missing."""

    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")