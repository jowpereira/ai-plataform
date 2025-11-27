# Copyright (c) Microsoft. All rights reserved.

"""
Worker - Motor de execução para agentes e workflows.

Componentes principais:
- WorkflowEngine: Orquestrador de workflows multi-agente
- AgentRunner: Executor para agentes standalone
- AgentFactory: Factory para criação de agentes
- ConfigLoader: Carregador de configurações YAML/JSON

Uso básico:
    from src.worker import WorkflowEngine, ConfigLoader
    
    loader = ConfigLoader("config.yaml")
    engine = WorkflowEngine(loader.load())
    result = await engine.run("input")

Para agentes standalone:
    from src.worker import AgentRunner, ConfigLoader
    
    loader = ConfigLoader("agente.json")
    runner = AgentRunner(loader.load_agent())
    result = await runner.run("input")
"""

from src.worker.config import (
    AgentConfig,
    ConfigLoader,
    ModelConfig,
    ResourcesConfig,
    StandaloneAgentConfig,
    ToolConfig,
    WorkerConfig,
    WorkflowConfig,
    WorkflowStep,
)
from src.worker.engine import WorkflowEngine
from src.worker.factory import AgentFactory, ToolFactory
from src.worker.runner import AgentRunner

__all__ = [
    # Engine
    "WorkflowEngine",
    "AgentRunner",
    # Factory
    "AgentFactory",
    "ToolFactory",
    # Config
    "ConfigLoader",
    "WorkerConfig",
    "StandaloneAgentConfig",
    "AgentConfig",
    "ModelConfig",
    "ResourcesConfig",
    "ToolConfig",
    "WorkflowConfig",
    "WorkflowStep",
]