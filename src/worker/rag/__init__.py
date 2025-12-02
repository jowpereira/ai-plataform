"""RAG (Retrieval Augmented Generation) module for MAIA platform."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Mapping

from src.worker.config import ModelConfig, RagConfig, WorkerConfig
from src.worker.providers.embeddings import EmbeddingProvider, EmbeddingRegistry
from src.worker.rag.context import RAGContextProvider, RAGMatch
from src.worker.rag.interfaces import VectorStore
from src.worker.rag.stores.memory import InMemoryVectorStore

from .citation_processor import Citation, CitationProcessor, integrate_rag_with_agent_framework

logger = logging.getLogger("worker.rag.runtime")


@dataclass(slots=True)
class RagRuntimeState:
    """Estado global do runtime RAG."""

    rag_config: RagConfig
    embeddings: EmbeddingProvider
    store: VectorStore
    worker_config: WorkerConfig | None = None
    global_provider: RAGContextProvider | None = None


_runtime_state: RagRuntimeState | None = None
_vector_store: VectorStore | None = None

# Hub global para armazenar os últimos matches de qualquer provider
# Isso permite que o executor acesse os matches após a execução do workflow
_last_global_matches: list[RAGMatch] = []


def publish_rag_matches(matches: list[RAGMatch]) -> None:
    """Publica matches RAG para acesso global (chamado pelos providers)."""
    global _last_global_matches
    _last_global_matches = list(matches)
    if matches:
        logger.debug(f"📚 RAG matches publicados globalmente: {len(matches)}")


def get_last_rag_matches() -> list[RAGMatch]:
    """Retorna os últimos matches RAG publicados (para uso pelo executor)."""
    return _last_global_matches


def clear_rag_matches() -> None:
    """Limpa os matches RAG globais (chamar antes de nova execução)."""
    global _last_global_matches
    _last_global_matches = []


def configure_rag_runtime(config: WorkerConfig | None) -> RagRuntimeState | None:
    """Configura o runtime RAG a partir de um WorkerConfig completo."""

    if not config or not config.rag or not config.rag.enabled:
        logger.info("RAG não habilitado para este worker")
        return None

    if not config.rag.embedding:
        logger.warning("Configuração RAG sem embedding definido – ignorando")
        return None

    model_config = config.resources.models.get(config.rag.embedding.model)
    if not model_config:
        raise ValueError(
            f"Modelo de embedding '{config.rag.embedding.model}' não encontrado em resources.models"
        )

    runtime = _create_runtime_state(
        rag_config=config.rag,
        model_config=model_config,
        worker_config=config,
    )
    _set_runtime_state(runtime)
    logger.info(
        "RAG configurado com sucesso (modelo: %s | namespace: %s)",
        config.rag.embedding.model,
        config.rag.namespace,
    )
    return runtime


def configure_rag_runtime_from_config(rag_config: RagConfig | None) -> RagRuntimeState | None:
    """Configura o runtime RAG apenas com RagConfig (usado pelo DevUI/CLI)."""

    if not rag_config or not rag_config.enabled:
        logger.info("RAG desabilitado – configuração não aplicada")
        return None

    if not rag_config.embedding:
        logger.warning("RagConfig fornecida sem embedding – ignorando")
        return None

    model_config = _resolve_model_from_env(rag_config.embedding.model)
    runtime = _create_runtime_state(rag_config=rag_config, model_config=model_config)
    _set_runtime_state(runtime)
    logger.info(
        "RAG configurado via RagConfig (modelo: %s | namespace: %s)",
        rag_config.embedding.model,
        rag_config.namespace,
    )
    return runtime


def get_context_provider() -> RAGContextProvider | None:
    """Retorna o provider de contexto global configurado para o worker."""

    return _runtime_state.global_provider if _runtime_state else None


def create_agent_context_provider(
    collection_ids: Iterable[str] | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
) -> RAGContextProvider | None:
    """Cria um ContextProvider específico para um agente/coleção."""

    if not _runtime_state:
        logger.warning("create_agent_context_provider chamado sem runtime configurado")
        return None

    rag_config = _runtime_state.rag_config
    metadata_filters: Mapping[str, object] | None = None

    if collection_ids:
        metadata_filters = {"collection_id": {"$in": list(collection_ids)}}

    provider = _build_context_provider(
        rag_config=rag_config,
        store=_runtime_state.store,
        embeddings=_runtime_state.embeddings,
        top_k=top_k,
        min_score=min_score,
        metadata_filters=metadata_filters,
    )
    logger.debug(
        "ContextProvider especializado criado (collections=%s, top_k=%s)",
        list(collection_ids) if collection_ids else None,
        top_k or rag_config.top_k,
    )
    return provider


def get_rag_runtime() -> RagRuntimeState | None:
    """Retorna o runtime RAG atual (store, embeddings, config)."""

    return _runtime_state


def register_vector_store(store_instance: VectorStore) -> None:
    """Registra um VectorStore externo (ex.: KnowledgeBaseService)."""

    global _vector_store
    _vector_store = store_instance
    logger.info("VectorStore externo registrado: %s", type(store_instance).__name__)
    _refresh_runtime_store()


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _set_runtime_state(state: RagRuntimeState) -> None:
    global _runtime_state
    _runtime_state = state
    _refresh_runtime_store()


def _refresh_runtime_store() -> None:
    if not _runtime_state:
        return

    if _vector_store:
        _runtime_state.store = _vector_store
        _runtime_state.global_provider = _build_context_provider(
            rag_config=_runtime_state.rag_config,
            store=_vector_store,
            embeddings=_runtime_state.embeddings,
        )


def _create_runtime_state(
    *,
    rag_config: RagConfig,
    model_config: ModelConfig,
    worker_config: WorkerConfig | None = None,
) -> RagRuntimeState:
    store = _vector_store or InMemoryVectorStore()
    embedding_cfg = rag_config.embedding

    provider = EmbeddingRegistry.create_provider(
        model_config,
        dimensions=getattr(embedding_cfg, "dimensions", None),
        normalize=getattr(embedding_cfg, "normalize", True),
    )

    global_provider = _build_context_provider(
        rag_config=rag_config,
        store=store,
        embeddings=provider,
    )

    return RagRuntimeState(
        rag_config=rag_config,
        embeddings=provider,
        store=store,
        worker_config=worker_config,
        global_provider=global_provider,
    )


def _build_context_provider(
    *,
    rag_config: RagConfig,
    store: VectorStore,
    embeddings: EmbeddingProvider,
    top_k: int | None = None,
    min_score: float | None = None,
    metadata_filters: Mapping[str, object] | None = None,
) -> RAGContextProvider:
    return RAGContextProvider(
        store=store,
        embeddings=embeddings,
        top_k=top_k or rag_config.top_k,
        min_score=min_score if min_score is not None else rag_config.min_score,
        strategy=rag_config.strategy,
        context_prompt=rag_config.context_prompt,
        namespace=rag_config.namespace,
        metadata_filters=metadata_filters,
    )


def _resolve_model_from_env(model_name: str) -> ModelConfig:
    """Resolve provider/type para embeddings quando não há resources disponíveis."""

    if os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_API_KEY"):
        deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", model_name)
        provider_type = "azure-openai"
    else:
        deployment = model_name
        provider_type = "openai"

    return ModelConfig(type=provider_type, deployment=deployment)


__all__ = [
    "CitationProcessor",
    "Citation",
    "integrate_rag_with_agent_framework",
    "RAGContextProvider",
    "RAGMatch",
    "configure_rag_runtime",
    "configure_rag_runtime_from_config",
    "get_context_provider",
    "create_agent_context_provider",
    "get_rag_runtime",
    "register_vector_store",
    "RagRuntimeState",
    "publish_rag_matches",
    "get_last_rag_matches",
    "clear_rag_matches",
]