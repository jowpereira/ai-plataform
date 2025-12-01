from __future__ import annotations

import asyncio
import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, DefaultDict, Mapping, Sequence

from src.worker.providers.embeddings import Vector
from src.worker.rag.interfaces import VectorDocument, VectorMatch, VectorStore

logger = logging.getLogger("worker.rag.store.memory")


@dataclass(slots=True)
class _StoredDocument:
    document_id: str
    content: str
    metadata: dict[str, Any]
    vector: Vector
    namespace: str


class InMemoryVectorStore(VectorStore):
    """Implementação simples de VectorStore baseada em memória."""

    def __init__(self, *, normalize: bool = True) -> None:
        self._normalize = normalize
        self._namespaces: DefaultDict[str, list[_StoredDocument]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def add_documents(self, documents: Sequence[VectorDocument]) -> None:
        if not documents:
            return

        async with self._lock:
            for doc in documents:
                if not doc.embedding:
                    raise ValueError(f"Documento '{doc.id}' não possui embedding gerado")
                namespace = doc.namespace or "default"
                vector = self._normalize_vector(doc.embedding)
                stored = _StoredDocument(
                    document_id=doc.id,
                    content=doc.text,
                    metadata=dict(doc.metadata or {}),
                    vector=vector,
                    namespace=namespace,
                )
                self._namespaces[namespace].append(stored)
                logger.debug("Documento %s persistido no namespace %s", doc.id, namespace)

    async def similarity_search(
        self,
        query: Vector,
        *,
        top_k: int,
        score_threshold: float | None = None,
        namespace: str | None = None,
        metadata_filters: Mapping[str, Any] | None = None,
    ) -> list[VectorMatch]:
        if not query:
            return []

        query_vector = self._normalize_vector(query)
        ns = namespace or "default"

        async with self._lock:
            candidates = list(self._namespaces.get(ns, [])) if ns != "*" else [
                doc for docs in self._namespaces.values() for doc in docs
            ]

        matches: list[VectorMatch] = []
        for stored in candidates:
            if metadata_filters and not self._metadata_matches(stored.metadata, metadata_filters):
                continue
            score = self._cosine_similarity(query_vector, stored.vector)
            if score_threshold is not None and score < score_threshold:
                continue
            matches.append(
                VectorMatch(
                    document_id=stored.document_id,
                    content=stored.content,
                    score=score,
                    metadata=stored.metadata,
                    namespace=ns if ns != "*" else stored.namespace,
                ),
            )

        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:top_k]

    async def clear(self, namespace: str | None = None) -> None:
        async with self._lock:
            if namespace:
                self._namespaces.pop(namespace, None)
            else:
                self._namespaces.clear()

    async def load_seed_documents(self, dataset: Sequence[VectorDocument]) -> None:
        """Atalho para carregar lotes iniciais durante testes."""
        await self.add_documents(dataset)

    def export_namespace(self, namespace: str | None = None) -> list[VectorDocument]:
        """Exporta o estado atual do namespace para debugging/comparação."""
        ns = namespace or "default"
        docs = self._namespaces.get(ns, []) if ns != "*" else [
            doc for docs in self._namespaces.values() for doc in docs
        ]
        exported: list[VectorDocument] = []
        for stored in docs:
            exported.append(
                VectorDocument(
                    id=stored.document_id,
                    text=stored.content,
                    metadata=dict(stored.metadata),
                    namespace=stored.namespace,
                    embedding=list(stored.vector),
                ),
            )
        return exported

    def _normalize_vector(self, vector: Sequence[float]) -> Vector:
        if not self._normalize:
            return list(vector)
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return list(vector)
        return [value / norm for value in vector]

    @staticmethod
    def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        if len(vec_a) != len(vec_b):
            logger.debug("Vetores de dimensões diferentes: %s vs %s", len(vec_a), len(vec_b))
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        denom_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
        denom_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
        return dot / (denom_a * denom_b)

    @staticmethod
    def _metadata_matches(metadata: Mapping[str, Any], filters: Mapping[str, Any]) -> bool:
        """Verifica se os metadados correspondem aos filtros especificados.
        
        Suporta operadores:
        - {"key": {"$in": [values...]}} - valor deve estar na lista
        - {"key": value} - igualdade direta
        - {"key": [values...]} - intersecção de conjuntos
        """
        for key, expected in filters.items():
            value = metadata.get(key)
            
            # Suporte a operadores estilo MongoDB
            if isinstance(expected, dict):
                # Operador $in: valor deve estar na lista
                if "$in" in expected:
                    allowed = expected["$in"]
                    if isinstance(value, (list, set, tuple)):
                        if not set(value).intersection(allowed):
                            return False
                    else:
                        if value not in allowed:
                            return False
                    continue
                # Outros operadores podem ser adicionados aqui
                # Para dicts não-operadores, comparação direta
                if value != expected:
                    return False
            elif isinstance(value, (list, set, tuple)):
                if isinstance(expected, (list, set, tuple)):
                    if not set(value).intersection(expected):
                        return False
                else:
                    if expected not in value:
                        return False
            else:
                if value != expected:
                    return False
        return True