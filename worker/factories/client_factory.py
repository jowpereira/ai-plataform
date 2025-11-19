"""Client factory para instanciar chat clients de diferentes providers."""

import os
from abc import ABC, abstractmethod
from typing import Any

from agent_framework.openai import OpenAIChatClient


class ClientFactory(ABC):
    """Base factory para criar chat clients."""

    @abstractmethod
    def create_client(self, model_id: str, **kwargs) -> Any:
        """Cria instância de chat client.
        
        Args:
            model_id: ID do modelo
            **kwargs: Parâmetros específicos do provider
            
        Returns:
            Instância de chat client
        """
        pass

    @abstractmethod
    def supports_client_type(self, client_type: str) -> bool:
        """Verifica se factory suporta o tipo de client.
        
        Args:
            client_type: Tipo do client (openai, azure, etc.)
            
        Returns:
            True se suportado
        """
        pass


class OpenAIClientFactory(ClientFactory):
    """Factory para OpenAI clients."""

    def create_client(self, model_id: str, **kwargs) -> OpenAIChatClient:
        """Cria OpenAI client."""
        return OpenAIChatClient(model_id=model_id, **kwargs)

    def supports_client_type(self, client_type: str) -> bool:
        return client_type == "openai"


class AzureOpenAIClientFactory(ClientFactory):
    """Factory para Azure OpenAI clients."""

    def create_client(self, model_id: str, **kwargs) -> OpenAIChatClient:
        """Cria Azure OpenAI client."""
        from openai import AsyncOpenAI
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("OPENAI_API_VERSION", "2024-08-01-preview")
        
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT não definido")
            
        base_url = f"{endpoint.rstrip('/')}/openai/deployments/{model_id}"
        
        azure_client = AsyncOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            base_url=base_url,
            default_query={"api-version": api_version},
            **kwargs
        )
        
        return OpenAIChatClient(
            model_id=model_id,
            async_client=azure_client,
        )

    def supports_client_type(self, client_type: str) -> bool:
        return client_type == "azure"





class ClientFactoryRegistry:
    """Registry para gerenciar client factories."""

    def __init__(self):
        self._factories: list[ClientFactory] = []
        self._register_default_factories()

    def _register_default_factories(self):
        """Registra factories padrão."""
        self.register(OpenAIClientFactory())
        self.register(AzureOpenAIClientFactory())

    def register(self, factory: ClientFactory):
        """Registra nova factory.
        
        Args:
            factory: Factory a ser registrada
        """
        self._factories.append(factory)

    def create_client(self, client_type: str, model_id: str, **kwargs) -> Any:
        """Cria client usando factory apropriada.
        
        Args:
            client_type: Tipo do client
            model_id: ID do modelo
            **kwargs: Parâmetros específicos
            
        Returns:
            Instância de chat client
            
        Raises:
            ValueError: se client_type não for suportado
        """
        for factory in self._factories:
            if factory.supports_client_type(client_type):
                return factory.create_client(model_id, **kwargs)
        
        raise ValueError(f"Client type '{client_type}' não suportado")

    def get_supported_types(self) -> list[str]:
        """Retorna lista de tipos suportados."""
        types = []
        for factory in self._factories:
            for client_type in ["openai", "azure"]:
                if factory.supports_client_type(client_type):
                    types.append(client_type)
        return types