# Análise Detalhada dos Recursos de Orquestração do Microsoft Agent Framework

Este documento apresenta uma análise detalhada dos exemplos de orquestração do `agent_framework`, cobrindo padrões sequenciais, concorrentes, handoffs, group chat e orquestração "magentic" (baseada em planejamento).

## 1. Orquestração Sequencial (`SequentialBuilder`)

O padrão sequencial permite encadear agentes ou executores onde a saída de um passo alimenta o contexto do próximo, mantendo um histórico de conversação compartilhado.

### Exemplos Analisados

#### `sequential_agents.py`

* **Cenário:** Um fluxo simples onde um agente "writer" gera um texto e um agente "reviewer" o avalia.
* **Recursos Utilizados:**
  * `SequentialBuilder`: Construtor principal para fluxos lineares.
  * `.participants([agent1, agent2])`: Define a ordem de execução. Os participantes compartilham uma lista de `ChatMessage`.
  * **Adaptadores Internos:** O framework insere automaticamente adaptadores ("input-conversation", "to-conversation") para normalizar entradas e saídas entre os agentes.
  * `WorkflowOutputEvent`: Evento que contém o resultado final do fluxo (a lista completa de mensagens).
* **Principais Imports:**
  ```python
  from agent_framework import ChatMessage, Role, SequentialBuilder, WorkflowOutputEvent
  from agent_framework.azure import AzureOpenAIChatClient
  ```

#### `sequential_custom_executors.py`

* **Cenário:** Mistura um agente padrão com um executor customizado (`Summarizer`) que processa a conversa via código Python.
* **Recursos Utilizados:**
  * `Executor`: Classe base para criar lógica customizada.
  * `@handler`: Decorador para marcar o método que processa a entrada.
  * `WorkflowContext`: Usado para enviar resultados (`ctx.yield_output`) ou mensagens (`ctx.send_message`).
  * **Interoperabilidade:** Demonstra como agentes de IA e código imperativo podem coexistir no mesmo pipeline sequencial.
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatMessage,
      Executor,
      Role,
      SequentialBuilder,
      WorkflowContext,
      handler,
  )
  from agent_framework.azure import AzureOpenAIChatClient
  ```

---

## 2. Orquestração Concorrente (`ConcurrentBuilder`)

O padrão concorrente permite executar múltiplos agentes ou executores em paralelo ("fan-out") e agregar seus resultados ("fan-in").

### Exemplos Analisados

#### `concurrent_agents.py`

* **Cenário:** Três agentes (pesquisador, marqueteiro, advogado) recebem o mesmo prompt simultaneamente.
* **Recursos Utilizados:**
  * `ConcurrentBuilder`: Construtor para fluxos paralelos.
  * **Dispatcher/Aggregator Padrão:** O framework usa um dispatcher padrão que envia a entrada para todos e um agregador que concatena as respostas em uma lista de `ChatMessage`.
* **Principais Imports:**
  ```python
  from agent_framework import ChatMessage, ConcurrentBuilder
  from agent_framework.azure import AzureOpenAIChatClient
  ```

#### `concurrent_custom_agent_executors.py`

* **Cenário:** Similar ao anterior, mas encapsula cada agente em uma classe `Executor` customizada.
* **Recursos Utilizados:**
  * `AgentExecutorRequest` e `AgentExecutorResponse`: Tipos de dados para comunicação estruturada entre o orquestrador e os executores.
  * **Encapsulamento:** Permite controle fino sobre como o agente é invocado e como sua resposta é formatada antes de retornar ao fluxo principal.
* **Principais Imports:**
  ```python
  from agent_framework import (
      AgentExecutorRequest,
      AgentExecutorResponse,
      ChatAgent,
      ChatMessage,
      ConcurrentBuilder,
      Executor,
      WorkflowContext,
      handler,
  )
  from agent_framework.azure import AzureOpenAIChatClient
  ```

#### `concurrent_custom_aggregator.py`

* **Cenário:** Executa agentes em paralelo e usa um **agregador customizado** (uma função assíncrona) para sintetizar as respostas usando uma chamada de LLM.
* **Recursos Utilizados:**
  * `.with_aggregator(callback)`: Substitui a agregação padrão. O callback recebe os resultados de todos os ramos e produz a saída final do workflow.
  * **Padrão Map-Reduce:** Implementa efetivamente um padrão map-reduce onde os agentes fazem o "map" e a função customizada faz o "reduce".
* **Principais Imports:**
  ```python
  from agent_framework import ChatMessage, ConcurrentBuilder, Role
  from agent_framework.azure import AzureOpenAIChatClient
  ```

---

## 3. Orquestração via Handoff (`HandoffBuilder`)

Este padrão modela fluxos de atendimento onde o controle é passado explicitamente de um agente para outro (roteamento).

### Exemplos Analisados

#### `handoff_simple.py`

* **Cenário:** Um agente de triagem recebe o usuário e roteia para especialistas (reembolso, pedidos, suporte).
* **Recursos Utilizados:**
  * `HandoffBuilder`: Construtor para grafos de roteamento.
  * `.set_coordinator(agent)`: Define o ponto de entrada (triagem).
  * **Ferramentas Automáticas:** O framework cria ferramentas (tools) de handoff automaticamente baseadas nos nomes dos agentes (ex: `handoff_to_refund_agent`).
  * `.with_termination_condition(callback)`: Define quando o loop de interação deve parar (ex: após N mensagens).
  * `HandoffUserInputRequest`: Evento que sinaliza que o workflow está aguardando input do usuário.
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatAgent,
      ChatMessage,
      HandoffBuilder,
      HandoffUserInputRequest,
      RequestInfoEvent,
      WorkflowEvent,
      WorkflowOutputEvent,
      WorkflowRunState,
      WorkflowStatusEvent,
  )
  from agent_framework.azure import AzureOpenAIChatClient
  ```

#### `handoff_specialist_to_specialist.py`

* **Cenário:** Roteamento multinível. Triagem -> Especialista A -> Especialista B.
* **Recursos Utilizados:**
  * `.add_handoff(source, [targets])`: Define explicitamente o grafo de transições permitidas.
  * **Transições Diretas:** Permite que especialistas passem o bastão entre si sem voltar para o usuário ou para a triagem, útil para resolver problemas complexos em uma única interação do usuário.
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatMessage,
      HandoffBuilder,
      HandoffUserInputRequest,
      RequestInfoEvent,
      WorkflowEvent,
      WorkflowOutputEvent,
      WorkflowRunState,
      WorkflowStatusEvent,
  )
  from agent_framework.azure import AzureOpenAIChatClient
  ```

#### `handoff_return_to_previous.py`

* **Cenário:** Demonstra o recurso de "retorno ao anterior", onde a entrada do usuário volta para o último especialista ativo.
* **Recursos Utilizados:**
  * `.enable_return_to_previous(True)`: Mantém o contexto do especialista. Se o usuário responde a uma pergunta do "Suporte Técnico", a mensagem vai direto para o "Suporte Técnico", não para a "Triagem".
  * **Contexto Persistente:** Essencial para conversas multi-turno com um especialista específico.
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatAgent,
      HandoffBuilder,
      HandoffUserInputRequest,
      RequestInfoEvent,
      WorkflowEvent,
      WorkflowOutputEvent,
  )
  from agent_framework.azure import AzureOpenAIChatClient
  ```

---

## 4. Orquestração Group Chat (`GroupChatBuilder`)

Gerencia um grupo de agentes que colaboram em uma conversa compartilhada, com lógica para decidir "quem fala a seguir".

### Exemplos Analisados

#### `group_chat_simple_selector.py`

* **Cenário:** Alternância simples entre um pesquisador e um escritor.
* **Recursos Utilizados:**
  * `GroupChatBuilder`: Construtor para chat em grupo.
  * `.select_speakers(selector_func)`: Usa uma função Python pura para determinar o próximo falante.
  * `GroupChatStateSnapshot`: Objeto passado para a função seletora, contendo histórico, participantes e índice da rodada.
* **Principais Imports:**
  ```python
  from agent_framework import ChatAgent, GroupChatBuilder, GroupChatStateSnapshot, WorkflowOutputEvent
  from agent_framework.openai import OpenAIChatClient
  ```

#### `group_chat_prompt_based_manager.py`

* **Cenário:** Um "Gerente" (LLM) decide quem deve falar com base no contexto.
* **Recursos Utilizados:**
  * `.set_prompt_based_manager(chat_client)`: Configura um LLM para atuar como orquestrador, decidindo dinamicamente o fluxo da conversa.
* **Principais Imports:**
  ```python
  from agent_framework import AgentRunUpdateEvent, ChatAgent, GroupChatBuilder, WorkflowOutputEvent
  from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient
  ```

---

## 5. Orquestração Magentic (`MagenticBuilder`)

O padrão mais avançado, focado em agentes autônomos que planejam, executam e revisam tarefas complexas.

### Exemplos Analisados

#### `magentic.py`

* **Cenário:** Um gerente coordena um pesquisador e um codificador para resolver uma tarefa complexa (análise de eficiência energética de ML).
* **Recursos Utilizados:**
  * `MagenticBuilder`: Construtor para workflows baseados em planejamento.
  * `.with_standard_manager(...)`: Configura o "cérebro" do workflow, responsável por quebrar tarefas e delegar.
  * **Eventos de Streaming:** `MagenticOrchestratorMessageEvent` (pensamento do gerente), `MagenticAgentDeltaEvent` (streaming de resposta dos agentes).
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatAgent,
      HostedCodeInterpreterTool,
      MagenticAgentDeltaEvent,
      MagenticAgentMessageEvent,
      MagenticBuilder,
      MagenticFinalResultEvent,
      MagenticOrchestratorMessageEvent,
      WorkflowOutputEvent,
  )
  from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient
  ```

#### `magentic_checkpoint.py`

* **Cenário:** Pausa o workflow para revisão humana e retoma posteriormente.
* **Recursos Utilizados:**
  * `.with_checkpointing(storage)`: Habilita persistência de estado.
  * `FileCheckpointStorage`: Implementação de armazenamento em arquivo (pode ser substituído por DB).
  * **Retomada:** Capacidade de carregar o estado de um ponto específico e continuar a execução, injetando respostas pendentes.
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatAgent,
      FileCheckpointStorage,
      MagenticBuilder,
      MagenticPlanReviewDecision,
      MagenticPlanReviewReply,
      MagenticPlanReviewRequest,
      RequestInfoEvent,
      WorkflowCheckpoint,
      WorkflowOutputEvent,
      WorkflowRunState,
      WorkflowStatusEvent,
  )
  from agent_framework.azure import AzureOpenAIChatClient
  ```

#### `magentic_human_plan_update.py`

* **Cenário:** O humano revisa e aprova (ou edita) o plano gerado pelo agente antes da execução.
* **Recursos Utilizados:**
  * `.with_plan_review()`: Insere uma etapa de aprovação manual no ciclo de vida.
  * `MagenticPlanReviewRequest`: Evento emitido quando um plano está pronto para revisão.
  * `MagenticPlanReviewReply`: Resposta do usuário (APROVAR, REVISAR) enviada de volta ao workflow.
* **Principais Imports:**
  ```python
  from agent_framework import (
      ChatAgent,
      HostedCodeInterpreterTool,
      MagenticAgentDeltaEvent,
      MagenticAgentMessageEvent,
      MagenticBuilder,
      MagenticFinalResultEvent,
      MagenticOrchestratorMessageEvent,
      MagenticPlanReviewDecision,
      MagenticPlanReviewReply,
      MagenticPlanReviewRequest,
      RequestInfoEvent,
      WorkflowOutputEvent,
  )
  from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient
  ```

---

## Resumo dos Principais Componentes

| Componente | Finalidade |
| :--- | :--- |
| **Builders** | `SequentialBuilder`, `ConcurrentBuilder`, `HandoffBuilder`, `GroupChatBuilder`, `MagenticBuilder` |
| **Eventos** | `WorkflowOutputEvent`, `RequestInfoEvent`, `WorkflowStatusEvent`, `AgentRunUpdateEvent` |
| **Conceitos** | `Executor` (unidade de trabalho), `Agent` (IA conversacional), `WorkflowContext` (contexto de execução) |
| **Extensibilidade** | Callbacks de agregação, seletores de falante customizados, armazenamento de checkpoint |
