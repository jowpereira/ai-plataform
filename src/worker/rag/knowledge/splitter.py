from __future__ import annotations

import re
from typing import Iterable


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Divide o texto em chunks preservando parágrafos quando possível."""

    normalized = _normalize_whitespace(text)
    paragraphs = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_size = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        # Parágrafos muito grandes são quebrados artificialmente para evitar overflows
        if paragraph_len > chunk_size:
            if buffer:
                chunks.append("\n\n".join(buffer))
                buffer = []
                buffer_size = 0
            chunks.extend(_split_long_paragraph(paragraph, chunk_size, chunk_overlap))
            continue

        if buffer_size + paragraph_len + 2 <= chunk_size:
            buffer.append(paragraph)
            buffer_size += paragraph_len + 2
        else:
            chunks.append("\n\n".join(buffer))
            overlap_content = _get_overlap(buffer, chunk_overlap)
            buffer = overlap_content + [paragraph]
            buffer_size = sum(len(part) + 2 for part in buffer)

    if buffer:
        chunks.append("\n\n".join(buffer))

    # Remover duplicados triviais e garantir tamanho mínimo
    unique_chunks = []
    seen = set()
    for chunk in chunks:
        normalized_chunk = chunk.strip()
        if len(normalized_chunk) < 40:
            continue
        key = normalized_chunk[:120]
        if key in seen:
            continue
        seen.add(key)
        unique_chunks.append(normalized_chunk)

    return unique_chunks


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t", "    ", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def _split_long_paragraph(paragraph: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    tokens = paragraph.split(" ")
    chunks: list[str] = []
    buffer: list[str] = []
    size = 0

    for token in tokens:
        token_len = len(token) + 1
        if size + token_len <= chunk_size:
            buffer.append(token)
            size += token_len
        else:
            chunks.append(" ".join(buffer))
            overlap_tokens = _get_overlap(buffer, chunk_overlap)
            buffer = overlap_tokens + [token]
            size = sum(len(part) + 1 for part in buffer)

    if buffer:
        chunks.append(" ".join(buffer))

    return chunks


def _get_overlap(buffer: Iterable[str], chunk_overlap: int) -> list[str]:
    reversed_parts = list(buffer)[::-1]
    overlap: list[str] = []
    size = 0
    for part in reversed_parts:
        part_len = len(part) + 2
        if size + part_len > chunk_overlap:
            break
        overlap.insert(0, part)
        size += part_len
    return overlap
