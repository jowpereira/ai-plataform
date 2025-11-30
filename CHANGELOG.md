# Changelog

Todos os marcos notáveis deste projeto serão documentados neste arquivo.

## [0.17.1] - 2025-11-29

### Correções Playground e Serialização de Eventos

#### Corrigido
- **WorkflowView (`workflow-view.tsx`)**:
  - Removido envio de `workflow_config` customizado - workflows declarativos já estão definidos no backend.
  - Playground agora é puramente para visualização e debug do grafo, não modificação.
  - Erro "Field required: steps" eliminado.

- **Serialização de ChatMessage (`_mapper.py`)**:
  - Corrigido tratamento de listas de `ChatMessage` em `WorkflowOutputEvent`.
  - Output final agora mostra texto real das mensagens em vez de `<object at 0x...>`.
  - Formato: `[autor]: texto` quando há `author_name`, senão apenas texto.

- **Tipo de Workflow (`workflow-utils.ts`)**:
  - Removido tipo `dag` do default (não suportado pelo backend).
  - Default alterado para `sequential`.
  - Adicionado suporte a `magentic` nos tipos válidos.

- **Tipos TypeScript (`workflow.ts`)**:
  - Adicionado `magentic` ao tipo `WorkflowConfig.type`.

- **Seletor de Entidades no Header (`app-header.tsx`, `PlatformLayout.tsx`)**:
  - Seletor de agentes/workflows agora só aparece em páginas que precisam.
  - Visível apenas no Playground e Chat.
  - Demais páginas mostram apenas marca MAIA e controles globais.

## [0.17.0] - 2025-11-29

### Frontend - Globalização do Header e Unificação Chat/Playground

#### Adicionado
- **PlaygroundPage (`src/pages/platform/playground/PlaygroundPage.tsx`)**:
  - Nova página substitui DebugPage com foco em desenvolvimento e testes.
  - Mantém funcionalidades de debug panel, workflow visualization e ferramentas.
  - Código simplificado - lógica de carregamento movida para PlatformLayout.

#### Alterado
- **PlatformLayout (`src/layouts/PlatformLayout.tsx`)**:
  - AppHeader agora é global, visível em todas as páginas da plataforma.
  - Carregamento centralizado de entidades (agents, workflows) via Zustand store.
  - Nova organização da sidebar: Playground acima do Chat na seção "Interação".
  - Estados de loading e erro tratados no nível do layout.

- **ChatPage (`src/pages/platform/chat/ChatPage.tsx`)**:
  - Completamente refatorada para usar `AgentView` e `WorkflowView`.
  - Mesma engine robusta do Playground (renderização de ferramentas, streaming, attachments).
  - Debug panel automaticamente desabilitado para experiência focada na conversação.
  - Suporte completo a workflows sem visualização do grafo.

- **App.tsx**:
  - Rota `/platform/debug` redirecionada para `/platform/playground` (backward compatibility).
  - Nova rota `/platform/playground` registrada.

- **Sidebar/Navegação**:
  - "Debug Console" renomeado para "Playground" com ícone Play.
  - Reordenação: Dashboard → Agentes → Workflows → [Playground → Chat] → Admin.
  - Título "AI Platform" removido da sidebar (marca agora está no Header global).

#### Deprecated
- **AssistantChat (`src/components/features/chat/AssistantChat.tsx`)**:
  - Marcado como `@deprecated` - será removido em versão futura.
  - Substituído por AgentView que oferece melhor tratamento de ferramentas e erros.

#### Correções
- Problemas de renderização de ferramentas na página de Chat corrigidos.
- Sincronização de entidade selecionada agora funciona corretamente entre páginas.
- Query param `?entity_id=...` continua funcionando para deep linking.

## [0.16.2] - 2025-11-28

### Persistência e Validação (Fase 8 e 9)

#### Adicionado
- **Persistência de Estado (`src/worker/state.py`)**:
  - Implementado mecanismo de Checkpointing automático.
  - Estado do workflow salvo em arquivo JSON configurável (`checkpoint_file`).
  - Suporte a recuperação de estado (`load_checkpoint`) na inicialização do Engine.
  - Modelo de estado migrado para Pydantic para serialização robusta.

#### Validado
- **Testes de Regressão**:
  - Validado workflow de Handoff (`handoff_human.json`) - Sucesso.
  - Validado workflow de Code Interpreter Local (`magentic_code_interpreter.json`) - Sucesso.
  - Validado persistência de estado via teste manual.

#### Documentação
- Atualizado `TODO.md` refletindo conclusão das Fases 8 e 9.1.

## [0.16.1] - 2025-11-28

### Ferramentas Locais - Alternativa às Hosted Tools (Fase 9.1)

> **Contexto**: Hosted Tools (HostedCodeInterpreterTool, HostedWebSearchTool) requerem Azure AI Agent Service (AzureAIAgentClient), não Azure OpenAI Chat Completions. Este projeto usa AzureOpenAIChatClient, portanto ferramentas locais foram implementadas.

#### Adicionado
- **Arquitetura Plug-and-Play de Ferramentas (`ferramentas/`)**:
  - `ferramentas/__init__.py`: Módulo centralizado com exports e documentação
  - `ferramentas/registry.py`: Registry baseado em decorators com categorias e tags
  - Decorator `@ai_tool` que combina `@ai_function` + registro automático

- **Web Search Real (`ferramentas/web_search.py`)**:
  - Backend DuckDuckGo gratuito (sem necessidade de API key)
  - Funções: `pesquisar_web()`, `buscar_noticias()`, `buscar_documentacao()`, `buscar_multiplo()`
  - Suporte assíncrono via aiohttp
  - Fallback inteligente quando API indisponível

- **Code Interpreter Seguro (`ferramentas/code_interpreter.py`)**:
  - Sandbox com execução isolada e timeout de 30s
  - Whitelist de módulos seguros (math, datetime, json, re, collections, etc.)
  - Builtins restritos (sem file I/O, network, exec perigosos)
  - Funções: `executar_codigo()`, `calcular()`, `analisar_dados()`, `gerar_grafico_texto()`

- **Aviso de Incompatibilidade (`src/worker/factory.py`)**:
  - Warning explícito quando Hosted Tools são usadas com cliente incompatível
  - Mensagem: "Hosted Tools requerem Azure AI Agent Service (AzureAIAgentClient)"

#### Alterado
- **Workflows Atualizados**:
  - `magentic_code_interpreter.json`: `hosted://` → `ferramentas:code_interpreter`
  - `magentic_research_team.json`: `hosted://` → `ferramentas:web_search`
  - `group_chat_hosted_tools.json`: Ambas ferramentas migradas
  - `sequential_hosted_tools.json`: Ambas ferramentas migradas
  - Nenhum workflow usa mais `hosted://` paths

#### Dependências
- Adicionado `aiohttp` para requisições HTTP assíncronas no web search

#### Documentação
- Atualizado `TODO.md` com Fase 9: Ferramentas Locais e Azure AI Agent Service (futuro)
- Documentado plano para futura integração com Azure AI Agent Service

---

## [0.16.0] - 2025-11-28

### Worker SDK - Implementação de Gaps do Framework (Fase 8)

> **Objetivo**: Fechar os gaps identificados no relatório de investigação, implementando Streaming, Approval Mode e Hosted Tools.

#### Adicionado
- **Streaming de Eventos (`src/worker/engine.py`)**:
  - Implementado suporte a `AGENT_STREAM_UPDATE` no método `ainvoke`.
  - Captura de deltas de streaming do framework e emissão de eventos normalizados.
  - Permite feedback em tempo real token-a-token na UI/CLI.

- **Approval Mode (`src/worker/tools/models.py`)**:
  - Adicionado enum `ApprovalMode` (NEVER, ALWAYS, ON_FIRST, CONDITIONAL).
  - Campo `approval_mode` no `ToolDefinition` e `ToolConfig`.
  - Suporte a configuração via YAML (`approval_mode: always`).

- **Hosted Tools (`src/worker/tools/adapters/hosted.py`)**:
  - Novo adapter `HostedToolAdapter` para ferramentas nativas do framework.
  - Suporte a `HostedCodeInterpreterTool`, `HostedWebSearchTool`, `HostedFileSearchTool`.
  - Integração transparente com o sistema de registry existente.

#### Alterado
- **Factory (`src/worker/factory.py`)**:
  - Atualizado `register_from_config` para processar `approval_mode` e `hosted_config`.
  - Importação de novos tipos de ferramentas e modos de aprovação.

- **Configuração (`src/worker/config.py`)**:
  - Atualizado `ToolConfig` com campos `approval_mode` e `hosted_config`.

#### Impacto
- **Streaming**: Experiência de usuário mais fluida com respostas em tempo real.
- **Segurança**: Controle humano sobre execução de ferramentas sensíveis.
- **Capacidade**: Acesso a ferramentas poderosas hospedadas (Code Interpreter, Bing Search).

---

## [0.15.5] - 2025-11-28

### Documentação - Guia de Investigação do Framework (Completo)

#### Adicionado
- **`prompts/GUIA_INVESTIGACAO_FRAMEWORK.md`** — Guia completo e expandido para validar alinhamento com Microsoft Agent Framework:
  - **Resumo Executivo** com status de conformidade de todas as 6 strategies
  - **Fase 1**: Análise comparativa de orquestradores (tabela validada)
  - **Fase 2**: Mapeamento de ferramentas built-in (incluindo análise de Hosted Tools)
  - **Fase 3**: Comparação de schemas declarativos
  - **Fase 4**: Eventos e callbacks (com matriz detalhada e gaps de Streaming/HITL)
  - **Fase 5**: Checklist de compliance

- **Apêndice A — Deep Dive Magentic One**:
  - Arquitetura interna documentada (MagenticContext, TaskLedger, ProgressLedger)
  - Prompts internos mapeados (FACTS, PLAN, PROGRESS)
  - Fluxo de execução detalhado e checklist de conformidade

- **Apêndice B — Ferramentas Built-in por Orquestrador**:
  - Mapeamento de injeção automática e confirmação do modelo Magentic

- **Apêndice C — Schema Declarativo**:
  - Referência para análise de workflow samples YAML

- **Apêndice D — Relatório da Investigação**:
  - Análise detalhada de `_tools.py` e `_events.py`
  - Lista de gaps identificados (Streaming, Approval Mode, Hosted Tools)

#### Status de Conformidade (Validado ✅)
| Orquestrador | Builder Oficial | Nossa Strategy | Conformidade |
|--------------|-----------------|----------------|--------------|
| Sequential | `SequentialBuilder` | `SequentialStrategy` | ✅ 100% |
| Parallel | `ConcurrentBuilder` | `ParallelStrategy` | ✅ 100% |
| Group Chat | `GroupChatBuilder` | `GroupChatStrategy` | ✅ 100% |
| Handoff | `HandoffBuilder` | `HandoffStrategy` | ✅ 100% |
| Router | `WorkflowBuilder` | `RouterStrategy` | ✅ 100% |
| Magentic | `MagenticBuilder` | `MagenticStrategy` | ✅ 100% |

#### Gaps Identificados para Próxima Versão
1. **Streaming**: Falta `AGENT_STREAM_UPDATE`
2. **Approval Mode**: `@ai_function(approval_mode=...)` não explorado
3. **Hosted Tools**: Oportunidade de integrar code_interpreter, web_search

---

## [0.15.4] - 2025-11-28

### Frontend - Suporte Completo ao Workflow Magentic One

#### Adicionado
- **`MagenticEditor.tsx`** — Editor visual para workflows Magentic One:
  - Configuração do Manager (modelo, instruções, max_rounds, max_stall_count)
  - Switch para Human-in-the-Loop (plan review)
  - Gerenciamento visual de participantes
  - Tooltips explicativos para cada campo
  - Validações específicas do tipo magentic

- **`tooltip.tsx`** — Componente Tooltip (shadcn/ui) para dicas contextuais

- **Suporte ao tipo `magentic` no Workflow Studio**:
  - Adicionado em `WorkflowTypeSelector.tsx` com ícone Sparkles
  - Tipos atualizados em `types.ts`
  - Renderização no `StudioPage.tsx`
  - Validação específica (manager_model obrigatório, min 2 participantes)

#### Dependências
- `@radix-ui/react-tooltip` — componente de tooltip

#### Status dos Tipos de Workflow no Frontend
| Tipo | Status |
|------|--------|
| `sequential` | ✅ Completo |
| `parallel` | ✅ Completo |
| `group_chat` | ✅ Completo |
| `handoff` | ✅ Completo |
| `router` | ✅ Completo |
| `magentic` | ✅ **NOVO** |

---

## [0.15.3] - 2025-11-27

### UI do Console Aprimorada

#### Melhorado
- **ConsoleReporter (`src/worker/reporters/console.py`)**:
  - Painéis de início (Workflow/Agente) centralizados e destacados
  - Timestamps em todos os passos da execução
  - Role do agente em **bold** e centralizado
  - Diferenciação visual clara entre etapas intermediárias (💬 azul) e resultado final (📋 verde bold)
  - Subtítulos informativos com horário de conclusão
  - Ferramentas exibidas de forma compacta com ícone 🔧

---

## [0.15.2] - 2025-11-27

### Auditoria Profunda - Limpeza de Código Morto

#### Removido
- **`src/worker/prompts/`** — Diretório completo excluído (5 arquivos, ~1.200 linhas):
  - `__init__.py`, `messages.py`, `models.py`, `engine.py`, `context.py`
  - Reimplementava tipos já existentes no framework (`ChatMessage`, `Role`, `TextContent`)
  - Zero referências externas — código 100% morto

- **`OutputExecutor` (class deprecated)**:
  - Removida de `src/worker/strategies/executors.py`
  - Substituída pela função `yield_agent_response`

#### Corrigido
- **ConsoleReporter (`src/worker/reporters/console.py`)**:
  - Evento `AGENT_RUN_COMPLETE` agora exibe o resultado do agente
  - Corrige problema onde agentes executavam mas não mostravam output
  - Fallback plain-text também atualizado

- **Docstring genérica em `http.py`**:
  - Exemplo `buscar_cliente` substituído por `fetch_data` genérico

#### Validação
- Testados **7 agentes** standalone — todos funcionando ✅
- Testados **5 workflows** — 3 funcionando, 2 com problemas pré-existentes ⚠️
- Relatório completo em `docs/RELATORIO_AUDITORIA_CODIGO.md`

#### Impacto
- **-32%** linhas de código
- **-20%** arquivos Python
- Worker 100% alinhado com tipos nativos do Microsoft Agent Framework

---

## [0.15.1] - 2025-11-27

### Correção de Bug - Exibição do Magentic e Captura de Eventos

#### Corrigido
- **WorkflowEngine (`src/worker/engine.py`)**:
  - Corrigido comparação de `Role` enum vs string no processamento de `WorkflowOutputEvent`.
  - Agora usa `str(role) == 'assistant'` para compatibilidade com enum `agent_framework._types.Role`.
  - Respostas de cada agente são emitidas corretamente via `AGENT_RESPONSE`.
  - Eventos `AGENT_START` emitidos apenas uma vez por agente (sem duplicação).
  - Removido método helper `run()` - APIs públicas são apenas `invoke()` e `ainvoke()`.

- **EventMiddleware (`src/worker/middleware/__init__.py`)**:
  - Desabilitado emissão de eventos duplicados (controlado agora pelo engine).
  - Mantido apenas como pass-through para não interferir no fluxo.
  - Método `_extract_content()` preservado para uso futuro.

- **CLI (`run.py`)**:
  - Adicionada opção `--stream/--no-stream` para escolher modo de execução.
  - `--stream` (padrão): Usa `ainvoke()` com streaming e eventos em tempo real.
  - `--no-stream`: Usa `invoke()` para execução direta sem streaming.

- **ConsoleReporter (`src/worker/reporters/console.py`)**:
  - Método `_is_stream_placeholder()` para detectar placeholders de streaming.
  - Suprime exibição de respostas inválidas.

#### Técnico
- Tipos de eventos do framework identificados:
  - `AgentRunUpdateEvent`: Streaming com `executor_id` e `data.text` (delta).
  - `WorkflowOutputEvent`: Lista de `ChatMessage` com resultado completo.
  - `ExecutorCompletedEvent`: Marcador de conclusão de executor.
- `WorkflowOutputEvent.data` contém lista de `ChatMessage` com atributos:
  - `role`: Enum `Role.user` ou `Role.assistant`
  - `author_name`: Nome do agente (ex: `agente_pesquisador`)
  - `text`: Conteúdo completo da mensagem

#### Impacto
- Workflows agora exibem corretamente todas as respostas dos agentes.
- Console mostra painéis individuais para cada agente.
- Resultado final exibido corretamente no painel "Workflow Concluído".

---

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
