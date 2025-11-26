# Changelog

Todos os marcos notáveis deste projeto serão documentados neste arquivo.

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
