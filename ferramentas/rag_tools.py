"""Ferramentas relacionadas ao pipeline RAG."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_framework import ai_function
from pydantic import BaseModel, Field, conint, constr

from src.worker.rag import get_rag_runtime

logger = logging.getLogger("ferramentas.rag")


class SearchKnowledgeBaseInput(BaseModel):
    query: constr(min_length=3, strip_whitespace=True) = Field(
        ..., description="Pergunta ou termo a ser procurado na base em memória.", examples=["política de reembolso"]
    )
    top_k: conint(ge=1, le=10) | None = Field(
        None,
        description="Quantidade máxima de trechos a retornar (usa default da config se omitido).",
    )
    namespace: constr(strip_whitespace=True) | None = Field(
        None,
        description="Namespace opcional para buscar documentos (default segue configuração atual).",
    )


@ai_function(
    name="search_knowledge_base",
    description=(
        "Pesquisa vetorial na base em memória configurada no pipeline RAG. "
        "Retorna trechos com score e metadados para referência rápida."
    ),
)
async def search_knowledge_base(payload: SearchKnowledgeBaseInput) -> str:
    runtime = get_rag_runtime()
    if not runtime or not runtime.config.rag or not runtime.config.rag.enabled:
        logger.warning("Tentativa de busca RAG sem runtime configurado")
        return "RAG não está habilitado para o worker atual."

    rag_config = runtime.config.rag
    namespace = payload.namespace or rag_config.namespace
    top_k = payload.top_k or rag_config.top_k

    query_vector = await runtime.embeddings.embed_query(payload.query)
    matches = await runtime.store.similarity_search(
        query_vector,
        top_k=top_k,
        score_threshold=rag_config.min_score,
        namespace=namespace,
    )

    if not matches:
        return json.dumps(
            {
                "query": payload.query,
                "namespace": namespace,
                "results": [],
                "message": "Nenhum documento relevante encontrado",
            },
            ensure_ascii=False,
        )

    formatted = [
        {
            "id": match.document_id,
            "score": round(match.score, 4),
            "namespace": match.namespace,
            "source": match.metadata.get("source") or match.metadata.get("path") or match.document_id,
            "snippet": match.content,
            "metadata": match.metadata,
        }
        for match in matches
    ]

    return json.dumps(
        {
            "query": payload.query,
            "namespace": namespace,
            "results": formatted,
        },
        ensure_ascii=False,
    )


__all__ = ["search_knowledge_base", "SearchKnowledgeBaseInput"]
