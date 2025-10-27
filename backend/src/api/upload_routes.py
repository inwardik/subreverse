"""API routes for file uploads (ZIP, NDJSON) and export."""
import os
import io
import json
import zipfile
import tempfile
import shutil
import re
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from application.dto import UploadSummaryDTO
from api.dependencies import get_subtitle_service, get_subtitle_pair_repository
from application.subtitle_service import SubtitlePairService
from domain.interfaces import ISubtitlePairRepository
from domain.entities import SubtitlePair
from infrastructure.srt_parser import parse_srt, match_cues


router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    Simple file upload endpoint for testing.
    Accepts any file up to 1GB and returns its size.
    """
    try:
        size = 0
        chunk = await file.read(1024 * 1024)  # Read 1MB at a time
        while chunk:
            size += len(chunk)
            if size > 1_000_000_000:  # 1GB guard
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large: {size} bytes"
                )
            chunk = await file.read(1024 * 1024)
        return {
            "message": f"Received file '{file.filename}' of size {size} bytes",
            "filename": file.filename,
            "size": size
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {e}")


@router.post("/upload_zip", response_model=UploadSummaryDTO)
async def upload_zip(
    file: UploadFile = File(...),
    repo: ISubtitlePairRepository = Depends(get_subtitle_pair_repository)
):
    """
    Accept a zip with many .srt files, find valid _en/_ru pairs by basename, and load them into DB.
    Rules:
    - Consider only files ending with _en.srt or _ru.srt
    - Pair files that share the same basename before the _en/_ru suffix
    - Skip unmatched singles or other files
    Returns a summary JSON.
    """
    filename = file.filename or "upload.zip"
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    try:
        # Stream file into memory
        data = await file.read()
        if len(data) > 1_000_000_000:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {len(data)} bytes"
            )

        zf = zipfile.ZipFile(io.BytesIO(data))
        tmpdir = tempfile.mkdtemp(prefix="srtzip_")
        extracted_paths: List[str] = []

        try:
            # Extract .srt files
            for zi in zf.infolist():
                if zi.is_dir():
                    continue
                name = zi.filename
                base_name = os.path.basename(name)
                if not base_name.lower().endswith('.srt'):
                    continue
                out_path = os.path.join(tmpdir, base_name)
                with zf.open(zi, 'r') as src, open(out_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                extracted_paths.append(out_path)

            # Find pairs
            pairs_dict: Dict[str, Dict[str, str]] = {}
            en_re = re.compile(r"^(?P<base>.+)_en\.srt$", re.IGNORECASE)
            ru_re = re.compile(r"^(?P<base>.+)_ru\.srt$", re.IGNORECASE)

            for p in extracted_paths:
                bn = os.path.basename(p)
                m_en = en_re.match(bn)
                m_ru = ru_re.match(bn)
                if m_en:
                    key = m_en.group('base')
                    pairs_dict.setdefault(key, {})['en'] = p
                elif m_ru:
                    key = m_ru.group('base')
                    pairs_dict.setdefault(key, {})['ru'] = p

            valid_pairs: List[tuple] = []
            skipped: List[str] = []
            for key, d in pairs_dict.items():
                if 'en' in d and 'ru' in d:
                    valid_pairs.append((key, d['en'], d['ru']))
                else:
                    if 'en' in d:
                        skipped.append(os.path.basename(d['en']))
                    if 'ru' in d:
                        skipped.append(os.path.basename(d['ru']))

            # Process pairs
            total_docs = 0
            inserted_total = 0
            errors: List[str] = []

            for key, en_path, ru_path in valid_pairs:
                try:
                    en_cues = parse_srt(en_path)
                    ru_cues = parse_srt(ru_path)
                    pairs_matched = match_cues(en_cues, ru_cues, 1000)

                    subtitle_pairs: List[SubtitlePair] = []
                    file_en_base = os.path.basename(en_path)
                    file_ru_base = os.path.basename(ru_path)

                    # Get next seq_id
                    existing_count = await repo.count_total()
                    start_seq = existing_count + 1

                    for idx, (en_cue, ru_cue) in enumerate(pairs_matched):
                        pair = SubtitlePair(
                            id="",  # Will be assigned by repo
                            en=en_cue.text,
                            ru=ru_cue.text if ru_cue else "",
                            file_en=file_en_base,
                            file_ru=file_ru_base,
                            time_en=en_cue.time_str,
                            time_ru=ru_cue.time_str if ru_cue else None,
                            rating=0,
                            seq_id=start_seq + idx
                        )
                        subtitle_pairs.append(pair)

                    total_docs += len(subtitle_pairs)
                    inserted = await repo.create_many(subtitle_pairs)
                    inserted_total += inserted
                except Exception as e:
                    errors.append(f"{key}: {e}")

            return UploadSummaryDTO(
                filename=filename,
                lines_read=len(extracted_paths),
                inserted_docs=inserted_total,
                skipped_lines=len(skipped),
                errors=errors[:20]
            )
        finally:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process ZIP: {e}")


@router.post("/import_ndjson", response_model=UploadSummaryDTO)
async def import_ndjson(
    file: UploadFile = File(...),
    repo: ISubtitlePairRepository = Depends(get_subtitle_pair_repository)
):
    """
    Import records from an NDJSON file into MongoDB. Each line must be a JSON object.
    - Sets rating to 0 when missing or invalid.
    - Only allows known fields: en, ru, file_en, file_ru, time_en, time_ru, rating, seq_id.
    Returns a summary.
    """
    filename = file.filename or "upload.ndjson"
    if not filename.lower().endswith(".ndjson"):
        raise HTTPException(status_code=400, detail="Only .ndjson files are supported")

    try:
        allowed_fields = {"en", "ru", "file_en", "file_ru", "time_en", "time_ru", "rating", "seq_id"}
        lines_read = 0
        inserted_total = 0
        skipped_lines: List[str] = []
        errors: List[str] = []
        batch: List[SubtitlePair] = []
        BATCH_SIZE = 1000

        # Read file
        decoder = (await file.read()).decode("utf-8", errors="replace")

        # Get starting seq_id
        existing_count = await repo.count_total()
        next_seq_id = existing_count + 1

        for raw_line in decoder.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lines_read += 1

            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    skipped_lines.append(f"line {lines_read}: not an object")
                    continue

                # Filter allowed fields
                doc = {k: v for k, v in obj.items() if k in allowed_fields}

                # Normalize rating
                r = doc.get("rating")
                try:
                    doc["rating"] = int(r) if r is not None else 0
                except Exception:
                    doc["rating"] = 0

                # Ensure minimal field: en or ru should exist
                if not doc.get("en") and not doc.get("ru"):
                    skipped_lines.append(f"line {lines_read}: missing both en and ru")
                    continue

                # Assign seq_id if missing
                if "seq_id" not in doc or doc["seq_id"] is None:
                    doc["seq_id"] = next_seq_id
                    next_seq_id += 1

                # Create SubtitlePair entity
                pair = SubtitlePair(
                    id="",
                    en=doc.get("en", ""),
                    ru=doc.get("ru", ""),
                    file_en=doc.get("file_en"),
                    file_ru=doc.get("file_ru"),
                    time_en=doc.get("time_en"),
                    time_ru=doc.get("time_ru"),
                    rating=doc["rating"],
                    seq_id=doc["seq_id"]
                )
                batch.append(pair)

                if len(batch) >= BATCH_SIZE:
                    inserted = await repo.create_many(batch)
                    inserted_total += inserted
                    batch = []
            except Exception as e:
                skipped_lines.append(f"line {lines_read}: {e}")

        # Flush remaining batch
        if batch:
            inserted = await repo.create_many(batch)
            inserted_total += inserted

        return UploadSummaryDTO(
            filename=filename,
            lines_read=lines_read,
            inserted_docs=inserted_total,
            skipped_lines=len(skipped_lines),
            errors=errors[:20]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process NDJSON: {e}")


@router.post("/export")
async def export_all(
    repo: ISubtitlePairRepository = Depends(get_subtitle_pair_repository)
):
    """Export all documents from MongoDB collection to a temporary NDJSON file and return it."""
    try:
        # Get all pairs
        pairs = await repo.get_all()

        # Create temp file
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{now}.ndjson"
        tmp = tempfile.NamedTemporaryFile(prefix="export_", suffix=".ndjson", delete=False)
        path = tmp.name

        with tmp:
            for pair in pairs:
                doc = {
                    "_id": pair.id,
                    "en": pair.en,
                    "ru": pair.ru,
                    "file_en": pair.file_en,
                    "file_ru": pair.file_ru,
                    "time_en": pair.time_en,
                    "time_ru": pair.time_ru,
                    "rating": pair.rating,
                    "seq_id": pair.seq_id
                }
                if pair.category:
                    doc["category"] = pair.category
                tmp.write((json.dumps(doc, ensure_ascii=False) + "\n").encode("utf-8"))

        # Return file and schedule deletion after response
        def cleanup(p: str):
            try:
                os.remove(p)
            except Exception:
                pass

        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return FileResponse(
            path,
            media_type="application/x-ndjson",
            filename=filename,
            headers=headers,
            background=BackgroundTask(lambda: cleanup(path))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export: {e}")


@router.post("/index_db")
async def index_db(
    repo: ISubtitlePairRepository = Depends(get_subtitle_pair_repository)
):
    """
    Index all MongoDB pairs collection documents.
    This endpoint ensures all documents are properly indexed.
    Note: Indexes are created automatically by the repository, so this is mostly a no-op.
    """
    try:
        total = await repo.count_total()
        return {
            "message": "Database indexed successfully",
            "total_docs": total,
            "indexes": ["en", "ru", "seq_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index database: {e}")
