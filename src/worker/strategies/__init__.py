"""
Workflow Strategies para o Worker SDK.

Implementa o Strategy Pattern para construção de workflows,
permitindo extensibilidade e desacoplamento do engine.

Uso:
    ```python
    from src.worker.strategies import StrategyRegistry
    
    # Obter strategy pelo tipo
    strategy = StrategyRegistry.get("sequential")
    workflow = strategy.build(agents, config, agent_factory)
    
    # Registrar strategy customizada
    StrategyRegistry.register("custom", MyCustomStrategy())
    ```
"""

from src.worker.strategies.registry import StrategyRegistry, get_strategy_registry
from src.worker.strategies.base import BaseWorkflowStrategy
from src.worker.strategies.sequential import SequentialStrategy
from src.worker.strategies.parallel import ParallelStrategy
from src.worker.strategies.group_chat import GroupChatStrategy
from src.worker.strategies.handoff import HandoffStrategy
from src.worker.strategies.router import RouterStrategy

__all__ = [
    "StrategyRegistry",
    "get_strategy_registry",
    "BaseWorkflowStrategy",
    "SequentialStrategy",
    "ParallelStrategy",
    "GroupChatStrategy",
    "HandoffStrategy",
    "RouterStrategy",
]
