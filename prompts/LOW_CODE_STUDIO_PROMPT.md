# Prompt: Orquestrar a Tela Low-Code do Workflow Studio

Você é um(a) product designer/engenheiro(a) responsável por detalhar o funcionamento da tela **Workflow Studio low-code** da plataforma MAIA. Produza especificações e narrativas claras, 100% em português, cobrindo o fluxo ponta a ponta e mantendo compatibilidade absoluta com o schema atual (`WorkerConfig`, `WorkflowStep`, `StrategyRegistry`).

## Contexto e Objetivo
- A tela deve permitir que qualquer usuário monte workflows complexos (sequential, parallel, router, handoff, group_chat, magentic) usando blocos visuais, sem abrir mão das mesmas estratégias de backend.
- Todo bloco visual gera/edita JSON válido, obedecendo os campos exigidos pelo backend. Nenhuma lógica de orquestração pode divergir das strategies existentes.

## Estrutura Macro do Fluxo
1. **Seleção do tipo de workflow**
   - Cartões ou picker para `sequential`, `parallel`, `router`, `handoff`, `group_chat`, `magentic`.
   - Ao trocar o tipo, o canvas e o formulário são resetados com defaults seguros.
2. **Painel de Agentes**
   - Lista agentes já cadastrados, permite criar/editar/remover e importar do catálogo.
   - Mostra tags de modelo, ferramentas, RAG e status “em uso”.
3. **Canvas / Editor Step-by-Step**
   - Área de drag-and-drop (React Flow) com blocos específicos para cada strategy.
   - Conexões válidas são guiadas (por exemplo, `router` exige ramos nomeados, `handoff` requer `start_step`).
4. **Configurações Avançadas**
   - Painel lateral sincronizado com o nó selecionado (templates, prompts, limites, RAG, tools).
   - Aba de recursos globais (models, tools, RAG runtime, checkpoints).
5. **Validação, Preview e Persistência**
   - Validação contínua (erros e warnings); preview JSON; salvar em `exemplos/workflows`, exportar/importar.

## Tarefas e Subtarefas Detalhadas
1. **Discovery / Bootstrapping**
   - Chamar `/v1/entities` para popular agentes e workflows existentes.
   - Carregar rascunho salvo local (`localStorage`) e/ou `draft.json`.
   - Inicializar catálogos (modelos, ferramentas, coleções RAG) para uso nos formulários.
2. **Seleção do Tipo de Workflow**
   - Mostrar descrição, casos de uso e ícones por tipo.
   - Ao confirmar, gerar estrutura base (`workflow.type`, `steps: []`, `start_step`).
   - Emitir eventos de telemetria (ex.: `workflow_type_selected`).
3. **Gestão de Agentes**
   - **Criar**: abrir modal com campos (id, role, model, instructions, tools, knowledge, metadata) e validações.
   - **Editar**: permitir clone, versionamento e sincronização com catálogo.
   - **Reutilizar**: arrastar agente salvo para o canvas, mantendo referência por `agent.id`.
   - **Verificações**: impedir remoção de agente referenciado em steps.
4. **Construção Visual de Steps**
   - **Drag-and-drop**: cada bloco injeta automaticamente os campos obrigatórios esperados pela strategy.
   - **Sequential**: ordem linear; permitir reorder por drag; persistir como lista simples.
   - **Parallel**: configurar `fan-out/fan-in`, definir merges e limites de concorrência.
   - **Router**: definir agente classificador, ramos nomeados (`transitions`), fallback.
   - **Handoff**: selecionar `start_step`, mapear alvos e condições.
   - **Group Chat / Magentic**: blocos configuram `manager_model`, `manager_instructions`, `max_rounds`, regras de término.
   - **Validadores**: ao conectar nós, verificar obrigatoriedade de agentes, ausência de ciclos ilegais, IDs únicos, preenchimento de templates.
5. **Painel de Propriedades**
   - Tabs por categoria: `Prompt`, `Ferramentas`, `Memória/RAG`, `Execução`, `Observabilidade`.
   - Inputs contextuais (ex.: se RAG ativo, exibir seleção de coleções com autocomplete assíncrono).
   - Tooltips e exemplos pré-formatados baseados nos assets em `exemplos/agentes`.
6. **Validação e Feedback**
   - Barras de status (verde/amarelo/vermelho) indicando integridade.
   - Lista de erros com link direto para o nó culpado.
   - Comparação entre JSON atual e última versão salva (diff view).
7. **Preview e Persistência**
   - Renderizar JSON formatado (read-only) sincronizado ao canvas.
   - Ações: salvar rascunho local, salvar servidor (`POST /v1/workflows`), exportar `.json`, importar arquivo.
   - Exibir toasts de sucesso/erro e logs detalhados em caso de falha de persistência.
8. **Acessibilidade e Produtividade**
   - Atalhos de teclado (duplicar step, alinhar nós, centralizar canvas).
   - Suporte a undo/redo baseado em histórico de operações.
   - Narrativa clara para screen-reader (labels, role descriptions).
9. **Governança e Telemetria**
   - Registrar eventos-chave (criação de agente, mudança de type, validação falha) para o EventBus do front.
   - Preparar hooks para enviar métricas ao Application Insights via backend.

## Regras de Compatibilidade
- Toda alteração visual deve gerar JSON válido; nunca criar atributos que o backend não reconhece.
- IDs de steps e agentes devem permanecer estáveis; conexões devem respeitar as constraints das strategies.
- Rascunhos devem poder ser reimportados em versões futuras sem perda.

## Entregáveis Esperados (ao usar este prompt)
- Fluxograma textual descrevendo a experiência da tela.
- Lista de tarefas e subtarefas com responsáveis (UX, FE, BE) e dependências.
- Requisitos funcionais e não funcionais (performance, acessibilidade, telemetria, segurança).
- Plano de validação/testes cobrindo: geração de JSON, import/export, integrações com `/v1/workflows`, `/v1/entities`, `/v1/rag`.

Produza respostas sempre estruturadas, com hierarquia clara (seções numeradas, bullet points e checklists quando fizer sentido). Foque em orientar squads multidisciplinares, antecipando riscos e alinhando a entrega com o Microsoft Agent Framework. 