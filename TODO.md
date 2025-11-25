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
