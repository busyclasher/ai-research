from __future__ import annotations

import json
from pathlib import Path
from typing import BinaryIO

from app.config import get_settings

settings = get_settings()


def store_raw_asset(document_id: str, filename: str, stream: BinaryIO) -> str:
    """Persist the uploaded raw asset to disk and return its URI."""

    document_dir = settings.raw_storage_path / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(filename).name or "payload"
    destination = document_dir / safe_filename

    with destination.open("wb") as fh:
        while chunk := stream.read(1024 * 1024):
            fh.write(chunk)

    return str(destination)


def store_json_payload(document_id: str, name: str, payload: dict) -> str:
    """Persist derived JSON payloads (e.g., transcripts) to disk."""

    document_dir = settings.derived_storage_path / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    destination = document_dir / f"{name}.json"

    with destination.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    return str(destination)
