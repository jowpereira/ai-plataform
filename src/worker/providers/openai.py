"""
Provider para OpenAI API nativa.

Cria clientes compatíveis com agent_framework para
modelos da API OpenAI direta.
"""

import os
from typing import Any, List

from agent_framework.openai import OpenAIChatClient

from src.worker.interfaces import ProviderType
from src.worker.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    Provider para OpenAI API nativa.
    
    Variáveis de Ambiente Esperadas:
        - OPENAI_API_KEY: Chave de API da OpenAI
        
    Exemplo de Configuração:
        ```yaml
        resources:
          models:
            gpt-4o-mini:
              type: openai
              deployment: gpt-4o-mini
        ```
    """
    
    REQUIRED_ENV_VARS = ["OPENAI_API_KEY"]
    
    # Modelos conhecidos da OpenAI (não exaustivo)
    KNOWN_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """Lista de modelos conhecidos (aceita qualquer um)."""
        return self.KNOWN_MODELS
    
    def create_client(self, config: Any) -> OpenAIChatClient:
        """
        Cria um cliente OpenAI.
        
        Args:
            config: ModelConfig com type="openai" e deployment (model_id)
            
        Returns:
            Instância de OpenAIChatClient
            
        Raises:
            ValueError: Se deployment não estiver definido
            EnvironmentError: Se OPENAI_API_KEY não estiver definida
        """
        # Validar configuração
        deployment = getattr(config, 'deployment', None)
        if not deployment:
            raise ValueError(
                "OpenAI requer 'deployment' (nome do modelo) na configuração"
            )
        
        # Aplicar variáveis de ambiente específicas
        env_vars = getattr(config, 'env_vars', None)
        self._apply_env_vars(env_vars)
        
        # Validar API key
        missing = self.validate_required_env(self.REQUIRED_ENV_VARS)
        if missing:
            raise EnvironmentError(
                f"Variável OPENAI_API_KEY não definida. "
                f"Configure a chave de API da OpenAI."
            )
        
        # Criar cliente
        # OpenAIChatClient busca OPENAI_API_KEY automaticamente
        return OpenAIChatClient(model_id=deployment)
    
    def health_check(self) -> bool:
        """Verifica se a API key está configurada."""
        return bool(os.environ.get("OPENAI_API_KEY"))
