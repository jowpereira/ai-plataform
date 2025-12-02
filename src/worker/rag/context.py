from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from agent_framework import ChatMessage, Context, ContextProvider, Role

from src.worker.providers.embeddings import EmbeddingProvider
from src.worker.rag.interfaces import VectorMatch, VectorStore

logger = logging.getLogger("worker.rag.context")

RagStrategy = Literal["last_message", "conversation"]

# Instrução de citação no final do contexto RAG (estilo Azure Search Demo)
CITATION_INSTRUCTION = """
---
Lembre-se: Ao responder, cite as fontes usando [1], [2], etc. no texto da resposta.
Exemplo: "A política permite até 30 dias de férias [1]."
"""


@dataclass
class RAGMatch:
    """Representa um match RAG para uso externo (ex: criar annotations)."""

    index: int
    document_id: str
    source: str
    content: str
    score: float
    metadata: dict[str, Any]


class RAGContextProvider(ContextProvider):
    """ContextProvider compatível com Agent Framework usando VectorStore em memória.

    Injeta contexto de documentos relevantes antes da chamada ao LLM,
    incluindo instruções explícitas para citar fontes.
    """

    def __init__(
        self,
        *,
        store: VectorStore,
        embeddings: EmbeddingProvider,
        top_k: int,
        min_score: float | None,
        strategy: RagStrategy,
        context_prompt: str,
        namespace: str,
        metadata_filters: Mapping[str, Any] | None = None,
    ) -> None:
        self._store = store
        self._embeddings = embeddings
        self._top_k = top_k
        self._min_score = min_score
        self._strategy = strategy
        self._context_prompt = context_prompt
        self._namespace = namespace
        self._metadata_filters = metadata_filters
        # Armazena últimos matches para acesso externo (criar annotations)
        self._last_matches: list[RAGMatch] = []

    @property
    def last_matches(self) -> list[RAGMatch]:
        """Retorna os últimos matches RAG encontrados (útil para criar annotations)."""
        return self._last_matches

    async def invoking(
        self,
        messages: ChatMessage | Sequence[ChatMessage],
        **_: Any,
    ) -> Context:
        message_list = [messages] if isinstance(messages, ChatMessage) else list(messages)
        filtered = [
            msg for msg in message_list if msg and msg.text and msg.text.strip() and msg.role in (Role.USER, Role.ASSISTANT)
        ]
        if not filtered:
            self._last_matches = []
            return Context()

        query_text = self._build_query(filtered)
        if not query_text:
            self._last_matches = []
            return Context()

        start = time.perf_counter()
        query_vector = await self._embeddings.embed_query(query_text)
        embed_duration = (time.perf_counter() - start) * 1000

        search_start = time.perf_counter()
        matches = await self._store.similarity_search(
            query_vector,
            top_k=self._top_k,
            score_threshold=self._min_score,
            namespace=self._namespace,
            metadata_filters=self._metadata_filters,
        )
        search_duration = (time.perf_counter() - search_start) * 1000

        if not matches:
            logger.debug("Sem contexto RAG para a consulta atual")
            self._last_matches = []
            return Context()

        logger.debug(
            "Contexto RAG gerado com %s trechos (embedding %.1fms | busca %.1fms)",
            len(matches),
            embed_duration,
            search_duration,
        )

        # Armazenar matches para acesso externo
        self._last_matches = [
            RAGMatch(
                index=idx + 1,
                document_id=match.document_id,
                source=match.metadata.get("source") or match.metadata.get("path") or match.document_id,
                content=match.content.strip() or "Trecho vazio",
                score=match.score,
                metadata=dict(match.metadata),
            )
            for idx, match in enumerate(matches)
        ]
        
        # Publicar matches globalmente para acesso pelo executor após workflow
        try:
            from src.worker.rag import publish_rag_matches
            publish_rag_matches(self._last_matches)
        except ImportError:
            pass  # Ignorar se não disponível

        # Montar contexto: prompt inicial + trechos numerados + instrução de citação
        context_parts = [self._context_prompt]
        context_parts.extend(self._format_match(m) for m in self._last_matches)
        context_parts.append(CITATION_INSTRUCTION)

        full_context = "\n\n".join(context_parts)
        return Context(messages=[ChatMessage(role=Role.USER, text=full_context)])

    def _build_query(self, messages: Sequence[ChatMessage]) -> str:
        if self._strategy == "conversation":
            return "\n".join(msg.text.strip() for msg in messages if msg.text)
        for msg in reversed(messages):
            if msg.role == Role.USER and msg.text:
                return msg.text.strip()
        return messages[-1].text.strip() if messages and messages[-1].text else ""

    @staticmethod
    def _format_match(match: RAGMatch) -> str:
        """Formata um match RAG para inclusão no contexto."""
        header = f"[{match.index}] {match.source} (relevância: {match.score:.0%})"
        return f"{header}\n{match.content}"