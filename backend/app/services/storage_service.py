"""
KaushalTwin Backend — Storage Service

Safe local file storage abstraction.
- Generates server-side UUIDs for filenames (no client paths trusted)
- Validates file extension and size
- Computes SHA-256 content hash
- Stores files under UPLOAD_DIRECTORY/<worker_id>/<uuid>.<ext>

The abstraction is designed to be swappable with object storage (S3, GCS)
by replacing only this module.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_upload_root() -> Path:
    root = Path(settings.UPLOAD_DIRECTORY)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _validate_extension(filename: str) -> str:
    """Return the extension if allowed; raise 400 otherwise."""
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not allowed. Allowed: {settings.allowed_extensions_set}",
        )
    return ext


async def save_upload(
    upload: UploadFile,
    worker_id: uuid.UUID,
) -> dict:
    """
    Save an uploaded file safely.

    Returns a dict with:
      file_path       — server-side relative path
      file_name       — original filename (for display)
      file_size_bytes — byte count
      mime_type       — from upload headers
      content_hash    — SHA-256 hex digest
    """
    if not upload.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    ext = _validate_extension(upload.filename)

    # Read content (enforcing size limit)
    content = await upload.read(settings.MAX_UPLOAD_SIZE + 1)
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE} bytes",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Compute hash
    content_hash = hashlib.sha256(content).hexdigest()

    # Generate server-side safe path
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    worker_dir = _get_upload_root() / str(worker_id)
    worker_dir.mkdir(parents=True, exist_ok=True)
    file_path = worker_dir / safe_name

    # Write to disk
    file_path.write_bytes(content)
    logger.info("Saved upload: %s (%d bytes)", file_path, len(content))

    return {
        "file_path": str(file_path),
        "file_name": upload.filename,
        "file_size_bytes": len(content),
        "mime_type": upload.content_type,
        "content_hash": content_hash,
    }


def get_file_path(stored_path: str) -> Path:
    """
    Resolve a stored path safely.
    Raises 404 if the file does not exist.
    Raises 403 if the path escapes the upload directory (path traversal check).
    """
    upload_root = _get_upload_root().resolve()
    resolved = Path(stored_path).resolve()

    # Path traversal guard
    try:
        resolved.relative_to(upload_root)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if not resolved.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return resolved
