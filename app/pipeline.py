from __future__ import annotations

import logging
from pathlib import Path

from app.db import session_scope
from app.models import Chunk, Document, DocumentStatus, DerivedAsset
from app.storage import store_json_payload

logger = logging.getLogger(__name__)


def process_document(document_id: str) -> None:
    """Run extraction + chunking pipeline for a document."""

    with session_scope() as session:
        document = session.get(Document, document_id)
        if not document:
            logger.warning("Document %s not found for processing", document_id)
            return

        document.status = DocumentStatus.PROCESSING
        session.flush()

    try:
        chunks, derived_assets = _extract_assets(document_id)
    except Exception:
        logger.exception("Failed to process document %s", document_id)
        with session_scope() as session:
            document = session.get(Document, document_id)
            if document:
                document.status = DocumentStatus.FAILED
        raise

    with session_scope() as session:
        document = session.get(Document, document_id)
        if not document:
            logger.warning("Document %s disappeared before completion", document_id)
            return

        for asset in derived_assets:
            session.add(asset)

        for chunk in chunks:
            session.add(chunk)

        document.status = DocumentStatus.INDEXED


def _extract_assets(document_id: str) -> tuple[list[Chunk], list[DerivedAsset]]:
    """Placeholder extraction pipeline operating on local files."""

    from app.config import get_settings

    settings = get_settings()
    raw_dir = settings.raw_storage_path / document_id
    if not raw_dir.exists():
        raise FileNotFoundError(f"Missing raw assets for {document_id}")

    chunks: list[Chunk] = []
    derived_assets: list[DerivedAsset] = []

    for raw_file in raw_dir.iterdir():
        if raw_file.suffix.lower() in {".txt", ""}:
            text = raw_file.read_text(encoding="utf-8", errors="ignore")
            derived_assets.extend(_handle_text_asset(document_id, raw_file, text))
            chunks.extend(_chunk_text(document_id, text, raw_file.name))
        else:
            payload = {"note": "processing for this modality is not yet implemented"}
            uri = store_json_payload(document_id, raw_file.stem, payload)
            derived_assets.append(
                DerivedAsset(
                    document_id=document_id,
                    asset_type="placeholder",
                    uri=uri,
                    payload=payload,
                )
            )

    return chunks, derived_assets


def _handle_text_asset(document_id: str, raw_file: Path, text: str) -> list[DerivedAsset]:
    payload = {"raw_file": raw_file.name, "length": len(text)}
    uri = store_json_payload(document_id, raw_file.stem, payload)
    return [
        DerivedAsset(
            document_id=document_id,
            asset_type="text_metadata",
            uri=uri,
            payload=payload,
        )
    ]


def _chunk_text(document_id: str, text: str, filename: str, max_chars: int = 800) -> list[Chunk]:
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    segments: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in normalized.split("\n\n"):
        para = paragraph.strip()
        if not para:
            continue
        if current_length + len(para) <= max_chars:
            current.append(para)
            current_length += len(para) + 2
        else:
            if current:
                segments.append("\n\n".join(current))
            segments.append(para)
            current = []
            current_length = 0

    if current:
        segments.append("\n\n".join(current))

    chunks: list[Chunk] = []
    for ordinal, segment in enumerate(segments):
        chunks.append(
            Chunk(
                document_id=document_id,
                modality="text",
                ordinal=ordinal,
                text=segment,
                metadata={"source_filename": filename},
            )
        )

    return chunks
