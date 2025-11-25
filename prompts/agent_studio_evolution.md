# 🤖 Prompt de Sistema: Evolução do Agent Studio

> **Tipo**: Prompt de Instruções para Sistema de Agentes  
> **Versão**: 2.0 | **Data**: 2025-11-25  
> **Objetivo**: Guiar a implementação do Agent Studio com capacidade completa de criação de agentes e workflows

---

## 📋 Contexto do Projeto

O **AI Platform** é uma plataforma de orquestração de agentes baseada no `agent_framework` (Microsoft). O objetivo atual é evoluir o **Agent Studio** **frontend** para permitir:

1. **Criar agentes** individualmente (com modelo, instruções, ferramentas)
2. **Criar workflows de agentes** (reutilizando agentes existentes ou criando novos inline)
3. **Salvar configurações** em JSON
4. **Executar** via CLI (`run.py`) ou via UI (aba Debug)

### Tipos de Workflow Suportados (Builders de Alto Nível)

| Tipo | Descrição | Uso |
|------|-----------|-----|
| `sequential` | Cadeia linear A → B → C | Pipeline simples |
| `parallel` | Fan-out → Fan-in | Processamento paralelo |
| `group_chat` | Multi-agente com Manager | Discussão colaborativa |
| `handoff` | Triagem com coordenador | Roteamento inteligente |
| `router` | Switch/Case condicional | Decisão baseada em output |

---

## ⚠️ INSTRUÇÃO CRÍTICA: Desabilitar DAG Temporariamente

### Motivo
O modo DAG genérico (`type: "dag"` com `nodes`/`edges`) é complexo e não está totalmente validado. **Momentaneamente**, o foco deve ser nos builders de alto nível que são mais seguros e cobrem 90% dos casos de uso.

### Ações Requeridas

#### Frontend (`frontend/src/`)

1. **Comentar/Desabilitar** a opção "DAG" no seletor de tipo de workflow
2. **Comentar/Desabilitar** a renderização de nodes/edges customizados
3. **Manter apenas** os tipos: `sequential`, `parallel`, `group_chat`, `handoff`, `router`
4. **Adicionar TODO** com mensagem: `// TODO: Reativar DAG quando validação estiver pronta`

**Arquivos afetados:**
- `frontend/src/pages/platform/studio/StudioPage.tsx`
- `frontend/src/components/features/studio/` (todos os componentes)
- `frontend/src/types/workflow.ts`

#### Backend (`src/worker/`)

1. **Comentar** (não remover) o código do `_build_dag()` em `engine.py`
2. **Lançar exceção** se `type: "dag"` for recebido: `raise NotImplementedError("DAG mode temporarily disabled. Use high-level builders.")`
3. **Manter** a estrutura de nodes/edges no config.py para compatibilidade futura

**Arquivos afetados:**
- `src/worker/engine.py` - método `_build_dag()`
- `src/worker/config.py` - manter `NodeConfig` e `EdgeConfig` comentados ou com flag

---

## 🎯 Plano de Tarefas: Agent Studio

### Épico 1: Criação de Agentes

#### Task 1.1: Tela de Lista de Agentes
**Descrição**: Criar tela para visualizar, criar, editar e deletar agentes do projeto.

**Subtarefas:**
- [ ] 1.1.1 Criar componente `AgentListPage.tsx` em `pages/platform/agents/`
- [ ] 1.1.2 Implementar tabela com colunas: ID, Role, Modelo, Ferramentas, Ações
- [ ] 1.1.3 Adicionar botão "Novo Agente" que abre modal de criação
- [ ] 1.1.4 Implementar ações: Editar, Duplicar, Deletar
- [ ] 1.1.5 Adicionar filtro por modelo e busca por nome

**Critérios de Aceite:**
- Lista carrega agentes do projeto atual
- CRUD completo funcional
- Feedback visual para ações (toast notifications)

#### Task 1.2: Modal/Formulário de Criação de Agente
**Descrição**: Formulário completo para definir um agente.

**Subtarefas:**
- [ ] 1.2.1 Criar componente `AgentFormModal.tsx`
- [ ] 1.2.2 Campos obrigatórios: `id`, `role`, `model`, `instructions`
- [ ] 1.2.3 Campo opcional: `description` (para orquestração)
- [ ] 1.2.4 Seletor de modelo (dropdown com modelos disponíveis em `resources.models`)
- [ ] 1.2.5 Multi-select de ferramentas (lista de `resources.tools`)
- [ ] 1.2.6 Editor de instruções com syntax highlighting (markdown)
- [ ] 1.2.7 Preview do JSON gerado em tempo real
- [ ] 1.2.8 Validação de formulário (Zod ou similar)

**Critérios de Aceite:**
- Formulário valida campos obrigatórios
- JSON preview atualiza em tempo real
- Salvar adiciona agente à configuração

#### Task 1.3: Gerenciamento de Recursos (Models/Tools)
**Descrição**: Permitir adicionar modelos e ferramentas ao projeto.

**Subtarefas:**
- [ ] 1.3.1 Criar aba "Recursos" no Studio ou página separada
- [ ] 1.3.2 Seção "Modelos": adicionar modelo com tipo (openai/azure-openai) e deployment
- [ ] 1.3.3 Seção "Ferramentas": adicionar ferramenta com ID, path (`module:function`), descrição
- [ ] 1.3.4 Validar path de ferramenta (formato `module:function`)
- [ ] 1.3.5 Auto-descoberta de ferramentas do diretório `tools/` (chamar API `/v1/tools`)

**Critérios de Aceite:**
- Recursos salvos no JSON do projeto
- Validação de formato de path
- Ferramentas descobertas automaticamente listadas

---

### Épico 2: Criação de Workflows

#### Task 2.1: Seletor de Tipo de Workflow
**Descrição**: Interface para escolher o tipo de workflow antes de configurar.

**Subtarefas:**
- [ ] 2.1.1 Criar componente `WorkflowTypeSelector.tsx`
- [ ] 2.1.2 Cards visuais para cada tipo: Sequential, Parallel, Group Chat, Handoff, Router
- [ ] 2.1.3 Cada card com ícone, nome, descrição curta e exemplo de uso
- [ ] 2.1.4 **Desabilitar/ocultar** opção "DAG" (comentar com TODO)
- [ ] 2.1.5 Ao selecionar, navegar para o editor específico do tipo

**Critérios de Aceite:**
- 5 tipos disponíveis (sem DAG)
- Cards responsivos e acessíveis
- Seleção leva ao editor correto

#### Task 2.2: Editor de Workflow Sequential
**Descrição**: Interface visual para criar workflow sequencial.

**Subtarefas:**
- [ ] 2.2.1 Criar componente `SequentialWorkflowEditor.tsx`
- [ ] 2.2.2 Lista ordenável (drag-and-drop) de steps
- [ ] 2.2.3 Cada step: selecionar agente existente OU criar novo inline
- [ ] 2.2.4 Campo `input_template` com placeholders `{{user_input}}`, `{{previous_output}}`
- [ ] 2.2.5 Botão "Adicionar Step" no final da lista
- [ ] 2.2.6 Preview visual do fluxo (A → B → C)
- [ ] 2.2.7 Gerar JSON de output em tempo real

**Critérios de Aceite:**
- Steps reordenáveis via drag-and-drop
- Seleção de agente funciona corretamente
- JSON gerado é válido para o worker

#### Task 2.3: Editor de Workflow Parallel
**Descrição**: Interface para workflow paralelo (fan-out/fan-in).

**Subtarefas:**
- [ ] 2.3.1 Criar componente `ParallelWorkflowEditor.tsx`
- [ ] 2.3.2 Visualização: um nó "Dispatcher" → N nós paralelos → um nó "Aggregator"
- [ ] 2.3.3 Adicionar/remover agentes paralelos
- [ ] 2.3.4 Cada agente com seu `input_template`
- [ ] 2.3.5 Opcional: configurar estratégia de agregação

**Critérios de Aceite:**
- Visualização clara de fan-out/fan-in
- Mínimo 2 agentes paralelos
- JSON gerado é válido

#### Task 2.4: Editor de Workflow Group Chat
**Descrição**: Interface para chat em grupo multi-agente.

**Subtarefas:**
- [ ] 2.4.1 Criar componente `GroupChatWorkflowEditor.tsx`
- [ ] 2.4.2 Lista de participantes (agentes) com ordem
- [ ] 2.4.3 Configuração do Manager:
  - [ ] 2.4.3.1 Modelo do manager (default: primeiro modelo disponível)
  - [ ] 2.4.3.2 Instruções do manager (como selecionar próximo speaker)
- [ ] 2.4.4 Campo `max_rounds` (padrão: 8)
- [ ] 2.4.5 Opcional: `termination_condition`
- [ ] 2.4.6 Preview visual: círculo com agentes conectados ao Manager central

**Critérios de Aceite:**
- Manager configurável
- Participantes adicionáveis/removíveis
- JSON inclui configuração de manager

#### Task 2.5: Editor de Workflow Handoff
**Descrição**: Interface para workflow de triagem/handoff.

**Subtarefas:**
- [ ] 2.5.1 Criar componente `HandoffWorkflowEditor.tsx`
- [ ] 2.5.2 Seleção de "Coordenador" (primeiro step, obrigatório)
- [ ] 2.5.3 Lista de "Especialistas" (outros agentes)
- [ ] 2.5.4 Para cada step, definir `transitions` (para quais agentes pode transferir)
- [ ] 2.5.5 Preview visual: coordenador no centro, especialistas ao redor com setas de transição

**Critérios de Aceite:**
- Coordenador obrigatório no `start_step`
- Transitions configuráveis por step
- JSON gerado inclui `transitions`

#### Task 2.6: Editor de Workflow Router
**Descrição**: Interface para workflow com roteamento condicional.

**Subtarefas:**
- [ ] 2.6.1 Criar componente `RouterWorkflowEditor.tsx`
- [ ] 2.6.2 Definir "Agente Roteador" (primeiro step)
- [ ] 2.6.3 Lista de "Destinos" (outros agentes)
- [ ] 2.6.4 Explicar que o roteador deve retornar o ID do próximo step
- [ ] 2.6.5 Último destino é automaticamente o `Default`
- [ ] 2.6.6 Preview visual: roteador com setas condicionais para destinos

**Critérios de Aceite:**
- Roteador obrigatório no `start_step`
- Destinos configuráveis
- Documentação inline sobre convenção de output

---

### Épico 3: Salvar e Carregar Projetos

#### Task 3.1: Serialização para JSON
**Descrição**: Gerar JSON válido do WorkerConfig.

**Subtarefas:**
- [ ] 3.1.1 Criar função `serializeWorkerConfig(state): WorkerConfig`
- [ ] 3.1.2 Incluir todos os campos: version, name, resources, agents, workflow
- [ ] 3.1.3 Validar JSON contra schema Pydantic do backend (ou Zod no frontend)
- [ ] 3.1.4 Formatar JSON com indentação de 2 espaços

**Critérios de Aceite:**
- JSON gerado passa validação do backend
- Formato legível e consistente

#### Task 3.2: Download de JSON
**Descrição**: Permitir baixar o JSON do projeto.

**Subtarefas:**
- [ ] 3.2.1 Botão "Exportar JSON" no header do Studio
- [ ] 3.2.2 Gerar arquivo com nome: `{project_name}.json`
- [ ] 3.2.3 Iniciar download automaticamente

**Critérios de Aceite:**
- Download funciona em todos os navegadores
- Nome do arquivo correto

#### Task 3.3: Upload/Importação de JSON
**Descrição**: Permitir importar projeto existente.

**Subtarefas:**
- [ ] 3.3.1 Botão "Importar JSON" no header do Studio
- [ ] 3.3.2 Abrir file picker (aceitar .json)
- [ ] 3.3.3 Validar JSON importado
- [ ] 3.3.4 Carregar no estado do Studio
- [ ] 3.3.5 Mostrar erro se JSON inválido

**Critérios de Aceite:**
- Importação carrega corretamente
- Erros de validação exibidos claramente

#### Task 3.4: Persistência Local (LocalStorage)
**Descrição**: Salvar rascunho automaticamente.

**Subtarefas:**
- [ ] 3.4.1 Auto-save a cada 30 segundos no localStorage
- [ ] 3.4.2 Restaurar rascunho ao abrir Studio
- [ ] 3.4.3 Botão "Limpar Rascunho"

**Critérios de Aceite:**
- Rascunho persiste entre sessões
- Não perde trabalho em fechamento acidental

---

### Épico 4: Execução de Workflows

#### Task 4.1: Execução via UI (Debug)
**Descrição**: Rodar workflow pela aba Debug da UI.

**Subtarefas:**
- [ ] 4.1.1 Na aba Debug, carregar projeto do Studio (ou importar JSON)
- [ ] 4.1.2 Campo de input para mensagem inicial
- [ ] 4.1.3 Botão "Executar"
- [ ] 4.1.4 Exibir eventos em tempo real (streaming)
- [ ] 4.1.5 Mostrar output final destacado
- [ ] 4.1.6 Histórico de execuções na sessão

**Critérios de Aceite:**
- Execução funciona com todos os tipos de workflow
- Eventos exibidos em tempo real
- Output final claro

#### Task 4.2: Execução via CLI
**Descrição**: Garantir que `run.py` funcione com JSONs gerados pelo Studio.

**Subtarefas:**
- [ ] 4.2.1 Testar todos os tipos de workflow com JSONs do Studio
- [ ] 4.2.2 Documentar comando: `python run.py exemplos/meu_workflow.json "mensagem"`
- [ ] 4.2.3 Adicionar flag `--verbose` para debug

**Critérios de Aceite:**
- CLI aceita JSONs do Studio sem erros
- Documentação clara

---

### Épico 5: Melhorias de UI/UX

#### Task 5.1: Redesign dos Conectores/Edges
**Descrição**: Melhorar visual das conexões entre nós.

**Subtarefas:**
- [ ] 5.1.1 Trocar conectores quadrados por curvas Bezier suaves
- [ ] 5.1.2 Adicionar animação de "flow" (pulse) durante execução
- [ ] 5.1.3 Cores diferenciadas por tipo de conexão:
  - [ ] Azul: fluxo normal
  - [ ] Verde: condição `true`
  - [ ] Vermelho: condição `false`/default
- [ ] 5.1.4 Setas mais elegantes (SVG customizado)

**Critérios de Aceite:**
- Conectores visualmente suaves
- Animações não impactam performance
- Cores semânticas aplicadas

#### Task 5.2: Redesign dos Nós/Cards
**Descrição**: Melhorar visual dos cards de agentes/steps.

**Subtarefas:**
- [ ] 5.2.1 Bordas arredondadas (border-radius maior)
- [ ] 5.2.2 Ícones por tipo de nó (Agent, Human, Tool)
- [ ] 5.2.3 Badge de status durante execução (idle, running, completed, error)
- [ ] 5.2.4 Tooltip com informações detalhadas ao hover
- [ ] 5.2.5 Tema dark/light consistente

**Critérios de Aceite:**
- Cards visualmente consistentes
- Status claramente visíveis
- Responsivo em diferentes tamanhos

#### Task 5.3: Melhorias de Usabilidade
**Descrição**: Tornar o Studio mais intuitivo.

**Subtarefas:**
- [ ] 5.3.1 Drag-and-drop de agentes da sidebar para o canvas
- [ ] 5.3.2 Atalhos de teclado:
  - [ ] `Ctrl+S`: Salvar/Exportar
  - [ ] `Ctrl+Z`: Undo
  - [ ] `Delete`: Remover item selecionado
- [ ] 5.3.3 Mini-mapa para navegação em workflows grandes
- [ ] 5.3.4 Zoom in/out com scroll do mouse
- [ ] 5.3.5 Snap-to-grid para alinhamento
- [ ] 5.3.6 Auto-layout (organizar nós automaticamente)

**Critérios de Aceite:**
- Drag-and-drop funcional
- Atalhos documentados (tooltip ou help)
- Navegação fluida

#### Task 5.4: Feedback Visual
**Descrição**: Melhorar feedback para ações do usuário.

**Subtarefas:**
- [ ] 5.4.1 Toast notifications para sucesso/erro
- [ ] 5.4.2 Loading states com skeletons
- [ ] 5.4.3 Confirmação antes de deletar (modal ou toast com undo)
- [ ] 5.4.4 Indicador de alterações não salvas (badge no título)

**Critérios de Aceite:**
- Todas as ações têm feedback
- Loading states não bloqueantes
- Usuário sabe quando há alterações pendentes

---

## 📁 Estrutura de Arquivos Sugerida

```
frontend/src/
├── pages/
│   └── platform/
│       ├── agents/
│       │   └── AgentListPage.tsx          # Task 1.1
│       ├── studio/
│       │   └── StudioPage.tsx             # Refatorado
│       └── debug/
│           └── DebugPage.tsx              # Task 4.1
├── components/
│   └── features/
│       └── studio/
│           ├── AgentFormModal.tsx         # Task 1.2
│           ├── ResourcesPanel.tsx         # Task 1.3
│           ├── WorkflowTypeSelector.tsx   # Task 2.1
│           ├── editors/
│           │   ├── SequentialEditor.tsx   # Task 2.2
│           │   ├── ParallelEditor.tsx     # Task 2.3
│           │   ├── GroupChatEditor.tsx    # Task 2.4
│           │   ├── HandoffEditor.tsx      # Task 2.5
│           │   └── RouterEditor.tsx       # Task 2.6
│           ├── nodes/
│           │   ├── AgentNode.tsx          # Task 5.2
│           │   └── StepNode.tsx
│           └── edges/
│               └── SmoothEdge.tsx         # Task 5.1
├── stores/
│   └── studioStore.ts                     # Estado do Studio (Zustand)
├── utils/
│   └── workflowSerializer.ts              # Task 3.1
└── types/
    └── workflow.ts                        # Tipos atualizados
```

---

## ✅ Checklist de Validação Final

Antes de considerar o Agent Studio completo, validar:

- [ ] **Criação de Agente**: Criar agente com todos os campos e salvar
- [ ] **Criação de Workflow**: Criar cada um dos 5 tipos de workflow
- [ ] **Export JSON**: Exportar e verificar que JSON é válido
- [ ] **Import JSON**: Importar JSON exportado e verificar que carrega corretamente
- [ ] **Execução Debug**: Executar workflow pela UI e ver output
- [ ] **Execução CLI**: Executar `python run.py arquivo.json "mensagem"` e ver output
- [ ] **UI/UX**: Verificar que conectores, nós e interações estão suaves
- [ ] **DAG Desabilitado**: Confirmar que opção DAG não aparece e backend rejeita

---

## 📝 Notas Adicionais

### Convenções de Código

- **Frontend**: React + TypeScript, Zustand para estado, Tailwind para estilos
- **Componentes**: Usar shadcn/ui como base
- **Validação**: Zod para schemas
- **Testes**: Jest + React Testing Library (mínimo para componentes críticos)

### Integração com Backend

- **API Base**: `/v1/` (definida em `src/maia_ui/_server.py`)
- **Endpoints usados**:
  - `GET /v1/tools` - Listar ferramentas disponíveis
  - `POST /v1/agents/{id}/run` - Executar agente
  - `POST /v1/workflows/{id}/run` - Executar workflow
  - `GET /v1/entities` - Listar entidades disponíveis

### Priorização

1. **P0**: Tasks 1.1, 1.2, 2.1, 2.2, 3.1, 3.2 (MVP funcional)
2. **P1**: Tasks 2.3-2.6, 3.3, 4.1 (Workflows completos + execução)
3. **P2**: Tasks 1.3, 3.4, 4.2, 5.1-5.4 (Polish e UX)

---

*Este prompt deve ser usado como guia para implementação do Agent Studio. Cada task pode ser atribuída a um agente ou desenvolvedor individualmente.*
