"""
Workflow Strategies para o Worker SDK.

Implementa o Strategy Pattern para construção de workflows,
permitindo extensibilidade e desacoplamento do engine.

Padrão Microsoft Agent Framework:
    - @executor: Para funções simples → FunctionExecutor
    - @handler: Para métodos de classe Executor
    - Builders de alto nível: Sequential, Concurrent, GroupChat, Handoff, Magentic
    - Adapters: InputToConversation, ResponseToConversation, EndWithConversation

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
from src.worker.strategies.magentic import MagenticStrategy
from src.worker.strategies.executors import (
    yield_agent_response,
    yield_string_output,
    yield_any_output,
)
from src.worker.strategies.adapters import (
    InputToConversation,
    ResponseToConversation,
    EndWithConversation,
    EndWithText,
    RouterDispatcher,
)

__all__ = [
    # Registry
    "StrategyRegistry",
    "get_strategy_registry",
    # Base
    "BaseWorkflowStrategy",
    # Strategies
    "SequentialStrategy",
    "ParallelStrategy",
    "GroupChatStrategy",
    "HandoffStrategy",
    "RouterStrategy",
    "MagenticStrategy",
    # Executors (@executor functions)
    "yield_agent_response",
    "yield_string_output",
    "yield_any_output",
    # Adapters (Executor classes with @handler)
    "InputToConversation",
    "ResponseToConversation",
    "EndWithConversation",
    "EndWithText",
    "RouterDispatcher",
]
