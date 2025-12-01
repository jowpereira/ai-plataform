from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from agent_framework import ContextProvider

# Reutiliza tipo do provider centralizado
from src.worker.providers.embeddings import EmbeddingProvider, Vector


@dataclass(slots=True)
class VectorDocument:
    """Documento vetorial pronto para persistência no VectorStore."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    namespace: str = "default"
    embedding: Vector | None = None


@dataclass(slots=True)
class VectorMatch:
    """Resultado de similaridade retornado pelo VectorStore."""

    document_id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    namespace: str = "default"


class VectorStore(ABC):
    """Contrato base para implementação de Vector Stores."""

    @abstractmethod
    async def add_documents(self, documents: Sequence[VectorDocument]) -> None:
        """Persiste documentos vetorizados no namespace configurado."""

    @abstractmethod
    async def similarity_search(
        self,
        query: Vector,
        *,
        top_k: int,
        score_threshold: float | None = None,
        namespace: str | None = None,
        metadata_filters: Mapping[str, Any] | None = None,
    ) -> list[VectorMatch]:
        """Busca os documentos mais similares ao vetor informado."""

    @abstractmethod
    async def clear(self, namespace: str | None = None) -> None:
        """Remove documentos de um namespace específico ou de toda a store."""


ContextProviderProtocol = ContextProvider

__all__ = [
    "Vector",
    "VectorDocument",
    "VectorMatch",
    "EmbeddingProvider",
    "VectorStore",
    "ContextProviderProtocol",
]
