"""
Provider para Azure OpenAI Service.

Cria clientes compatíveis com agent_framework para
modelos hospedados no Azure OpenAI.
"""

import os
from typing import Any, List, Optional

from agent_framework.azure import AzureOpenAIChatClient

from src.worker.interfaces import ProviderType
from src.worker.providers.base import BaseLLMProvider


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Provider para Azure OpenAI Service.
    
    Variáveis de Ambiente Esperadas:
        - AZURE_OPENAI_ENDPOINT: URL do recurso Azure OpenAI
        - AZURE_OPENAI_API_KEY: Chave de API (opcional se usar DefaultAzureCredential)
        
    Exemplo de Configuração:
        ```yaml
        resources:
          models:
            gpt-4o:
              type: azure-openai
              deployment: gpt-4o-deployment
        ```
    """
    
    REQUIRED_ENV_VARS = ["AZURE_OPENAI_ENDPOINT"]
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.AZURE_OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """Azure suporta qualquer modelo deployado no recurso."""
        return []
    
    def create_client(self, config: Any) -> AzureOpenAIChatClient:
        """
        Cria um cliente Azure OpenAI.
        
        Args:
            config: ModelConfig com type="azure-openai" e deployment
            
        Returns:
            Instância de AzureOpenAIChatClient
            
        Raises:
            ValueError: Se deployment não estiver definido
            EnvironmentError: Se variáveis de ambiente faltarem
        """
        # Validar configuração
        if not hasattr(config, 'deployment') or not config.deployment:
            raise ValueError(
                "Azure OpenAI requer 'deployment' na configuração do modelo"
            )
        
        # Aplicar variáveis de ambiente específicas do modelo
        env_vars = getattr(config, 'env_vars', None)
        self._apply_env_vars(env_vars)
        
        # Validar variáveis obrigatórias
        missing = self.validate_required_env(self.REQUIRED_ENV_VARS)
        if missing:
            raise EnvironmentError(
                f"Variáveis de ambiente obrigatórias não definidas: {missing}. "
                f"Configure AZURE_OPENAI_ENDPOINT e opcionalmente AZURE_OPENAI_API_KEY."
            )
        
        # Criar cliente
        # AzureOpenAIChatClient busca automaticamente do ambiente:
        # - AZURE_OPENAI_ENDPOINT
        # - AZURE_OPENAI_API_KEY (ou usa DefaultAzureCredential)
        return AzureOpenAIChatClient(deployment_name=config.deployment)
    
    def health_check(self) -> bool:
        """Verifica se as credenciais Azure estão configuradas."""
        missing = self.validate_required_env(self.REQUIRED_ENV_VARS)
        return len(missing) == 0
