"""
Registry de Workflow Strategies.

Centraliza o registro e descoberta de strategies,
permitindo extensibilidade.
"""

from typing import Any, Dict, List, Optional, Type

from src.worker.interfaces import WorkflowStrategy


class StrategyRegistry:
    """
    Registry singleton para strategies de workflow.
    
    Uso:
        ```python
        # Obter strategy pelo tipo
        strategy = StrategyRegistry.get("sequential")
        workflow = strategy.build(agents, config, factory)
        
        # Registrar strategy customizada
        StrategyRegistry.register("my_custom", MyCustomStrategy())
        
        # Listar disponíveis
        types = StrategyRegistry.list_types()
        ```
    """
    
    _instance: Optional["StrategyRegistry"] = None
    _strategies: Dict[str, WorkflowStrategy] = {}
    _initialized: bool = False
    
    def __new__(cls) -> "StrategyRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not StrategyRegistry._initialized:
            self._register_defaults()
            StrategyRegistry._initialized = True
    
    def _register_defaults(self) -> None:
        """Registra strategies padrão."""
        # Import tardio para evitar circular imports
        from src.worker.strategies.sequential import SequentialStrategy
        from src.worker.strategies.parallel import ParallelStrategy
        from src.worker.strategies.group_chat import GroupChatStrategy
        from src.worker.strategies.handoff import HandoffStrategy
        from src.worker.strategies.router import RouterStrategy
        from src.worker.strategies.magentic import MagenticStrategy
        
        self._strategies["sequential"] = SequentialStrategy()
        self._strategies["parallel"] = ParallelStrategy()
        self._strategies["group_chat"] = GroupChatStrategy()
        self._strategies["handoff"] = HandoffStrategy()
        self._strategies["router"] = RouterStrategy()
        self._strategies["magentic"] = MagenticStrategy()
    
    def register(self, workflow_type: str, strategy: WorkflowStrategy) -> None:
        """
        Registra uma strategy.
        
        Args:
            workflow_type: Tipo de workflow (ex: "sequential", "my_custom")
            strategy: Instância da strategy
        """
        self._strategies[workflow_type] = strategy
    
    def get(self, workflow_type: str) -> Optional[WorkflowStrategy]:
        """
        Obtém uma strategy registrada.
        
        Args:
            workflow_type: Tipo do workflow
            
        Returns:
            Strategy ou None se não encontrada
        """
        return self._strategies.get(workflow_type)
    
    def list_types(self) -> List[str]:
        """Lista todos os tipos de workflow disponíveis."""
        return list(self._strategies.keys())
    
    def has(self, workflow_type: str) -> bool:
        """Verifica se um tipo está registrado."""
        return workflow_type in self._strategies
    
    def build(
        self,
        workflow_type: str,
        agents: List[Any],
        config: Any,
        agent_factory: Any
    ) -> Any:
        """
        Atalho para obter strategy e construir workflow.
        
        Args:
            workflow_type: Tipo do workflow
            agents: Lista de agentes
            config: Configuração do workflow
            agent_factory: Factory de agentes
            
        Returns:
            Workflow construído
            
        Raises:
            ValueError: Se tipo não suportado
        """
        strategy = self.get(workflow_type)
        if not strategy:
            available = self.list_types()
            raise ValueError(
                f"Tipo de workflow '{workflow_type}' não suportado. "
                f"Disponíveis: {available}"
            )
        
        return strategy.build(agents, config, agent_factory)
    
    def validate(self, workflow_type: str, config: Any) -> List[str]:
        """
        Valida configuração para um tipo de workflow.
        
        Args:
            workflow_type: Tipo do workflow
            config: Configuração a validar
            
        Returns:
            Lista de erros (vazia se válido)
        """
        strategy = self.get(workflow_type)
        if not strategy:
            return [f"Tipo de workflow '{workflow_type}' não suportado"]
        
        return strategy.validate(config)
    
    @classmethod
    def reset(cls) -> None:
        """Reseta o registry (útil para testes)."""
        cls._strategies.clear()
        cls._initialized = False
        cls._instance = None


# Instância global
_registry: Optional[StrategyRegistry] = None


def get_strategy_registry() -> StrategyRegistry:
    """
    Obtém a instância global do registry.
    
    Returns:
        StrategyRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry
