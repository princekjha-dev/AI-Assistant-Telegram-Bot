"""
Nexus — Media Processing Service
Handles images, voice, PDFs, and document files.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nexus.media")


async def extract_text_from_bytes(
    file_bytes: bytes,
    mime_type: str,
    filename: str = "",
) -> Optional[str]:
    """
    Extract text from various file formats.
    Returns extracted text or None.
    """
    try:
        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            return await _extract_pdf(file_bytes)
        elif mime_type.startswith("text/") or filename.lower().endswith((".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".html", ".xml")):
            return file_bytes.decode("utf-8", errors="replace")
        else:
            # Try decode as text anyway
            try:
                return file_bytes.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                return None
    except Exception as exc:
        logger.warning("Text extraction failed for %s: %s", filename, exc)
        return None


async def _extract_pdf(file_bytes: bytes) -> Optional[str]:
    """Extract text from PDF using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages) if pages else None
    except ImportError:
        logger.warning("pypdf not installed — PDF extraction unavailable")
        return "[PDF processing requires pypdf. Install it with: pip install pypdf]"
    except Exception as exc:
        logger.warning("PDF extraction error: %s", exc)
        return None


def truncate_text(text: str, max_chars: int = 8000) -> str:
    """Truncate text to fit in context window."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[... truncated — {len(text) - max_chars} characters omitted]"


async def convert_ogg_to_wav(ogg_bytes: bytes) -> Optional[bytes]:
    """Convert OGG/Opus voice data to WAV for transcription."""
    try:
        import pydub
        audio = pydub.AudioSegment.from_ogg(io.BytesIO(ogg_bytes))
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        return wav_io.getvalue()
    except Exception as exc:
        logger.warning("Audio conversion failed: %s", exc)
        return ogg_bytes  # Return original bytes as fallback
