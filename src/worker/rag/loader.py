import requests
from typing import Optional

def load_text(source: str) -> str:
    """Carrega texto de um arquivo local ou URL."""
    if source.startswith("http"):
        response = requests.get(source)
        response.raise_for_status()
        return response.text
    else:
        with open(source, "r", encoding="utf-8") as f:
            return f.read()

def load_pdf(path: str) -> str:
    """Carrega texto de um PDF (Stub)."""
    # TODO: Implementar com pypdf ou similar
    return f"Conteúdo simulado do PDF {path}"
