# Implementação de Referências à Base de Conhecimento (Citações)

## Contexto
Atualmente, o componente de chat (`AgentView`, `OpenAIMessageRenderer`) e o backend (`_mapper.py`) não suportam a exibição explícita de referências ou citações de arquivos da base de conhecimento (RAG). Quando um agente utiliza documentos para gerar uma resposta, essas fontes devem ser visíveis para o usuário para garantir transparência e verificabilidade.

## Objetivo
Implementar o suporte ponta-a-ponta para citações de arquivos da base de conhecimento nas conversas com agentes.

## Análise da Situação Atual
1.  **Backend (`src/maia_ui/_mapper.py`)**:
    *   O mapper converte eventos do Agent Framework para o formato OpenAI.
    *   Atualmente, define `annotations=[]` (lista vazia) para `ResponseOutputText`.
    *   Eventos como `HostedFileContent` são mapeados apenas como traces de debug, não como conteúdo visível.
    *   Não há lógica para extrair citações do texto ou de metadados do agente.

2.  **Frontend (`frontend/src/components/features/agent/message-renderers/`)**:
    *   `OpenAIContentRenderer.tsx` renderiza texto usando `MarkdownRenderer`.
    *   `MarkdownRenderer.tsx` suporta markdown padrão, mas não tem tratamento especial para marcadores de citação (ex: `[doc1]`, `[^1]`).
    *   Não há componente visual para listar as fontes utilizadas na resposta.

## Instruções de Implementação

### 1. Backend (Python)
*   **Arquivo**: `src/maia_ui/_mapper.py`
*   **Tarefa**:
    *   Identificar onde as informações de citação estão disponíveis na resposta do Agent Framework (ex: metadados de `TextContent`, campos específicos de RAG, ou `tool_messages` em extensões Azure).
    *   Mapear essas informações para o campo `annotations` do `ResponseOutputText` (conforme especificação OpenAI) ou formatá-las de maneira padronizada no texto.
    *   Se as citações vierem como objetos separados, garantir que sejam convertidas em `annotations` ou em uma lista de referências estruturada.

### 2. Frontend (React/TypeScript)
*   **Arquivo**: `frontend/src/components/features/agent/message-renderers/OpenAIContentRenderer.tsx`
    *   Atualizar `TextContentRenderer` para verificar a presença de `annotations`.
    *   Se houver anotações de citação, renderizá-las visualmente (ex: links interativos, tooltips com nome do arquivo).
    *   Adicionar uma seção "Fontes" ou "Referências" abaixo do texto se houver múltiplas citações.

*   **Arquivo**: `frontend/src/components/ui/markdown-renderer.tsx`
    *   Melhorar o parser para detectar padrões comuns de citação em texto (ex: `[doc1]`, `[source: file.pdf]`) se o backend as injetar diretamente no texto.
    *   Transformar esses padrões em elementos clicáveis.

### 3. Tipagem
*   Garantir que os tipos em `frontend/src/types/openai.ts` (especificamente `Annotation` e `MessageOutputTextContent`) sejam respeitados e utilizados corretamente.

## Resultado Esperado
Quando um usuário fizer uma pergunta que acione a base de conhecimento:
1.  O agente responde com a informação.
2.  A resposta inclui referências visíveis (ex: `[1]`, `[Manual de RH.pdf]`).
3.  O usuário pode identificar claramente quais arquivos foram usados para compor a resposta.
