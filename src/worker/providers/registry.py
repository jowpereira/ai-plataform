"""
Registry centralizado de LLM Providers.

Permite registro dinâmico de providers e descoberta automática
baseada no tipo de configuração.
"""

from typing import Any, Dict, List, Optional, Type

from src.worker.interfaces import LLMProvider, ProviderType, Registry


class ProviderRegistry(Registry):
    """
    Registry singleton para provedores de LLM.
    
    Uso:
        ```python
        # Registrar um provider customizado
        ProviderRegistry.register("my-provider", MyCustomProvider())
        
        # Obter provider pelo tipo
        provider = ProviderRegistry.get("azure-openai")
        client = provider.create_client(config)
        
        # Criar cliente diretamente (atalho)
        client = ProviderRegistry.create_client(model_config)
        ```
    """
    
    _instance: Optional["ProviderRegistry"] = None
    _providers: Dict[str, LLMProvider] = {}
    _initialized: bool = False
    
    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ProviderRegistry._initialized:
            self._register_defaults()
            ProviderRegistry._initialized = True
    
    def _register_defaults(self) -> None:
        """Registra providers padrão."""
        # Import tardio para evitar circular imports
        from src.worker.providers.azure import AzureOpenAIProvider
        from src.worker.providers.openai import OpenAIProvider
        
        self._providers[ProviderType.AZURE_OPENAI.value] = AzureOpenAIProvider()
        self._providers[ProviderType.OPENAI.value] = OpenAIProvider()
    
    def register(self, key: str, provider: LLMProvider) -> None:
        """
        Registra um provider.
        
        Args:
            key: Chave de identificação (ex: "azure-openai", "ollama")
            provider: Instância do provider
        """
        self._providers[key] = provider
    
    def get(self, key: str) -> Optional[LLMProvider]:
        """
        Obtém um provider registrado.
        
        Args:
            key: Chave do provider
            
        Returns:
            Provider ou None se não encontrado
        """
        return self._providers.get(key)
    
    def list_keys(self) -> List[str]:
        """Lista todos os providers registrados."""
        return list(self._providers.keys())
    
    def create_client(self, config: Any) -> Any:
        """
        Cria um cliente LLM baseado na configuração.
        
        Este é o método principal de conveniência que:
        1. Identifica o provider correto pelo config.type
        2. Delega a criação do cliente ao provider
        
        Args:
            config: ModelConfig com type e deployment
            
        Returns:
            Cliente de chat (ChatClient do agent_framework)
            
        Raises:
            ValueError: Se o tipo de provider não for suportado
        """
        provider_type = getattr(config, 'type', None)
        if not provider_type:
            raise ValueError("Configuração de modelo deve ter 'type' definido")
        
        provider = self.get(provider_type)
        if not provider:
            available = self.list_keys()
            raise ValueError(
                f"Provider '{provider_type}' não suportado. "
                f"Disponíveis: {available}"
            )
        
        return provider.create_client(config)
    
    @classmethod
    def reset(cls) -> None:
        """
        Reseta o registry (útil para testes).
        
        Remove todos os providers e reinicializa com defaults.
        """
        cls._providers.clear()
        cls._initialized = False
        # Força reinicialização
        cls._instance = None


# Instância global para acesso conveniente
_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """
    Obtém a instância global do registry.
    
    Returns:
        ProviderRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
