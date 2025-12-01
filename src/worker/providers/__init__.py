"""
Providers de LLM e Embeddings para o Worker SDK.

Este módulo expõe:
- ProviderRegistry: Registro centralizado de providers LLM
- AzureOpenAIProvider: Provider para Azure OpenAI
- OpenAIProvider: Provider para OpenAI nativo
- EmbeddingRegistry: Registro centralizado de providers de embeddings
- AzureOpenAIEmbeddingProvider: Provider de embeddings para Azure OpenAI
- OpenAIEmbeddingProvider: Provider de embeddings para OpenAI nativo
"""

from src.worker.providers.registry import ProviderRegistry
from src.worker.providers.azure import AzureOpenAIProvider
from src.worker.providers.openai import OpenAIProvider
from src.worker.providers.base import BaseLLMProvider
from src.worker.providers.embeddings import (
    EmbeddingRegistry,
    EmbeddingProvider,
    BaseEmbeddingProvider,
    AzureOpenAIEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_registry,
)

__all__ = [
    # LLM Providers
    "ProviderRegistry",
    "AzureOpenAIProvider", 
    "OpenAIProvider",
    "BaseLLMProvider",
    # Embedding Providers
    "EmbeddingRegistry",
    "EmbeddingProvider",
    "BaseEmbeddingProvider",
    "AzureOpenAIEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "get_embedding_registry",
]
