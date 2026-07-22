from .extractor import extract_text


def extract_ocr_text(path: str, filename: str) -> tuple[str, dict]:
    text, metadata = extract_text(path, filename)
    metadata["mode"] = "OCR" if metadata.get("used_ocr") else "Native text extraction"
    return text, metadata
