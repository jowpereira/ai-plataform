# Plano de Implementação: Gestão de RAG (Knowledge) no Frontend

## Contexto
O backend do AI Platform foi refatorado para utilizar um padrão de **Providers** para Embeddings e uma configuração centralizada de RAG (`RagConfig`) no `WorkerConfig`. Atualmente, o Frontend não possui interface para configurar ou gerenciar essas bases de conhecimento.

## Objetivo
Implementar uma nova seção **Knowledge** no Frontend, permitindo que o usuário configure visualmente o pipeline RAG (Provider, Embeddings, Estratégia) e gerencie as configurações de recuperação de informação.

## Arquitetura Proposta

### 1. Nova Feature: `Knowledge`
Seguindo o padrão arquitetural do projeto (`src/components/features/*`), criaremos um novo módulo:
- `frontend/src/components/features/knowledge/`
  - `KnowledgeListPage.tsx`: Listagem de configurações de RAG (ou a configuração ativa).
  - `KnowledgeFormModal.tsx`: Formulário para criar/editar a configuração RAG.
  - `KnowledgeCard.tsx`: Componente visual para exibir o resumo da configuração.

### 2. Atualização da API (`api.ts`)
Mapear as interfaces do backend para o frontend:
- Criar interface `RagConfig` (baseada no Pydantic model).
- Criar interface `RagEmbeddingConfig`.
- Adicionar endpoints (mockados inicialmente ou reais se existirem) para `GET /rag` e `POST /rag`.

### 3. Gerenciamento de Estado (Zustand)
- Criar `useKnowledgeStore` para gerenciar o estado da configuração RAG no frontend.

### 4. Integração com a UI Principal
- Adicionar item "Conhecimento" na barra lateral (`PlatformLayout.tsx`).
- Permitir que, ao configurar um Worker/Agente, o usuário visualize qual configuração de RAG está ativa.

## Detalhamento das Tarefas (Prompt para o Agente)

### Passo 1: Definição de Tipos e API
No arquivo `frontend/src/services/api.ts`, adicione as interfaces:

```typescript
export interface RagEmbeddingConfig {
  model: string;
  dimensions?: number;
  normalize: boolean;
}

export interface RagConfig {
  enabled: boolean;
  provider: 'memory' | 'azure_search';
  top_k: number;
  min_score: number;
  strategy: 'last_message' | 'conversation';
  context_prompt: string;
  namespace: string;
  embedding?: RagEmbeddingConfig;
}
```

### Passo 2: Criação da Store
Crie `frontend/src/stores/useKnowledgeStore.ts` seguindo o padrão do `useAgentStore`.

### Passo 3: Componentes de UI
1. **KnowledgeFormModal**:
   - Campos:
     - Toggle `Enabled`.
     - Select `Provider` (Memory, Azure Search).
     - Input `Namespace`.
     - Slider `Top K` (1-50).
     - Slider `Min Score` (0.0-1.0).
     - Select `Strategy` (Last Message, Conversation).
     - Textarea `Context Prompt`.
   - Seção `Embedding` (Condicional se Provider == Memory):
     - Select `Model` (ex: text-embedding-3-small).
     - Checkbox `Normalize`.

2. **KnowledgeListPage**:
   - Exibir a configuração atual em um Card detalhado (já que é uma config global por Worker).
   - Botão de "Editar Configuração" que abre o Modal.

### Passo 4: Navegação
- Atualizar `frontend/src/layouts/PlatformLayout.tsx` para incluir o link para `/platform/knowledge`.
- Atualizar `frontend/src/App.tsx` com a nova rota.

## Prompt de Execução
(Copie e cole este prompt para iniciar a implementação)

```markdown
# Tarefa: Implementar Gestão de RAG (Knowledge) no Frontend

Você deve implementar a interface de gerenciamento de RAG (Retrieval Augmented Generation) no Frontend do AI Platform.
Baseie-se na estrutura existente de `Agents` e `Tools`.

## Arquivos a Criar/Editar:

1.  **`frontend/src/services/api.ts`**:
    - Adicione as interfaces `RagConfig` e `RagEmbeddingConfig`.
    - Adicione funções de serviço `getRagConfig` e `updateRagConfig`.

2.  **`frontend/src/stores/useKnowledgeStore.ts`**:
    - Crie uma store Zustand para gerenciar o estado do RAG.

3.  **`frontend/src/components/features/knowledge/KnowledgeFormModal.tsx`**:
    - Crie um formulário usando `react-hook-form` e `zod` (se aplicável) ou estado local.
    - Mapeie todos os campos do `RagConfig` (src/worker/config.py).
    - Use componentes do `shadcn/ui` (Select, Slider, Switch, Input).

4.  **`frontend/src/pages/platform/knowledge/KnowledgePage.tsx`**:
    - Crie uma página que exibe o status atual do RAG (Ativo/Inativo, Provider, Modelo).
    - Inclua um botão para abrir o `KnowledgeFormModal`.

5.  **`frontend/src/layouts/PlatformLayout.tsx`**:
    - Adicione o item "Conhecimento" (ícone: Book/Database) na sidebar.

## Requisitos Funcionais:
- O formulário deve validar que se `provider == 'memory'`, a configuração de `embedding` é obrigatória.
- Os sliders de `top_k` e `min_score` devem ter limites visuais claros.
- A UI deve ser consistente com o tema atual (Dark/Light mode).

## Contexto Técnico:
- O backend espera a estrutura exata definida em `RagConfig` (Pydantic).
- Utilize os componentes de UI já existentes em `frontend/src/components/ui`.
```
