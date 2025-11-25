from typing import List

def split_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Divide o texto em chunks com sobreposição."""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks
