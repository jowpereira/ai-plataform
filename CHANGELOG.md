# Changelog

Todos os marcos notáveis deste projeto serão documentados neste arquivo.

## [0.15.0] - 2025-11-27

### Worker SDK - Alinhamento Total com Microsoft Agent Framework (Fase 7.12)

> **Objetivo**: Garantir 100% de conformidade com os padrões oficiais do Microsoft Agent Framework após análise exaustiva do código-fonte.

#### Adicionado
- **Módulo de Adapters (`src/worker/strategies/adapters.py`)**:
  - `InputToConversation`: Executor para normalizar input em mensagem de conversa.
  - `ResponseToConversation`: Executor para converter AgentResponse em conversa.
  - `EndWithText`: Executor terminal que extrai texto da resposta.
  - Seguem padrão oficial do framework com `@handler` decorator.

- **Relatório de Análise (`docs/relatorio_analise_orquestradores.md`)**:
  - Análise completa de todos os builders do framework.
  - Comparação linha-a-linha com nossa implementação.
  - Conformidade atualizada para 100% em todas as strategies.

#### Corrigido
- **RouterStrategy (`src/worker/strategies/router.py`)**:
  - Corrigido uso de `add_executor` (método privado) para `add_edge`.
  - WorkflowBuilder agora usa API pública corretamente.
  - Padrão `Case`/`Default` implementado conforme framework.

- **HandoffStrategy (`src/worker/strategies/handoff.py`)**:
  - Refatorado para usar API correta do HandoffBuilder.
  - `participants` agora passado no construtor.
  - Método `set_coordinator(name)` usado corretamente.
  - `add_handoff(source, targets)` para definir transferências.

- **GroupChatStrategy (`src/worker/strategies/group_chat.py`)**:
  - Melhorada passagem de descrições dos participantes.
  - Alinhado com padrão `participants(**kwargs)`.

#### Testado
- ✅ `sequencial_agent.json` - Pipeline sequencial funcionando.
- ✅ `classificador_router.json` - Roteamento por classificação funcionando.
- ✅ `comite_risco_groupchat.json` - Conversa em grupo com 4 agentes.
- ✅ `atendimento_handoff.json` - Handoff triagem→suporte funcionando.
- ✅ `email_triage_parallel.json` - Execução paralela de 3 agentes.
- ✅ `magentic_research.json` - Orquestração AI-driven funcionando.

#### Impacto
- **Conformidade**: Todas as 6 strategies agora 100% alinhadas ao framework.
- **Manutenibilidade**: Código mais limpo seguindo padrões oficiais.
- **Estabilidade**: Testes validaram todos os workflows principais.

---

## [0.14.0] - 2025-11-27

### Worker SDK - Maximização do Framework Microsoft (Fase 7.11)

> **Objetivo**: Utilizar ao máximo os recursos nativos do framework, eliminando código redundante e adicionando novas capacidades.

#### Adicionado
- **MagenticStrategy (`src/worker/strategies/magentic.py`)**:
  - Nova strategy para orquestração AI-driven avançada.
  - Planejamento dinâmico via Task Ledger.
  - Replanning adaptativo quando encontra obstáculos.
  - Suporte a revisão humana do plano (`enable_plan_review`).
  - Checkpointing para persistência de estado.

- **Exemplo Magentic (`exemplos/workflows/magentic_research.json`)**:
  - Workflow de equipe de pesquisa (Researcher, Analyst, Writer).
  - Demonstra orquestração inteligente com GPT-4o como manager.

- **Ferramentas com `@ai_function`**:
  - `ferramentas/basicas.py`: Todas as ferramentas agora usam `@ai_function`.
  - `mock_tools/basic.py`: Migrado para decorador nativo do framework.
  - Schema JSON gerado automaticamente pelo framework.
  - Validação Pydantic nativa.

#### Alterado
- **ToolFactory (`src/worker/factory.py`)**:
  - Detecta `AIFunction` e cria wrapper com observabilidade.
  - Mantém emissão de eventos `TOOL_CALL_START`, `TOOL_CALL_COMPLETE`, `TOOL_CALL_ERROR`.
  - Log informativo quando usa ferramenta nativa.

- **StrategyRegistry (`src/worker/strategies/registry.py`)**:
  - Registra `MagenticStrategy` como tipo "magentic".
  - Total de 6 strategies disponíveis.

#### Corrigido
- **Truncamento de Saída Removido**:
  - `src/worker/engine.py`: Removidos 3 truncamentos `[:500]` no resultado final.
  - `src/worker/reporters/console.py`: Removidos truncamentos de ferramentas e workflow.
  - Saída completa agora exibida sem cortes.

- **Observabilidade de Ferramentas `@ai_function`**:
  - Ferramentas convertidas para `@ai_function` agora emitem eventos corretamente.
  - Wrapper criado para manter logging e eventos do EventBus.

#### Impacto
- **Alinhamento**: Padrão `@ai_function` oficial do Microsoft Agent Framework.
- **Novidade**: Orquestração Magentic One agora disponível.
- **Observabilidade**: Ferramentas nativas mantêm logging visual.

## [0.13.0] - 2025-11-27

### Worker SDK - Alinhamento com Microsoft Agent Framework (Fase 7.10)

> **Análise Profunda**: Pesquisa exaustiva do código-fonte do framework para identificar redundâncias e oportunidades de simplificação.

#### Adicionado
- **Documento de Análise (`docs/ANALISE_FRAMEWORK.md`)**:
  - Comparação completa entre nossa implementação e o framework Microsoft.
  - Identificação de recursos subutilizados (MagenticBuilder, @executor decorator).
  - Recomendações de refatoração priorizadas.

- **Executors Funcionais (`src/worker/strategies/executors.py`)**:
  - `yield_agent_response`: Executor terminal usando `@executor` decorator (padrão oficial).
  - `yield_string_output`: Executor para strings diretas.
  - `yield_any_output`: Executor genérico para qualquer tipo de dados.
  - Alinhamento total com padrões do framework Microsoft.

- **Observabilidade de Agentes Standalone**:
  - Eventos `AGENT_RUN_START` e `AGENT_RUN_COMPLETE` em `WorkerEventType`.
  - `AgentRunner` agora emite eventos de ciclo de vida consistentes.
  - Visual de execução estilo CrewAI com painéis rich.

#### Alterado
- **RouterStrategy (`src/worker/strategies/router.py`)**:
  - Refatorado para usar `yield_agent_response` (decorator `@executor`).
  - Removida classe `OutputExecutor` em favor de função decorada.
  - Código mais conciso e alinhado com exemplos oficiais do framework.

- **ConsoleReporter (`src/worker/reporters/console.py`)**:
  - Handlers para novos eventos de agente standalone.
  - Saída visual unificada para agentes e workflows.

- **Engine (`src/worker/engine.py`)**:
  - Captura de última resposta via EventBus como fallback.
  - Melhor tratamento de outputs de workflows com edges sem saída.

#### Descobertas da Análise
- **Uso Correto**: SequentialBuilder, ConcurrentBuilder, GroupChatBuilder, HandoffBuilder.
- **Subutilizado**: MagenticBuilder para orquestração AI-driven avançada.
- **Redundante**: EventMiddleware (framework tem eventos nativos).
- **Oportunidade**: Converter ferramentas locais para `@ai_function`.

## [0.12.0] - 2025-11-27

### Worker SDK - Robustez e Padrões Avançados (Fase 7.7 e 7.9)

> **Marco Atingido**: O Worker agora é um SDK genérico, desacoplado e extensível, cumprindo os objetivos da Fase 7.

#### Adicionado
- **Gestão de Estado (`src/worker/state.py`)**:
  - `WorkflowStateManager`: Gerenciador centralizado de estado da execução.
  - Suporte a contexto global, histórico de execução e snapshots.
  - Integração com `WorkflowEngine` para ciclo de vida (`setup`, `teardown`).

- **Higiene de Mensagens (`src/worker/middleware/hygiene.py`)**:
  - `MessageSanitizerMiddleware`: Middleware para sanitização de histórico de mensagens.
  - Previne erros de API garantindo integridade da lista de mensagens antes do envio ao modelo.
  - Registrado globalmente no `AgentFactory`.

- **Estratégias de Confirmação (`src/worker/strategies/confirmation.py`)**:
  - `ConfirmationStrategy`: Interface para desacoplar interação humana.
  - `CLIConfirmationStrategy`: Interação via terminal (padrão).
  - `StructuredConfirmationStrategy`: Retorno estruturado (JSON) para integração com API/DevUI.
  - `AutoApprovalStrategy`: Aprovação automática para testes.

#### Alterado
- **Engine (`src/worker/engine.py`)**:
  - Implementado ciclo de vida completo (`setup`, `run`, `teardown`).
  - Integração com `WorkflowStateManager` para rastreamento de status (`initialized`, `running`, `completed`, `failed`).
  - Detecção automática de modo de confirmação para `HumanAgent` baseado em ambiente (`DEVUI_MODE`).

- **Agentes (`src/worker/agents.py`)**:
  - `HumanAgent` refatorado para usar `ConfirmationStrategy`.
  - Removida dependência direta de `input()` e `print()`.

- **Configuração (`src/worker/config.py`)**:
  - Adicionado campo `confirmation_mode` em `AgentConfig`.

## [0.11.0] - 2025-11-26

### Worker SDK - Observabilidade e CLI (Fase 7.6)

#### Adicionado
- **Sistema de Eventos (`src/worker/events.py`)**:
  - `get_event_bus()`: Singleton para acesso global ao barramento de eventos.
  - `emit_simple()`: Helper para emissão simplificada de eventos.
  - Novos tipos de eventos: `TOOL_CALL_START`, `TOOL_CALL_COMPLETE`, `TOOL_CALL_ERROR`.

- **Middleware (`src/worker/middleware.py`)**:
  - `EventMiddleware`: Middleware para interceptar execução de agentes e emitir eventos de ciclo de vida.

- **Reporter (`src/worker/reporters/console.py`)**:
  - `ConsoleReporter`: Visualização rica no terminal usando a biblioteca `rich`.
  - Exibição estruturada de:
    - Ciclo de vida do Workflow.
    - Ativação de Agentes.
    - Chamadas de Ferramentas (Args e Resultados).
    - Respostas de Agentes (Markdown renderizado).

#### Alterado
- **Factory (`src/worker/factory.py`)**:
  - Injeção automática de `EventMiddleware` na criação de agentes.
  - Wrapper de ferramentas legacy agora emite eventos de execução.

- **Tools (`src/worker/tools/base.py`)**:
  - `get_callable()` instrumentado para emitir eventos de execução de ferramentas.

- **CLI (`run.py`)**:
  - Integração com `ConsoleReporter` para feedback visual detalhado.
  - Removidos prints de debug redundantes para saída limpa.

## [0.10.0] - 2025-11-26

### Worker SDK - Sistema de Ferramentas e Strategies (Fase 7.4 e 7.5)

#### Adicionado
- **Sistema de Ferramentas (`src/worker/tools/`)**:
  - `ToolDefinition`: Modelo Pydantic completo com suporte a parâmetros, retry policy, e metadados.
  - `ToolParameter`: Definição tipada de parâmetros com conversão para JSON Schema.
  - `ToolResult`: Resultado padronizado com métricas de execução.
  - `RetryPolicy`: Política de retry com backoff exponencial configurável.
  - `ToolExecutionContext`: Contexto de execução com headers, auth, e tracing.

- **Adapters de Ferramentas (`src/worker/tools/adapters/`)**:
  - `LocalToolAdapter`: Execução de funções Python locais via importlib, com suporte a funções async.
  - `HttpToolAdapter`: Chamadas HTTP/REST com suporte a aiohttp/httpx, autenticação, e JSONPath.
  - `McpToolAdapter`: Integração com Model Context Protocol (MCP) servers.
  - `AdapterRegistry`: Registry para descoberta de adapters por tipo.

- **Registry de Ferramentas (`src/worker/tools/registry.py`)**:
  - `ToolRegistry`: Registry singleton com validação automática via adapter.
  - Métodos `register()`, `get_callable()`, `execute()`, `to_openai_functions()`.
  - Funções de conveniência: `get_tool_registry()`, `register_tool()`, `execute_tool()`.

- **Workflow Strategies (`src/worker/strategies/`)**:
  - `SequentialStrategy`: Workflow linear com encadeamento de steps.
  - `ParallelStrategy`: Execução paralela com merge de resultados.
  - `GroupChatStrategy`: Orquestração de agentes em chat colaborativo.
  - `HandoffStrategy`: Transferência de contexto entre agentes.
  - `RouterStrategy`: Roteamento dinâmico baseado em output.
  - `StrategyRegistry`: Registry com auto-descoberta de strategies.

#### Alterado
- **Factory (`src/worker/factory.py`)**:
  - `ToolFactory` refatorado para usar `ToolRegistry` com fallback legacy.
  - Novo método `register_from_config()` para conversão automática de ToolConfig.
  - Logging via `logging` module (substituindo prints).

- **Engine (`src/worker/engine.py`)**:
  - Refatorado para usar `StrategyRegistry` em vez de if/elif monolítico.
  - Removidas ~150 linhas de código duplicado.
  - Integração com `SimpleEventBus` para emissão de eventos.

## [0.9.0] - 2025-11-26

### Worker SDK - Arquitetura Genérica (Fase 7)

#### Adicionado
- **Interfaces e Contratos (`src/worker/interfaces.py`)**:
  - `LLMProvider(ABC)`: Contrato para provedores de modelo (OpenAI, Azure, Ollama).
  - `ToolAdapter(ABC)`: Contrato para ferramentas (local, HTTP, MCP).
  - `WorkflowStrategy(ABC)`: Strategy para builders de workflow.
  - `EventBus(ABC)`: Sistema de eventos para observabilidade.
  - `MemoryStore(ABC)`: Interface stub para persistência de contexto.
  - `WorkerEventType`: Enum com 16 tipos de eventos (lifecycle, prompt, LLM, tools, workflow, agent).

- **Camada de Providers (`src/worker/providers/`)**:
  - `BaseLLMProvider`: Classe base com utilitários para env vars.
  - `AzureOpenAIProvider`: Provider para Azure OpenAI Service.
  - `OpenAIProvider`: Provider para API OpenAI nativa.
  - `ProviderRegistry`: Registry singleton com auto-descoberta de providers.

- **Camada de Prompts (`src/worker/prompts/`)**:
  - `PromptTemplate`: Templates com variáveis dinâmicas e validação Pydantic.
  - `PromptVariable`: Definição tipada de variáveis.
  - `PromptChain`: Composição de templates em pipeline.
  - `MessageBuilder`: API fluente para construção de mensagens.
  - `ConversationalContext`: Gerenciamento de histórico e variáveis de sessão.
  - `PromptEngine`: Orquestrador de renderização.

- **Sistema de Eventos (`src/worker/events.py`)**:
  - `SimpleEventBus`: Implementação síncrona do EventBus.
  - Handlers pré-definidos: `create_logging_handler`, `create_json_handler`, `create_metrics_handler`.
  - Suporte a wildcard para receber todos os eventos.

- **Configuração (`src/worker/config.py`)**:
  - `PromptVariableConfig`: Configuração de variáveis de prompt.
  - `PromptTemplateConfig`: Configuração de templates.
  - `PromptsConfig`: Configuração completa para WorkerConfig.
  - Campo `prompts` adicionado ao `WorkerConfig`.

#### Alterado
- **Factory (`src/worker/factory.py`)**:
  - Refatorado para usar `ProviderRegistry` em vez de instanciação direta.
  - Removidas dependências diretas de `OpenAIChatClient` e `AzureOpenAIChatClient`.
  - Agora totalmente desacoplado do provider específico.

### Documentação
- `TODO.md` atualizado com Fase 7 completa (7.1, 7.2, 7.3, 7.6).
- Issues sugeridas para próximas etapas (Strategy Pattern, Tool Registry).

## [0.8.0] - 2025-11-26

### Core Framework Update (v1.0.0b251120)
- **Dependências:** Atualização forçada para `agent-framework-core==1.0.0b251120` (Commit 907d79a).
- **Group Chat:** Refatoração do `GroupChatBuilder` para utilizar `set_manager` (novo padrão) com fallback automático para `set_prompt_based_manager` (legacy), garantindo compatibilidade.
- **Handoff:** Implementação do método `auto_register_handoff_tools(True)` para registro automático de ferramentas de transferência.
- **Router:** Ajuste no `WorkflowEngine` para processar outputs do tipo `list[ChatMessage]`, substituindo a expectativa anterior de string pura.
- **Testes:** Adição de `tests/test_group_chat_refactor.py` para validar a lógica de seleção de manager.

## [0.7.0] - 2025-11-25

### Adicionado
- **Landing Page v2:** Redesign completo focado na experiência do colaborador ("Internal Builder").
- **Workflow Visualization:** Diagrama SVG interativo e complexo demonstrando padrões de Router, Sequential, Group Chat e Handoff.
- **Use Cases:** Novos cenários operacionais detalhados (Auditoria de Calls, Triagem de Email, Investigação de Fraudes).
- **Documentation:** Guia de identidade visual em `docs/rebranding/README.md`.

### Alterado
- **Rebranding (MAIA):**
    - Paleta de cores atualizada para identidade corporativa Mapfre.
    - Primária: Vermelho Corporativo (`#E6331A`).
    - Acento: Azul Institucional (`#003366`).
    - Gradientes e componentes UI ajustados para o novo esquema de cores.
- **Frontend:** Atualização de variáveis CSS em `index.css` para suporte a OKLCH e novas cores.

## [0.6.0] - 2025-11-25

### Adicionado

- **Gerenciamento de Workflows (CRUD):**
  - Nova página `WorkflowListPage` para listar, editar e excluir workflows.
  - Workflows são gerenciados a partir da pasta `exemplos/workflows/`.
  - Tabela com colunas: Nome, Arquivo, Tipo, Agentes, Steps.
  - Ações: Editar (abre no Studio), Executar (abre no Chat), Excluir.
  - Dialog de confirmação para exclusão segura.
  
- **Backend:**
  - Endpoint `DELETE /v1/workflows/{filename}` para remover arquivos de workflow.
  - Método `delete_entity` em `EntityDiscovery` para deletar entidades e seus arquivos.
  - Endpoint `DELETE /v1/entities/{entity_id}` exposto na API.

- **Frontend:**
  - `ApiClient.getSavedWorkflows()` - busca workflows da pasta `exemplos/workflows/`.
  - `ApiClient.deleteSavedWorkflow(filename)` - deleta arquivo de workflow.
  - `StudioPage` agora aceita parâmetro `?file=` para carregar workflow existente.
  - Menu lateral "Workflows" agora vai para a lista ao invés do Studio.

### Alterado

- Navegação do menu lateral reorganizada: "Workflows" leva à lista de gerenciamento.
- Fluxo de edição: Lista → Studio (com parâmetro file) → Salvar.

## [0.5.1] - 2025-11-24

### Refatoração (Engine + Builders)

- **WorkflowEngine:** passou a delegar todos os workflows de alto nível (`sequential`, `parallel`, `group_chat`, `handoff`, `router`) para os builders oficiais do Microsoft Agent Framework, unificando criação de participantes, roteamento e metadados.
- **Handoff e Router:** reconstruídos com `HandoffBuilder` e `WorkflowBuilder` + `Case/Default`, eliminando arestas manuais e restaurando compatibilidade com os exemplos da DevUI.
- **Group Chat:** criação automática do manager padrão usando o modelo configurado e registro determinístico dos participantes.
- **AgentFactory:** agora define `id`/`name` estáveis com base no `agent_id`, permitindo que handoffs reconheçam os alias corretos e preservando o `role` em `additional_properties` para exibição.
- **Ferramentas RAG:** `rag_index_documents` agora aceita string única além de listas, normalizando o input antes de chamar o `FunctionExecutor` e permitindo que o fluxo `dag_rag_test.json` inicialize sem erro de tipo.
- **Group Chat (Execução):** `WorkflowEngine` agora impõe um limite padrão de rodadas (configurável via `AI_PLATFORM_GROUP_CHAT_MAX_ROUNDS`) ao construir `GroupChatBuilder`, evitando loops infinitos e erros de contexto excedido ao testar `group_chat.json` via CLI.

### Correções (MAIA + UI)

- **Source Config Embed:** todo workflow construído pelo `WorkflowEngine` agora recebe `_source_config` com o blueprint completo, o que permite que a MAIA recupere metadados originais (tipo de nó, agente associado, templates etc.).
- **MAIA Server:** o endpoint `/v1/entities/{id}/info` enriquece o `workflow_dump` com esses metadados, mantendo o grafo do framework porém adicionando `node_type`, `agent`, `input_template` e `config` para cada executor.
- **Frontend (Workflow Utils):** passou a interpretar o blueprint enriquecido, priorizando `node_type` ao remontar o editor e preservando `start_step`. Com isso o UI deixa de enviar nós `_ConditionExecutor`/`FunctionExecutor` ao backend, desbloqueando a execução de todos os fluxos via MAIA.

## [0.5.0] - 2025-11-21

### Refatoração (Alinhamento Upstream)

- **Worker Engine:**
  - Substituição de classes customizadas (`ToolAgent`, `LogicAgent`, `RagAgent`) pelo uso nativo de `FunctionExecutor` do framework.
  - Simplificação do `_build_dag` em `src/worker/engine.py`.
  - Remoção de `src/worker/nodes.py` (código morto).
- **Backend:**
  - Validação de paridade entre `src/maia_ui` e `agent_framework_devui`.

## [0.4.0] - 2025-11-21

### Adicionado

- **Evolução do Backend (DAG & RAG):**
  - Suporte a workflows baseados em grafo (DAG) com nós e arestas explícitos.
  - Novos tipos de nós: `condition` (lógica if/else), `router` (switch/case), `tool` (execução direta).
  - Módulo RAG (`src/worker/rag`) com componentes para Loader, Splitter e Vector Store simples.
  - Sistema de descoberta automática de ferramentas (`src/worker/discovery.py`).
  - Atualização do schema de configuração (`src/worker/config.py`) para suportar `nodes` e `edges`.

## [0.3.0] - 2025-11-21

### Adicionado

- **MAIA (Microsoft Agent Interface for Arnaldo):** Integração completa da interface de desenvolvimento (antiga DevUI).
  - Interface gráfica para visualização e teste de agentes e workflows.
  - Rebranding completo de "DevUI" para "MAIA".
  - Execução via `python run.py --ui`.
  - Build do frontend React integrado ao projeto.
- Suporte a carregamento automático de exemplos na interface.

### Alterado

- Atualização do `run.py` para suportar a flag `--ui` e servir a aplicação web.
- **Refatoração de Módulo:**
  - Renomeado módulo `src.devui` para `src.maia_ui` para melhor alinhamento semântico.
  - Atualizado `run.py` e configurações de build do frontend.

## [0.2.0] - 2025-11-20

### Adicionado
- Suporte completo a **Group Chat** (`type: group_chat`) com gerenciador automático.
- Suporte a **Handoff** (`type: handoff`) para transições explícitas entre agentes.
- Diretório `exemplos/` centralizando todos os casos de uso (Sequencial, Paralelo, Router, Group Chat, Handoff, Humano).
- Diretório `ferramentas/` para centralizar funções Python usadas pelos agentes.
- Script `run.py` (antigo `executar.py`) como ponto único de entrada via CLI.

### Alterado
- **Refatoração Maior:** Limpeza da estrutura do projeto.
    - Removido diretório `scripts/` e testes antigos.
    - Renomeado `executar.py` para `run.py`.
    - Padronização dos nomes dos arquivos JSON em `exemplos/`.
- Atualização da documentação (`README.md` e `exemplos/README.md`).

## [0.1.0] - 2025-11-19

### Adicionado
- Implementado suporte a workflows paralelos (`type: parallel`).
- Implementado suporte a roteamento dinâmico (`type: router`).
- Implementado suporte a Human-in-the-loop (`type: human`).
- Estrutura base do Worker (`src/worker`).

### Alterado
- Finalizada Fase 1: Worker funcional com execução sequencial.

## [Início]

### Adicionado
- Criação inicial do `TODO.md` e `CHANGELOG.md`.
- Implementação do módulo `src.worker` com:
    - `config.py`: Modelos Pydantic e ConfigLoader.
    - `factory.py`: ToolFactory e AgentFactory.
    - `engine.py`: WorkflowEngine (suporte inicial sequencial).
