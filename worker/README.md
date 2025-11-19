# Generic Worker Module

> Módulo extremamente genérico e eficiente para executar workflows declarativos do Microsoft Agent Framework.

## 🎯 Objetivo

Runtime único capaz de ler um arquivo JSON declarativo e instanciar automaticamente qualquer orquestração suportada (Sequential, Concurrent, Group Chat, Handoff, Magentic).

## 🏗️ Arquitetura

```text
worker/
├── config/              # Pydantic models (type-safe)
│   ├── workspace.py     # WorkspaceConfig, TelemetryConfig, StorageConfig
│   ├── resources.py     # ResourcesConfig, MiddlewareConfig, ToolConfig
│   ├── agents.py        # AgentConfig, MemoryConfig
│   ├── orchestration.py # Union discriminada de configs de orquestração
│   └── observability.py # ObservabilityConfig, LogConfig, MetricsConfig
├── factories/           # Padrão Factory
│   ├── middleware_factory.py  # Instancia middleware com cache
│   ├── resource_factory.py    # Instancia tools, MCP servers
│   ├── agent_factory.py       # Cria agentes com middleware aplicado
│   └── workflow_factory.py    # Constrói workflows via WorkflowBuilder
├── streaming.py         # EventAggregator para UI limpo
├── builders/            # Helpers para padrões de orquestração (futuro)
├── execution/           # Event handlers e executores (futuro)
├── storage/             # Persistência JSON local (futuro)
└── runtime.py           # GenericWorker (orquestrador principal)
```

## ✅ Design Principles (Baseado em Validation Report)

### ❌ O Que NÃO Fazemos (Alucinações Corrigidas)

1. **Não usamos classes `SequentialOrchestration`, etc.** (não existem no Python)
   - ✅ Usamos `WorkflowBuilder` + edges específicas

2. **Não usamos `InProcessRuntime`** (não existe no Python)
   - ✅ Execução direta via `workflow.run()` / `workflow.run_stream()`

3. **Middleware não é de workflow**
   - ✅ Middleware é aplicado **no nível do agente individual** via `AgentFactory`

### ✅ O Que Fazemos Corretamente

- `WorkflowBuilder` + edges (direct, conditional, fan-out, fan-in, switch-case)
- Três tipos de middleware: `FunctionMiddleware`, `AgentMiddleware`, `ChatMiddleware`
- `AgentThread` + `ChatMessageStore` (in-memory, file, Redis)
- Eventos: `ExecutorInvokeEvent`, `ExecutorCompleteEvent`, `WorkflowOutputEvent`, etc.
- Sub-workflows via `WorkflowExecutor`
- Streaming com `workflow.run_stream()`
- Response format via Pydantic models
- **Terminal nodes** explícitos para workflow structure
- **EventAggregator** para UI streaming limpo

## 🚀 Uso Básico

### Modo Non-Streaming

```python
import asyncio
from worker import GenericWorker, WorkerConfig

async def main():
    # Carrega configuração JSON
    config = WorkerConfig.from_json("worker.json")
    
    # Inicializa worker
    worker = GenericWorker(config)
    await worker.initialize()
    
    # Executa workflow (non-streaming)
    results = await worker.run("input message")
    print(results)

asyncio.run(main())
```

### Modo Streaming (UI-Friendly)

```python
from worker import GenericWorker, WorkerConfig
from worker.streaming import EventAggregator, ConsoleStreamRenderer

async def main():
    config = WorkerConfig.from_json("worker.json")
    worker = GenericWorker(config)
    await worker.initialize()
    
    # Agregador com verbosity level
    aggregator = EventAggregator(verbosity="normal")
    
    # Streaming com output limpo
    async for message in aggregator.process_stream(worker.run_stream("input")):
        print(f"[{message.stage}] {message.executor_id}: {message.content}")
    
    # Ou use o renderer formatado
    renderer = ConsoleStreamRenderer()
    async for message in aggregator.process_stream(worker.run_stream("input")):
        renderer.render(message)

asyncio.run(main())
```

## 🎛️ Streaming Verbosity Levels

Configure o EventAggregator com diferentes níveis:

| Level | Eventos Emitidos | Uso |
|-------|------------------|-----|
| `minimal` | Apenas `workflow_output` final | APIs, dashboards |
| `normal` | `executor_start`, `executor_complete`, `workflow_output` | UIs interativas (recomendado) |
| `debug` | Todos os eventos incluindo chunks de tokens | Debugging, logs |

**Exemplo**:

```python
# Para UI limpa (sem token fragmentation)
aggregator = EventAggregator(verbosity="normal")

# Para debugging detalhado
aggregator = EventAggregator(verbosity="debug")
```

## 📝 Configuração JSON

### Terminal Nodes (Importante!)

Sempre declare `terminal_nodes` para evitar warnings e documentar explicitamente o fim do workflow:

```json
{
  "orchestration": {
    "type": "sequential",
    "start": "router",
    "edges": [
      {"kind": "direct", "source": "router", "target": "specialist"},
      {"kind": "direct", "source": "specialist", "target": "synthesizer"}
    ],
    "terminal_nodes": ["synthesizer"]
  }
}
```

**Por quê?**
- ✅ Elimina ambiguidade sobre nós finais
- ✅ Documenta intenção explicitamente
- ✅ Facilita validação e debugging
- ⚠️ Sem ele, você verá: `[WARNING] No outgoing edges found for executor X`

📖 **Leia mais**: [Terminal Nodes FAQ](../docs/terminal-nodes-faq.md) | [Workflow Patterns](../docs/workflow-patterns.md)

### Exemplo Sequential Completo

```json
{
  "workspace": {
    "name": "my-worker",
    "max_iterations": 12,
    "telemetry": {
      "providers": ["console", "file"],
      "level": "info"
    }
  },
  "resources": {
    "global_middleware": [
      {
        "id": "retry_middleware",
        "type": "agent",
        "class_path": "worker.middleware.RetryMiddleware",
        "params": { "max_retries": 3 }
      }
    ],
    "tools": {
      "get_weather": {
        "id": "get_weather",
        "function_path": "mytools.get_weather"
      }
    }
  },
  "agents": {
    "router": {
      "id": "router",
      "name": "Router",
      "client_type": "azure",
      "model": "gpt-4o-mini",
      "instructions": "Route queries.",
      "middleware": []
    },
    "specialist": {
      "id": "specialist",
      "name": "Specialist",
      "client_type": "azure",
      "model": "gpt-4o-mini",
      "instructions": "Handle specialized tasks.",
      "tools": ["get_weather"],
      "middleware": ["caching_middleware"]
    }
  },
  "orchestration": {
    "type": "sequential",
    "start": "router",
    "edges": [
      {
        "kind": "direct",
        "source": "router",
        "target": "specialist"
      },
      {
        "kind": "conditional",
        "source": "specialist",
        "target": "router",
        "condition": "lambda msg: msg.get('needs_retry', False)"
      }
    ]
  },
  "observability": {
    "logging": { "enabled": true, "level": "info" }
  }
}
```

## 🔧 Factories

### MiddlewareFactory

```python
from worker.factories import MiddlewareFactory
from worker.config import MiddlewareConfig

factory = MiddlewareFactory()

config = MiddlewareConfig(
    id="retry",
    type="agent",
    class_path="worker.middleware.RetryMiddleware",
    params={"max_retries": 3}
)

middleware = factory.create_middleware(config)
```

### AgentFactory

```python
from worker.factories import AgentFactory

# IMPORTANTE: Middleware é aplicado no nível do agente
agent = await agent_factory.create_agent(agent_config)
# Agente já tem global_middleware + agent_middleware aplicados
```

### WorkflowFactory

```python
from worker.factories import WorkflowFactory

# Constrói workflow usando WorkflowBuilder (sem classes *Orchestration)
workflow = workflow_factory.create_workflow(orchestration_config)
```

## 📦 Padrões de Orquestração Suportados

| Tipo | Descrição | Config Type |
|------|-----------|-------------|
| **Sequential** | Cadeia de agentes | `SequentialConfig` |
| **Concurrent** | Fan-out/fan-in paralelo | `ConcurrentConfig` |
| **Group Chat** | Manager + speaker selection | `GroupChatConfig` |
| **Handoff** | Transferência dinâmica | `HandoffConfig` |
| **Magentic** | Task ledger + delegation | `MagenticConfig` |

## 🔍 Event Streaming

```python
async for event in worker.run_stream(input_message):
    match event:
        case ExecutorInvokeEvent():
            print(f"▶ Starting {event.executor_id}")
        case ExecutorCompleteEvent():
            print(f"✓ Completed {event.executor_id}")
        case WorkflowOutputEvent():
            print(f"📤 Output: {event.data}")
        case WorkflowCompletedEvent():
            print(f"🏁 Done: {event.data}")
```

## 🎯 Próximos Passos

- [ ] Implementar builders helpers para cada padrão
- [ ] Storage layer (checkpoint, session, audit)
- [ ] Event handlers customizáveis
- [ ] Response format via Pydantic (structured output)
- [ ] Memory management (file, Redis)
- [ ] MCP server connections
- [ ] Human-in-the-loop support
- [ ] Sub-workflows via WorkflowExecutor
- [ ] Telemetry & observability completa

## 📚 Referências

- [Validation Report](../docs/blueprint-validation-report.md) - Análise de alucinações corrigidas
- [Blueprint](../docs/generic-worker-blueprint.md) - Especificação técnica completa
- [Agent Framework Docs](https://learn.microsoft.com/en-us/agent-framework/)
