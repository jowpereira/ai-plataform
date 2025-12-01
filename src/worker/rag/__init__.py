from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

from agent_framework import ContextProvider

from src.worker.config import ModelConfig, WorkerConfig
from src.worker.providers.embeddings import EmbeddingProvider, EmbeddingRegistry
from src.worker.rag.context import RAGContextProvider
from src.worker.rag.interfaces import VectorStore
from src.worker.rag.stores import InMemoryVectorStore

logger = logging.getLogger("worker.rag.runtime")


@dataclass(slots=True)
class RagRuntime:
    config: WorkerConfig
    rag_provider: RAGContextProvider
    embeddings: EmbeddingProvider
    store: VectorStore


_runtime: RagRuntime | None = None
_external_store: VectorStore | None = None


def register_vector_store(store: VectorStore) -> None:
    """Permite que serviços externos forneçam o VectorStore utilizado pelo RAG."""

    global _external_store
    _external_store = store


def configure_rag_runtime_from_config(
    rag_config: "RagConfig",  # type: ignore[name-defined]
    model_configs: Mapping[str, ModelConfig] | None = None,
) -> RagRuntime | None:
    """
    Configura o RAG runtime usando RagConfig standalone.
    
    Esta versão é usada quando não temos um WorkerConfig completo,
    como no caso de agentes unitários carregados do servidor.
    
    Args:
        rag_config: Configuração RAG
        model_configs: Mapeamento de modelos (opcional, infere do ambiente se não fornecido)
        
    Returns:
        RagRuntime configurado ou None se RAG desabilitado
    """
    global _runtime
    
    if not rag_config or not rag_config.enabled:
        logger.debug("RAG desabilitado na configuração")
        return None
    
    if not rag_config.embedding:
        logger.warning("RagConfig.embedding deve estar definido quando RAG estiver habilitado")
        return None
    
    # Se model_configs não fornecido, criar um config mínimo baseado nas variáveis de ambiente
    if model_configs is None:
        import os
        embedding_model = rag_config.embedding.model
        model_configs = {
            embedding_model: ModelConfig(
                type="azure-openai",
                deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", embedding_model),
            )
        }
    
    try:
        embeddings = _build_embedding_provider(
            rag_config.embedding.model,
            rag_config.embedding.dimensions,
            rag_config.embedding.normalize,
            model_configs,
        )
    except Exception as e:
        logger.error("Falha ao criar embedding provider: %s", e)
        return None
    
    store = _external_store or InMemoryVectorStore()
    
    # Criar um WorkerConfig mínimo para o RagRuntime (necessário para create_agent_context_provider)
    from src.worker.config import WorkerConfig, ResourcesConfig, WorkflowConfig, WorkflowStep
    minimal_config = WorkerConfig(
        name="rag_runtime",
        resources=ResourcesConfig(models=model_configs, tools=[]),
        agents=[],
        workflow=WorkflowConfig(
            type="sequential",
            steps=[WorkflowStep(id="dummy", type="agent", agent="dummy")]
        ),
        rag=rag_config,
    )
    
    provider = RAGContextProvider(
        store=store,
        embeddings=embeddings,
        top_k=rag_config.top_k,
        min_score=rag_config.min_score,
        strategy=rag_config.strategy,
        context_prompt=rag_config.context_prompt,
        namespace=rag_config.namespace,
    )
    
    _runtime = RagRuntime(config=minimal_config, rag_provider=provider, embeddings=embeddings, store=store)
    logger.info("RAG runtime configurado via RagConfig standalone")
    return _runtime


def configure_rag_runtime(config: WorkerConfig) -> RagRuntime | None:
    global _runtime
    rag_config = config.rag
    if not rag_config or not rag_config.enabled:
        _runtime = None
        logger.debug("RAG desabilitado na configuração corrente")
        return None

    if not rag_config.embedding:
        raise ValueError("RagConfig.embedding deve estar definido quando RAG estiver habilitado")

    embeddings = _build_embedding_provider(
        rag_config.embedding.model,
        rag_config.embedding.dimensions,
        rag_config.embedding.normalize,
        config.resources.models,
    )
    store = _external_store or InMemoryVectorStore()
    provider = RAGContextProvider(
        store=store,
        embeddings=embeddings,
        top_k=rag_config.top_k,
        min_score=rag_config.min_score,
        strategy=rag_config.strategy,
        context_prompt=rag_config.context_prompt,
        namespace=rag_config.namespace,
    )

    _runtime = RagRuntime(config=config, rag_provider=provider, embeddings=embeddings, store=store)
    logger.info("RAG runtime configurado com provider %s", provider.__class__.__name__)
    return _runtime


def get_rag_runtime() -> RagRuntime | None:
    return _runtime


def get_context_provider() -> ContextProvider | None:
    runtime = get_rag_runtime()
    return runtime.rag_provider if runtime else None


def create_agent_context_provider(
    collection_ids: list[str],
    top_k: int = 5,
    min_score: float = 0.25,
) -> ContextProvider | None:
    """
    Cria um RAGContextProvider específico para um agente com filtros de coleção.
    
    Este método permite que cada agente tenha seu próprio ContextProvider
    configurado para buscar apenas nas coleções especificadas.
    
    Args:
        collection_ids: Lista de IDs das coleções permitidas
        top_k: Número máximo de chunks retornados
        min_score: Score mínimo de similaridade
        
    Returns:
        RAGContextProvider configurado ou None se RAG não estiver habilitado
    """
    runtime = get_rag_runtime()
    if not runtime:
        logger.debug("RAG runtime não configurado, não é possível criar provider para agente")
        return None
    
    if not collection_ids:
        logger.debug("collection_ids vazio, retornando provider global")
        return runtime.rag_provider
    
    # Criar metadata_filters para filtrar por collection_id
    # O VectorStore deve buscar documentos onde metadata.collection_id está na lista
    metadata_filters = {"collection_id": {"$in": collection_ids}}
    
    # Criar novo RAGContextProvider com os filtros específicos
    provider = RAGContextProvider(
        store=runtime.store,
        embeddings=runtime.embeddings,
        top_k=top_k,
        min_score=min_score,
        strategy=runtime.config.rag.strategy if runtime.config.rag else "last_message",
        context_prompt=runtime.config.rag.context_prompt if runtime.config.rag else (
            "Use os trechos a seguir como base de conhecimento. Cite as fontes disponíveis."
        ),
        namespace=runtime.config.rag.namespace if runtime.config.rag else "default",
        metadata_filters=metadata_filters,
    )
    
    logger.info(
        "Criado RAGContextProvider para agente com collections=%s, top_k=%d, min_score=%.2f",
        collection_ids,
        top_k,
        min_score,
    )
    return provider


def _build_embedding_provider(
    model_id: str,
    dimensions: int | None,
    normalize: bool,
    models: Mapping[str, ModelConfig],
) -> EmbeddingProvider:
    """
    Constrói um EmbeddingProvider usando o EmbeddingRegistry.
    
    Delega a criação para o registry centralizado de providers,
    seguindo o mesmo padrão do ProviderRegistry para LLMs.
    """
    if model_id not in models:
        raise ValueError(f"Modelo de embeddings '{model_id}' não encontrado em resources.models")

    model_config = models[model_id]
    
    return EmbeddingRegistry.create_provider(
        model_config,
        dimensions=dimensions,
        normalize=normalize,
    )


__all__ = [
    "RagRuntime",
    "configure_rag_runtime",
    "configure_rag_runtime_from_config",
    "get_rag_runtime",
    "get_context_provider",
    "create_agent_context_provider",
    "register_vector_store",
]
