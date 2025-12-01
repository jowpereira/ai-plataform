from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


_TEXT_EXTENSIONS = {".txt", ".md", ".log"}
_CSV_EXTENSIONS = {".csv", ".tsv", ".psv"}
_JSON_EXTENSIONS = {".json"}


class UnsupportedFileError(RuntimeError):
    """Arquivo com formato não suportado para ingestão."""


def extract_text(filename: str, content_type: str | None, raw_bytes: bytes) -> str:
    """Extrai texto bruto a partir do arquivo enviado.

    Implementa suporte básico a TXT, CSV/TSV, JSON e PDF.
    """

    extension = Path(filename).suffix.lower()

    if extension in _TEXT_EXTENSIONS or (content_type and content_type.startswith("text/")):
        return _decode_text(raw_bytes)

    if extension in _CSV_EXTENSIONS or content_type in {"text/csv", "text/tsv", "application/vnd.ms-excel"}:
        return _extract_csv(raw_bytes, delimiter=_guess_csv_delimiter(extension))

    if extension in _JSON_EXTENSIONS:
        return _extract_json(raw_bytes)

    if extension == ".pdf" or content_type == "application/pdf":
        return _extract_pdf(raw_bytes)

    raise UnsupportedFileError(
        f"Formato '{extension or content_type or 'desconhecido'}' não suportado. "
        "Envie arquivos TXT, CSV/TSV, JSON ou PDF."
    )


def _decode_text(raw_bytes: bytes, encoding_candidates: Iterable[str] | None = None) -> str:
    encodings = list(encoding_candidates or []) + ["utf-8", "latin-1", "cp1252"]
    for encoding in encodings:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="ignore")


def _guess_csv_delimiter(extension: str) -> str:
    if extension == ".tsv":
        return "\t"
    if extension == ".psv":
        return "|"
    return ","


def _extract_csv(raw_bytes: bytes, delimiter: str) -> str:
    buffer = io.StringIO(_decode_text(raw_bytes))
    reader = csv.reader(buffer, delimiter=delimiter)
    rows = ["\t".join(cell.strip() for cell in row if cell) for row in reader]
    return "\n".join(row for row in rows if row)


def _extract_json(raw_bytes: bytes) -> str:
    data = json.loads(_decode_text(raw_bytes))
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False, indent=2)
    if isinstance(data, list):
        return "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
    return str(data)


def _extract_pdf(raw_bytes: bytes) -> str:
    buffer = io.BytesIO(raw_bytes)
    reader = PdfReader(buffer)
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(text)
    if not pages:
        raise UnsupportedFileError("Não foi possível extrair texto do PDF informado.")
    return "\n\n".join(pages)
