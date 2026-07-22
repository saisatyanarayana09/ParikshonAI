import os
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import UploadedFile


def save_temp_upload(uploaded_file: UploadedFile) -> str:
    extension = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        return tmp.name


def safe_delete(path: str) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            return


def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\x00", "").splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return " ".join(cleaned.split()) if len(cleaned) < 500 else cleaned


def split_text(text: str, max_chars: int = 3500, overlap: int = 350) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        boundary = text.rfind("\n", start, end)
        if boundary == -1 or boundary <= start + 500:
            boundary = text.rfind(". ", start, end)
        if boundary == -1 or boundary <= start + 500:
            boundary = end
        chunks.append(text[start:boundary].strip())
        start = max(boundary - overlap, boundary)
        if start == boundary:
            start = boundary
    return [chunk for chunk in chunks if chunk]
