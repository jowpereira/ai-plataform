# Roadmap de Desenvolvimento - Worker Genérico AI Platform

Este documento rastrea o progresso detalhado do desenvolvimento do módulo worker genérico.

## Fase 1: Fundamentos e Estrutura (MVP)
- [x] **Setup Inicial**
    - [x] Criar estrutura de diretórios `src/worker`.
    - [x] Criar `CHANGELOG.md` para registro de marcos.
- [x] **Modelagem de Configuração (`src/worker/config.py`)**
    - [x] Definir modelo `ToolConfig` (id, path).
    - [x] Definir modelo `ModelConfig` (type, deployment, env vars).
    - [x] Definir modelo `AgentConfig` (role, instructions, tools, model).
    - [x] Definir modelo `WorkflowStep` (id, agent, input_template, next).
    - [x] Definir modelo `WorkerConfig` (root).
    - [x] Implementar `ConfigLoader` com suporte a resolução de variáveis de ambiente (`${VAR}`).
- [x] **Fábrica de Componentes (`src/worker/factory.py`)**
    - [x] Implementar `ToolFactory` para importação dinâmica (`importlib`).
    - [x] Implementar `AgentFactory` para instanciar `ChatAgent` do framework.
    - [x] Implementar suporte a `OpenAIChatClient` e `AzureOpenAIChatClient`.
- [x] **Motor de Execução (`src/worker/engine.py`)**
    - [x] Criar classe `WorkflowEngine`.
    - [x] Implementar construção de workflow sequencial básico.
    - [x] Implementar método `run`.
- [x] **Refatoração e Teste**
    - [x] Migrar `scripts/worker_test/config/worker.json` para o novo schema.
    - [x] Atualizar `scripts/worker_test/run_worker.py` para usar o novo módulo `src.worker`.
    - [x] Validar execução ponta a ponta (Hello World).

## Fase 2: Workflows Avançados
- [x] **Suporte a Paralelismo**
    - [x] Adicionar tipo `parallel` no schema de workflow.
    - [x] Implementar construção de branches paralelos no `WorkflowEngine`.
- [x] **Roteamento Dinâmico**
    - [x] Adicionar tipo `router` no schema.
    - [x] Implementar lógica de decisão baseada em output de agente.
- [x] **Group Chat e Colaboração**
    - [x] Adicionar tipo `group_chat` no schema.
    - [x] Implementar `GroupChatBuilder` com gerenciador automático.
- [x] **Handoff (Transição de Agentes)**
    - [x] Adicionar tipo `handoff` no schema.
    - [x] Implementar transições explícitas.

## Fase 3: Human-in-the-loop e Persistência
- [x] **Interação Humana**
    - [x] Adicionar step type `human_approval`.
    - [x] Implementar mecanismo de callback para input externo.
- [ ] **Persistência**
    - [ ] Integrar mecanismo de checkpoint do framework (se disponível) ou customizado.

## Fase 4: Robustez e Observabilidade
- [ ] **Tracing**
    - [ ] Integrar OpenTelemetry.
- [ ] **Error Handling**
    - [ ] Implementar retry policies configuráveis.

## Fase 5: Evolução Backend (DAG & RAG)
- [x] **Schema Update**
    - [x] Adicionar `NodeConfig` e `EdgeConfig` em `src/worker/config.py`.
    - [x] Suportar tipo `dag` no `WorkflowConfig`.
- [x] **Novos Tipos de Nós**
    - [x] Implementar `LogicAgent` (Condition, Router).
    - [x] Implementar `ToolAgent` (Execução de ferramentas nativas).
- [x] **RAG & Data Strategy**
    - [x] Criar módulo `src/worker/rag` (Loader, Splitter, Store).
    - [x] Expor ferramentas RAG em `tools/rag_tools.py`.
- [x] **Tool Discovery**
    - [x] Implementar `src/worker/discovery.py` para escanear ferramentas.

## Fase 5: Interface e Ferramentas de Desenvolvimento

- [x] **Integração MAIA (DevUI)**
  - [x] Clonar e integrar código base do `agent_framework_devui`.
  - [x] Configurar build do frontend (Vite + React).
  - [x] Integrar servidor FastAPI ao `run.py`.
  - [x] Rebranding completo para "MAIA".
  - [x] Landing Page v2 (Foco em "Internal Builder" e Casos de Uso Operacionais).
  - [x] Carregamento automático de exemplos do diretório `exemplos/`.
  - [x] Renomear módulo `src.devui` para `src.maia_ui`.

## Fase 6: Análise Forense e Refatoração (Alinhamento Upstream)
- [x] **Análise Backend**
    - [x] Comparar `src/maia_ui` com `agent_framework_devui`.
    - [x] Verificar endpoints e mapeadores.
- [x] **Refatoração Worker**
    - [x] Eliminar redundância em `src/worker/engine.py` (usar `FunctionExecutor`).
    - [x] Remover `src/worker/nodes.py`.
    - [x] Validar uso de `WorkflowBuilder` nativo.
    - [x] Delegar workflows de alto nível (`sequential`, `parallel`, `group_chat`, `handoff`, `router`) para os builders oficiais do framework.
- [x] **Validação Frontend**
    - [x] Testar conectividade real com backend.
    - [x] Verificar listagem de entidades.
    - [x] Implementar gerenciamento CRUD de workflows.
    - [x] Criar página de listagem de workflows (`WorkflowListPage`).
    - [x] Integrar edição de workflows via Studio.

## Fase 5: Atualização Framework v1.0 (Commit 907d79a)
- [x] **Atualização de Dependências**
    - [x] Fixar versão `agent-framework-core==1.0.0b251120`.
    - [x] Resolver conflitos de dependências (`uv sync`).
- [x] **Refatoração do Engine**
    - [x] Group Chat: Suporte híbrido (`set_manager` / `set_prompt_based_manager`).
    - [x] Handoff: Implementar `auto_register_handoff_tools`.
    - [x] Router: Ajustar parsing de output (`list[ChatMessage]`).
- [ ] **Compatibilidade Declarativa**
    - [ ] Mapear schema declarativo sem dependências .NET.
- [x] **Qualidade**
    - [x] Criar testes de regressão para refatorações.

---

## Fase 7: Worker Genérico (v0.8.X → v0.9.0)

> **Objetivo**: Transformar o `worker` em um SDK 100% genérico, desacoplado e extensível.
> **Decisões Arquiteturais**:
> - ✅ Usar Pydantic estritamente para validar templates de prompt
> - ❌ Não criar stubs para `agent_framework` (testes usam o pacote real)

### 7.1 Contratos e Interfaces (ABCs)
- [x] **Criar `src/worker/interfaces.py`**
    - [x] `LLMProvider(ABC)`: Contrato para provedores de modelo (OpenAI, Azure, Ollama, etc.)
    - [x] `ToolAdapter(ABC)`: Contrato para ferramentas (local, HTTP, MCP)
    - [x] `WorkflowStrategy(ABC)`: Strategy para builders de workflow
    - [x] `EventBus(ABC)`: Sistema de eventos para hooks/observabilidade
    - [x] `MemoryStore(ABC)`: Interface stub para futura integração de memória

### 7.2 Camada de Providers LLM
- [x] **Criar `src/worker/providers/`**
    - [x] `__init__.py`: Registro de providers
    - [x] `base.py`: Implementação base do `LLMProvider`
    - [x] `openai.py`: Provider para OpenAI nativo
    - [x] `azure.py`: Provider para Azure OpenAI
    - [x] `registry.py`: `ProviderRegistry` para descoberta automática
- [x] **Refatorar `factory.py`**
    - [x] Remover instanciação direta de clients
    - [x] Usar `ProviderRegistry.get(type).create_client(config)`

### 7.3 ~~Camada de Mensagens & Prompts~~ (REMOVIDO)
> **Nota (27/11/2025):** Esta camada foi **removida** durante auditoria de código.
> O `agent_framework` nativo já fornece `ChatMessage`, `Role` e `TextContent` em `_types.py`.
> A implementação customizada era 100% redundante e nunca foi integrada ao projeto.
> Ver: `docs/RELATORIO_AUDITORIA_CODIGO.md`

### 7.4 Sistema de Ferramentas Extensível
- [x] **Criar `src/worker/tools/`**
    - [x] `__init__.py`: Exports
    - [x] `models.py`: `ToolDefinition`, `ToolParameter`, `ToolResult`, `RetryPolicy`
    - [x] `base.py`: `ToolAdapter(ABC)`, `AdapterRegistry`
    - [x] `registry.py`: `ToolRegistry` centralizado
    - [x] `adapters/local.py`: Ferramentas locais (Python functions)
    - [x] `adapters/http.py`: Ferramentas HTTP/REST (aiohttp/httpx)
    - [x] `adapters/mcp.py`: Ferramentas MCP (Model Context Protocol)
- [x] **Refatorar `ToolFactory`**
    - [x] Delegar para `ToolRegistry` (com fallback legacy)
    - [x] Método `register_from_config()` para conversão automática

### 7.5 Workflow Strategies
- [x] **Criar `src/worker/strategies/`**
    - [x] `__init__.py`: Exports
    - [x] `base.py`: `WorkflowStrategy` base
    - [x] `sequential.py`: Estratégia sequencial
    - [x] `parallel.py`: Estratégia paralela
    - [x] `group_chat.py`: Estratégia Group Chat
    - [x] `handoff.py`: Estratégia Handoff
    - [x] `router.py`: Estratégia Router
    - [x] `registry.py`: `StrategyRegistry`
    - [x] `magentic.py`: Estratégia Magentic One (AI-driven orchestration)
- [x] **Refatorar `engine.py`**
    - [x] Remover if/elif gigante (~150 linhas removidas)
    - [x] Usar `StrategyRegistry.get(type).build(agents, config)`

### 7.10 Análise e Alinhamento com Framework (ANALISE_FRAMEWORK.md)
> **Objetivo**: Pesquisa profunda do código-fonte do Microsoft Agent Framework para identificar redundâncias e maximizar uso de recursos nativos.

- [x] **Análise de Código-Fonte**
    - [x] Explorar `.agent_framework_comparison/python/packages/core/`
    - [x] Documentar padrões: `@executor`, `@handler`, `@ai_function`
    - [x] Identificar eventos nativos do workflow stream
    - [x] Criar documento `docs/ANALISE_FRAMEWORK.md`

- [x] **Refatoração RouterStrategy**
    - [x] Criar `executors.py` com `yield_agent_response` usando `@executor`
    - [x] Remover classe `OutputExecutor` em favor de função decorada
    - [x] Adicionar edges de agentes para executor terminal

- [x] **Conversão de Ferramentas para `@ai_function`**
    - [x] Atualizar `ferramentas/basicas.py` com `@ai_function` decorator
    - [x] Atualizar `mock_tools/basic.py` com `@ai_function` decorator
    - [x] Atualizar `ToolFactory` para detectar `AIFunction`
    - [x] Criar wrapper de observabilidade para manter eventos `TOOL_CALL_*`

- [x] **Explorar MagenticBuilder**
    - [x] Analisar `_magentic.py` do framework
    - [x] Criar `MagenticStrategy` em `src/worker/strategies/magentic.py`
    - [x] Criar exemplo `exemplos/workflows/magentic_research.json`
    - [x] Registrar no `StrategyRegistry`

- [x] **Correções de Qualidade**
    - [x] Remover truncamento de saída `[:500]` em `engine.py` e `console.py`
    - [x] Corrigir logging de ferramentas `@ai_function` (wrapper com EventBus)

### 7.12 Alinhamento Total com Framework (v0.15.0)
> **Objetivo**: Garantir 100% de conformidade com os padrões oficiais do Microsoft Agent Framework.

- [x] **Análise Exaustiva do Código-Fonte**
    - [x] Estudar `_executor.py`, `_function_executor.py`
    - [x] Estudar `_sequential.py`, `_group_chat.py`, `_handoff.py`
    - [x] Estudar `_magentic.py`, `_concurrent.py`
    - [x] Criar relatório `docs/relatorio_analise_orquestradores.md`

- [x] **Criar Módulo de Adapters**
    - [x] `adapters.py`: `InputToConversation`, `ResponseToConversation`, `EndWithText`
    - [x] Usar `@handler` decorator (padrão oficial)
    - [x] Exportar em `__init__.py`

- [x] **Corrigir RouterStrategy**
    - [x] Trocar `add_executor` (privado) por `add_edge`
    - [x] Manter padrão `Case`/`Default`

- [x] **Corrigir HandoffStrategy**
    - [x] `HandoffBuilder(participants=[...])` no construtor
    - [x] Usar `set_coordinator(name)` corretamente
    - [x] Usar `add_handoff(source, targets)` para transferências

- [x] **Corrigir GroupChatStrategy**
    - [x] Melhorar passagem de descrições
    - [x] Alinhar com padrão `participants(**kwargs)`

- [x] **Validação de Workflows**
    - [x] `sequencial_agent.json` - Pipeline OK
    - [x] `classificador_router.json` - Roteamento OK
    - [x] `comite_risco_groupchat.json` - Group chat OK
    - [x] `atendimento_handoff.json` - Handoff OK
    - [x] `email_triage_parallel.json` - Paralelo OK
    - [x] `magentic_research.json` - Magentic OK

### 7.6 Hooks & Observabilidade
- [x] **Criar `src/worker/events.py`**
    - [x] `WorkerEvent`: Enum de eventos (PROMPT_START, PROMPT_END, TOOL_CALL, etc.)
    - [x] `SimpleEventBus`: Implementação básica do `EventBus`
    - [x] Hooks: `on_prompt`, `on_tool_call`, `on_agent_response`
- [x] **Integrar ao Engine**
    - [x] Emitir eventos em pontos críticos (Engine, Factory, Tools)
    - [x] Middleware para interceptação de Agentes
- [x] **Visualização (CLI)**
    - [x] `ConsoleReporter` com `rich` para logs estruturados

### 7.7 Lifecycle Completo
- [x] **Atualizar `WorkflowEngine`**
    - [x] Método `setup()`: Inicialização e validação
    - [x] Método `run()`: Execução (já existe)
    - [x] Método `teardown()`: Limpeza de recursos
- [ ] **Adicionar Validação Semântica**
    - [ ] Verificar se todos os `handoff_target` existem
    - [ ] Detectar loops infinitos em rotas

### 7.8 Documentação & Testes
- [ ] **Documentação**
    - [ ] `docs/worker-sdk.md`: Guia de uso do SDK genérico
    - [ ] `docs/extending-providers.md`: Como adicionar novos providers
- [ ] **Testes de Integração**
    - [ ] `tests/test_providers.py`
    - [ ] `tests/test_strategies.py`

### 7.9 Padrões de Design Avançados (Inspirado em AG-UI)
> **Objetivo**: Aumentar a robustez do worker adotando padrões de higiene de mensagens, estratégias de confirmação e gestão de estado centralizada, baseados na arquitetura do `agent-framework-ag-ui`.

- [x] **Higiene de Mensagens (Message Hygiene)**
    - [x] **Análise e Estrutura**
        - [x] Estudar `_message_hygiene.py` do AG-UI para entender regras de sanitização.
        - [x] Criar módulo `src/worker/middleware/hygiene.py`.
    - [x] **Implementação do Middleware**
        - [x] Criar classe `MessageSanitizerMiddleware` herdando de `AgentMiddleware`.
        - [x] Implementar lógica para garantir paridade `FunctionCall` <-> `FunctionResult`.
        - [x] Implementar injeção de resultados sintéticos para chamadas de ferramenta órfãs.
        - [x] Implementar reordenação de mensagens (System -> User -> Assistant -> Tool).
    - [x] **Integração**
        - [x] Registrar middleware globalmente no `AgentFactory` (`src/worker/factory.py`).
        - [ ] Criar testes unitários com cenários de histórico corrompido.

- [x] **Estratégias de Confirmação (Human-in-the-loop)**
    - [x] **Definição de Contrato**
        - [x] Criar módulo `src/worker/strategies/confirmation.py`.
        - [x] Definir interface abstrata `ConfirmationStrategy` (métodos: `request_approval`, `on_approved`, `on_rejected`).
    - [x] **Implementação de Estratégias**
        - [x] Implementar `CLIConfirmationStrategy`: Comportamento atual (print/input).
        - [x] Implementar `StructuredConfirmationStrategy`: Retorna objetos JSON para consumo via API/DevUI.
    - [x] **Refatoração do HumanAgent**
        - [x] Atualizar `HumanAgent` em `src/worker/agents.py` para receber `ConfirmationStrategy`.
        - [x] Remover lógica de `input()` hardcoded e delegar para a estratégia.
    - [x] **Configuração**
        - [x] Atualizar `AgentConfig` em `src/worker/config.py` para suportar campo `confirmation_mode`.

- [x] **Gestão de Estado Centralizada (State Management)**
    - [x] **Core do State Manager**
        - [x] Criar módulo `src/worker/state.py`.
        - [x] Implementar classe `WorkflowStateManager`.
        - [x] Definir propriedades: `current_step_id`, `global_context`, `execution_history`.
    - [ ] **Validação e Schema**
        - [ ] Implementar validação de schema para variáveis de contexto (inspirado em `_state_manager.py`).
        - [ ] Adicionar suporte a snapshots de estado.
    - [x] **Integração com Engine**
        - [x] Instanciar `WorkflowStateManager` no `WorkflowEngine`.
        - [ ] Passar gerenciador via `WorkflowContext` para acesso pelos agentes.
