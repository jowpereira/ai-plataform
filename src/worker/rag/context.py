from __future__ import annotations

import logging
import time
from typing import Any, Literal, Mapping, Sequence

from agent_framework import ChatMessage, Context, ContextProvider, Role

from src.worker.providers.embeddings import EmbeddingProvider
from src.worker.rag.interfaces import VectorMatch, VectorStore

logger = logging.getLogger("worker.rag.context")

RagStrategy = Literal["last_message", "conversation"]


class RAGContextProvider(ContextProvider):
    """ContextProvider compatível com Agent Framework usando VectorStore em memória."""

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
            return Context()

        query_text = self._build_query(filtered)
        if not query_text:
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
            return Context()

        logger.debug(
            "Contexto RAG gerado com %s trechos (embedding %.1fms | busca %.1fms)",
            len(matches),
            embed_duration,
            search_duration,
        )

        context_messages = [ChatMessage(role=Role.USER, text=self._context_prompt)]
        context_messages.extend(ChatMessage(role=Role.USER, text=self._format_match(idx + 1, match)) for idx, match in enumerate(matches))
        return Context(messages=context_messages)

    def _build_query(self, messages: Sequence[ChatMessage]) -> str:
        if self._strategy == "conversation":
            return "\n".join(msg.text.strip() for msg in messages if msg.text)
        for msg in reversed(messages):
            if msg.role == Role.USER and msg.text:
                return msg.text.strip()
        return messages[-1].text.strip() if messages and messages[-1].text else ""

    @staticmethod
    def _format_match(index: int, match: VectorMatch) -> str:
        source = match.metadata.get("source") or match.metadata.get("path") or match.document_id
        score = f"score={match.score:.3f}"
        header = f"[{index}] {source} ({score})"
        chunk = match.content.strip()
        if not chunk:
            chunk = "Trecho vazio"
        return f"{header}\n{chunk}"