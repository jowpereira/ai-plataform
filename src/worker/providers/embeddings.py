"""
Provider de Embeddings integrado à arquitetura de Providers do Worker SDK.

Segue o mesmo padrão do ProviderRegistry, delegando a criação de clientes
de embeddings aos providers já existentes (Azure OpenAI, OpenAI).
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Sequence

logger = logging.getLogger("worker.providers.embeddings")

# Tipo de vetor para embeddings
Vector = list[float]


class EmbeddingProvider(Protocol):
    """Contrato para provedores de embeddings assíncronos."""

    async def embed_query(self, text: str) -> Vector:
        """Gera embedding para uma consulta livre."""
        ...

    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        """Gera embeddings para múltiplos documentos em lote."""
        ...


class BaseEmbeddingProvider(ABC):
    """
    Classe base para providers de embeddings.
    
    Fornece utilitários comuns (env vars, normalização, retries).
    """
    
    def __init__(
        self,
        *,
        dimensions: int | None = None,
        normalize: bool = True,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ) -> None:
        self._dimensions = dimensions
        self._normalize = normalize
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._env_backup: Dict[str, Optional[str]] = {}
    
    @abstractmethod
    async def embed_query(self, text: str) -> Vector:
        """Gera embedding para uma consulta."""
        ...
    
    @abstractmethod
    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        """Gera embeddings para múltiplos textos."""
        ...
    
    def _apply_env_vars(self, env_vars: Optional[Dict[str, str]]) -> None:
        """Aplica variáveis de ambiente temporárias."""
        if not env_vars:
            return
        for key, value in env_vars.items():
            self._env_backup[key] = os.environ.get(key)
            os.environ[key] = value
    
    def _normalize_vector(self, vector: Sequence[float]) -> Vector:
        """Normaliza vetor se configurado."""
        if self._dimensions and len(vector) != self._dimensions:
            logger.debug(
                "Dimensão do embedding (%s) diferente da esperada (%s)",
                len(vector),
                self._dimensions,
            )
        
        normalized = list(vector)
        if not self._normalize:
            return normalized
        
        norm = math.sqrt(sum(v * v for v in normalized))
        if not norm:
            return normalized
        return [v / norm for v in normalized]


class AzureOpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Provider de embeddings para Azure OpenAI.
    
    Reutiliza as mesmas credenciais e padrões do AzureOpenAIProvider.
    """
    
    def __init__(
        self,
        *,
        deployment: str,
        env_vars: Optional[Dict[str, str]] = None,
        dimensions: int | None = None,
        normalize: bool = True,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            normalize=normalize,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )
        
        if not deployment:
            raise ValueError("Azure OpenAI Embeddings requer 'deployment' definido")
        
        self._apply_env_vars(env_vars)
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise EnvironmentError(
                "AZURE_OPENAI_ENDPOINT não definido. "
                "Configure o recurso Azure OpenAI antes de usar embeddings."
            )
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            logger.warning(
                "AZURE_OPENAI_API_KEY não encontrado. "
                "O cliente tentará usar credenciais AAD configuradas no ambiente."
            )
        
        api_version = (
            os.getenv("AZURE_OPENAI_API_VERSION")
            or os.getenv("OPENAI_API_VERSION")
            or "2024-08-01-preview"
        )
        
        self._deployment = deployment
        
        # Import tardio para evitar dependência circular
        from openai import AsyncAzureOpenAI
        self._client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
    
    async def embed_query(self, text: str) -> Vector:
        if not text or not text.strip():
            raise ValueError("Texto da query não pode ser vazio para geração de embeddings")
        vectors = await self._create_embeddings([text])
        return vectors[0]
    
    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        payload = [t for t in texts if t and t.strip()]
        if not payload:
            return []
        return await self._create_embeddings(payload)
    
    async def _create_embeddings(self, inputs: Sequence[str]) -> list[Vector]:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            RateLimitError,
        )
        
        delay = self._retry_backoff
        last_error: Exception | None = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.embeddings.create(
                    model=self._deployment,
                    input=list(inputs),
                )
                vectors = [
                    self._normalize_vector(item.embedding) 
                    for item in response.data
                ]
                if len(vectors) != len(inputs):
                    logger.warning(
                        "Azure OpenAI retornou %s embeddings para %s entradas",
                        len(vectors),
                        len(inputs),
                    )
                return vectors
                
            except (RateLimitError, APITimeoutError, APIConnectionError, APIStatusError) as exc:
                last_error = exc
                should_retry = self._should_retry(exc)
                logger.warning(
                    "Falha ao gerar embeddings (tentativa %s/%s): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if not should_retry or attempt == self._max_retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
                
            except Exception as exc:
                last_error = exc
                logger.exception("Erro inesperado ao gerar embeddings")
                break
        
        raise RuntimeError("Falha ao gerar embeddings com Azure OpenAI") from last_error
    
    @staticmethod
    def _should_retry(error: Exception) -> bool:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            RateLimitError,
        )
        
        if isinstance(error, (RateLimitError, APITimeoutError, APIConnectionError)):
            return True
        if isinstance(error, APIStatusError):
            return error.status_code in {429, 500, 502, 503, 504}
        return False


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Provider de embeddings para OpenAI nativo.
    
    Usa a mesma lógica do OpenAIProvider para credenciais.
    """
    
    def __init__(
        self,
        *,
        model: str = "text-embedding-3-small",
        env_vars: Optional[Dict[str, str]] = None,
        dimensions: int | None = None,
        normalize: bool = True,
        max_retries: int = 3,
        retry_backoff: float = 0.5,
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            normalize=normalize,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )
        
        self._apply_env_vars(env_vars)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY não definido. "
                "Configure a chave de API do OpenAI antes de usar embeddings."
            )
        
        self._model = model
        
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
    
    async def embed_query(self, text: str) -> Vector:
        if not text or not text.strip():
            raise ValueError("Texto da query não pode ser vazio")
        vectors = await self._create_embeddings([text])
        return vectors[0]
    
    async def embed_documents(self, texts: Sequence[str]) -> list[Vector]:
        payload = [t for t in texts if t and t.strip()]
        if not payload:
            return []
        return await self._create_embeddings(payload)
    
    async def _create_embeddings(self, inputs: Sequence[str]) -> list[Vector]:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            RateLimitError,
        )
        
        delay = self._retry_backoff
        last_error: Exception | None = None
        
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=list(inputs),
                )
                return [
                    self._normalize_vector(item.embedding) 
                    for item in response.data
                ]
                
            except (RateLimitError, APITimeoutError, APIConnectionError, APIStatusError) as exc:
                last_error = exc
                logger.warning(
                    "Falha ao gerar embeddings (tentativa %s/%s): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if attempt == self._max_retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
                
            except Exception as exc:
                last_error = exc
                logger.exception("Erro inesperado ao gerar embeddings")
                break
        
        raise RuntimeError("Falha ao gerar embeddings com OpenAI") from last_error


class EmbeddingRegistry:
    """
    Registry centralizado para providers de embeddings.
    
    Segue o mesmo padrão do ProviderRegistry.
    
    Uso:
        ```python
        from src.worker.config import ModelConfig
        
        # Obter provider baseado em ModelConfig
        provider = EmbeddingRegistry.create_provider(model_config)
        vector = await provider.embed_query("texto")
        ```
    """
    
    _instance: Optional["EmbeddingRegistry"] = None
    
    def __new__(cls) -> "EmbeddingRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def create_provider(
        cls,
        model_config: Any,
        *,
        dimensions: int | None = None,
        normalize: bool = True,
    ) -> EmbeddingProvider:
        """
        Cria um provider de embeddings baseado na configuração do modelo.
        
        Args:
            model_config: ModelConfig com type e deployment
            dimensions: Dimensões esperadas do vetor
            normalize: Se deve normalizar os vetores
            
        Returns:
            EmbeddingProvider configurado
            
        Raises:
            ValueError: Se o tipo de provider não for suportado
        """
        provider_type = getattr(model_config, "type", None)
        deployment = getattr(model_config, "deployment", None)
        env_vars = getattr(model_config, "env_vars", None)
        
        if provider_type == "azure-openai":
            if not deployment:
                raise ValueError(
                    "Azure OpenAI Embeddings requer 'deployment' na configuração do modelo"
                )
            return AzureOpenAIEmbeddingProvider(
                deployment=deployment,
                env_vars=env_vars,
                dimensions=dimensions,
                normalize=normalize,
            )
        
        if provider_type == "openai":
            model = deployment or "text-embedding-3-small"
            return OpenAIEmbeddingProvider(
                model=model,
                env_vars=env_vars,
                dimensions=dimensions,
                normalize=normalize,
            )
        
        raise ValueError(
            f"Provider de embeddings '{provider_type}' não suportado. "
            f"Disponíveis: azure-openai, openai"
        )
    
    @classmethod
    def reset(cls) -> None:
        """Reseta o registry (útil para testes)."""
        cls._instance = None


def get_embedding_registry() -> EmbeddingRegistry:
    """Obtém a instância global do registry de embeddings."""
    return EmbeddingRegistry()
