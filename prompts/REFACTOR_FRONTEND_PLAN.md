# Plano de Refatoração Frontend: Globalização do Header e Unificação Chat/Playground

Este documento descreve o plano detalhado para refatorar o frontend da AI Platform. O objetivo é unificar a experiência de navegação, transformar a página de Debug em um Playground e elevar a qualidade da página de Chat reutilizando componentes robustos já existentes.

## Contexto Atual
- **Header:** O `AppHeader` (com seletor de agentes e settings) existe apenas na `DebugPage`.
- **DebugPage:** Contém lógica complexa de chat, visualização de workflows e painel de debug.
- **ChatPage:** Possui uma implementação simplificada e duplicada de chat (`AssistantChat`) que apresenta erros na renderização de ferramentas e falta funcionalidades.
- **Navegação:** "Debug" está abaixo de "Chat".

## Objetivos
1. **Header Global:** Mover o `AppHeader` para o layout principal (`PlatformLayout`), tornando-o visível em todas as páginas.
2. **Renomeação:** Renomear "Debug" para "Playground" e reposicionar na sidebar.
3. **Upgrade do Chat:** Fazer a página de Chat utilizar a mesma engine robusta do Debug (`AgentView`), corrigindo erros de renderização e garantindo paridade de funcionalidades (exceto visualização de grafos de workflow), mas conseguindo rodar workflow.

---

## Tarefas Detalhadas

### Fase 1: Globalização do AppHeader e Gerenciamento de Estado

O `AppHeader` depende de dados (agentes, workflows) que hoje são carregados pela `DebugPage`. Precisamos elevar esse carregamento para o `PlatformLayout`.

1.  **Refatorar `PlatformLayout.tsx`**:
    -   Adicionar o componente `AppHeader` no topo do layout (acima do `main` ou dentro do container principal, ajustando o layout flex).
    -   Implementar a lógica de inicialização do `devuiStore` (Zustand) dentro do `PlatformLayout`.
        -   Mover o `useEffect` que carrega `apiClient.getMeta()` e `apiClient.getEntities()` da `DebugPage.tsx` para o `PlatformLayout.tsx`.
        -   Garantir que o `AppHeader` receba as props corretas do store (`agents`, `workflows`, `selectedItem`, `onSelect`, etc.).
    -   Remover o título "AI Platform" da Sidebar, já que o Header Global terá a identidade visual.

2.  **Ajustar `DebugPage.tsx`**:
    -   Remover o `AppHeader` da renderização.
    -   Remover a lógica de carregamento inicial de dados (já que o layout fará isso).
    -   Manter apenas a lógica específica da página (gerenciamento de painéis de debug, redimensionamento, etc.).

### Fase 2: Renomeação e Navegação (Debug -> Playground)

1.  **Renomear Arquivos e Rotas**:
    -   Renomear a pasta `src/pages/platform/debug` para `src/pages/platform/playground`.
    -   Renomear `DebugPage.tsx` para `PlaygroundPage.tsx`.
    -   Atualizar a rota em `src/App.tsx`: de `/platform/debug` para `/platform/playground`.

2.  **Atualizar Sidebar (`Sidebar.tsx`)**:
    -   Alterar o link e texto de "Debug Console" para "Playground".
    -   **Reordenar:** Mover o item "Chat" para baixo de "Playground".
    -   Ícone sugerido para Playground: Manter `Bug` ou alterar para `Terminal`/`Play` se fizer mais sentido, mas o foco é a mudança de nome e posição.

### Fase 3: Refatoração da Página de Chat (Paridade de Funcionalidades)

A página de Chat deve ser poderosa, usando a mesma infraestrutura do Playground, mas focada apenas na conversação.

1.  **Refatorar `ChatPage.tsx`**:
    -   Remover o uso de `AssistantChat`.
    -   Utilizar o componente `AgentView` (importado de `src/components/features/agent/agent-view.tsx`).
    -   **Configuração do AgentView no Chat:**
        -   O `AgentView` deve ocupar a tela toda.
        -   Não deve renderizar o painel lateral de Debug (garantir que o store `showDebugPanel` esteja `false` ou que o componente suporte um modo "chat-only").
        -   Se o item selecionado no Header for um **Workflow**, a página de Chat deve exibir o chat do workflow (que o `AgentView` ou `WorkflowView` já suportam), mas **sem** a visualização gráfica do grafo (nodes/edges).
            -   *Nota:* Se o `AgentView` suportar apenas Agentes, verificar se o `WorkflowView` possui um modo "apenas chat". Se não, adaptar ou usar o `AgentView` genérico se a interface de chat for compatível. O objetivo é: Chat funcional para qualquer entidade selecionada.

2.  **Correção de Renderização de Ferramentas**:
    -   Ao usar o `AgentView`, automaticamente passaremos a usar o `OpenAIMessageRenderer` e `ContentPartRenderer`.
    -   Isso resolverá os problemas relatados de "erros nas mensagens de ferramentas", pois o `AgentView` já trata corretamente `function_call`, `tool_calls` e outputs complexos.

3.  **Limpeza**:
    -   Marcar `src/components/features/chat/AssistantChat.tsx` como deprecated ou remover se não for mais usado em lugar nenhum.

### Fase 4: Verificação e Ajustes Finos

1.  **Sincronização de Seleção**:
    -   Garantir que ao selecionar um Agente no Header Global estando na rota `/platform/chat`, a página atualize para o chat desse agente.
    -   Garantir que ao selecionar um Agente no Header Global estando na rota `/platform/playground`, a página atualize para o playground desse agente.

2.  **Persistência de URL**:
    -   Verificar se a query param `?entity_id=...` continua funcionando e sincronizando com o Header Global.

## Resumo Técnico para Execução

- **Arquivos Alvo:**
    - `src/layouts/PlatformLayout.tsx` (Adicionar Header, Init Store)
    - `src/components/layout/Sidebar.tsx` (Reordenar, Renomear)
    - `src/App.tsx` (Rotas)
    - `src/pages/platform/debug/DebugPage.tsx` -> `src/pages/platform/playground/PlaygroundPage.tsx` (Limpar Header/Init)
    - `src/pages/platform/chat/ChatPage.tsx` (Substituir por AgentView)

- **Componentes Chave:**
    - `AppHeader`
    - `AgentView`
    - `useDevUIStore`

---
**Instrução ao Agente:** Siga estas etapas sequencialmente. Comece pela refatoração do Layout para garantir que o Header esteja funcional antes de mexer nas páginas específicas.
