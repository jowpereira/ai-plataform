# Plano de Desenvolvimento: Maia Studio (Observabilidade & Avaliação)

Este documento define o plano mestre para a evolução do **Maia Studio**, transformando-o em uma plataforma completa de engenharia de IA com foco em observabilidade, experimentação e garantia de qualidade.

## 1. Visão Geral e Objetivos

O objetivo é evoluir o atual `DevServer` (`src/maia_ui`) para suportar três pilares fundamentais:
1.  **Trace Visualization (Deep Dive):** Visualização gráfica, interativa e histórica da execução de workflows, agentes e ferramentas.
2.  **Playground (Iteração Rápida):** Capacidade de "forkar" uma execução passada, editar inputs ou configurações e re-executar para validar correções instantaneamente.
3.  **Datasets & Avaliação (QA Automatizado):** Gestão de casos de teste (Golden Datasets) e execução de baterias de avaliação para garantir a qualidade e segurança das respostas.

---

## 2. Arquitetura Proposta

### 2.1. Camada de Persistência (Novo)
Atualmente, o sistema depende muito de armazenamento em memória ou arquivos JSON simples. Para suportar histórico e datasets, introduziremos um banco de dados leve (SQLite para dev, PostgreSQL para prod).

**Novas Entidades de Dados:**
*   **Run:** Registro de uma execução completa (ID, EntityID, Input, Output, Status, Duration, Timestamp).
*   **TraceSpan:** Eventos detalhados de uma Run (Agent Start, Tool Call, LLM Request), estruturados hierarquicamente.
*   **Dataset:** Coleção lógica de casos de teste (Nome, Descrição, Schema).
*   **TestCase:** Um par Input/ExpectedOutput associado a um Dataset.
*   **Evaluation:** Registro de uma bateria de testes executada (DatasetID, EntityID, Score Global).
*   **EvaluationResult:** Resultado individual de um TestCase (Score, Pass/Fail, Latency, Cost).

### 2.2. API Backend (`src/maia_ui`)
Extensão do servidor FastAPI existente para expor os novos recursos.

*   `GET /v1/history/runs`: Listagem de execuções passadas com filtros.
*   `GET /v1/history/runs/{run_id}/trace`: Árvore completa de eventos para visualização.
*   `POST /v1/playground/rerun`: Re-executar uma run anterior com overrides (inputs/config).
*   `POST /v1/datasets`: CRUD de datasets.
*   `POST /v1/evaluations/run`: Disparar avaliação de um agente contra um dataset.

---

## 3. Plano de Implementação Detalhado

### Fase 1: Persistência de Traces (Fundação)
**Objetivo:** Garantir que toda execução no Worker seja salva e consultável.

1.  **Criar `TraceStore`:**
    *   Implementar interface em `src/maia_ui/_storage.py`.
    *   Usar SQLite (`maia.db`) para armazenar Runs e Spans.
2.  **Integrar com `AgentFrameworkExecutor`:**
    *   No método `execute_entity` e `_execute_workflow`, capturar os eventos emitidos.
    *   Converter `WorkerEvent` e eventos do framework para o formato `TraceSpan`.
    *   Persistir assincronamente ao fim da execução.
3.  **API de Histórico:**
    *   Implementar endpoints de listagem e detalhe de runs.
    *   Garantir que o payload inclua a árvore hierárquica (Workflow -> Step -> Agent -> Tool).

### Fase 2: Playground & "Edit and Rerun"
**Objetivo:** Permitir iteração rápida sobre erros.

1.  **Captura de Configuração (Snapshot):**
    *   Ao salvar uma Run, salvar também o `workflow_config` ou `agent_config` usado.
2.  **Endpoint de Rerun:**
    *   Criar `POST /v1/playground/rerun`.
    *   Recebe: `original_run_id`, `new_input` (opcional), `config_overrides` (opcional).
    *   Lógica: Carrega a config original, aplica overrides, instancia um novo `WorkflowEngine` (ou usa `execute_entity` com config dinâmica) e executa.
    *   Retorna: O ID da nova Run (para que o frontend possa fazer polling do trace).

### Fase 3: Datasets & Gestão de Casos de Teste
**Objetivo:** Criar a "Verdade Absoluta" (Ground Truth) para testes.

1.  **CRUD de Datasets:**
    *   Endpoints para criar/listar/editar Datasets e TestCases.
    *   Suporte a importação de CSV/JSON.
2.  **Feature "Save as Test Case":**
    *   No frontend (Trace View), adicionar botão "Add to Dataset".
    *   Backend recebe o Input e o Output real daquela Run e salva como um novo `TestCase`.

### Fase 4: Motor de Avaliação (Evaluation Engine)
**Objetivo:** Automatizar a verificação de qualidade.

1.  **Avaliadores (Evaluators):**
    *   Implementar classe base `Evaluator`.
    *   **ExactMatchEvaluator:** Compara string exata.
    *   **LLMEvaluator:** Usa um LLM (ex: GPT-4) como juiz para avaliar critérios subjetivos (ex: "A resposta foi polida?", "Contém palavrões?").
2.  **Runner de Avaliação:**
    *   Criar serviço que itera sobre um Dataset.
    *   Para cada TestCase: Executa o Agente/Workflow -> Coleta Output -> Roda Evaluators -> Salva Resultado.
    *   Calcula métricas agregadas (Acurácia, Latência Média).
3.  **Visualização de Resultados:**
    *   API para retornar relatório de avaliação (Matriz de confusão, lista de falhas).

---

## 4. Instruções para o Desenvolvedor (Prompt)

Ao implementar, siga estas diretrizes:

*   **Modularidade:** Mantenha a lógica de persistência separada da lógica de execução (`src/maia_ui/_storage.py` vs `src/maia_ui/_executor.py`).
*   **Performance:** A gravação de traces não deve bloquear a resposta da API. Use `BackgroundTasks` do FastAPI.
*   **Compatibilidade:** O sistema deve funcionar tanto para Agentes simples quanto para Workflows complexos (Magentic, GroupChat).
*   **Schema:** Use Pydantic para definir estritamente os modelos de dados de Run, Trace e Dataset.

## 5. Exemplo de Estrutura de Dados (Trace)

```json
{
  "run_id": "run_12345",
  "entity_id": "agente_vendas",
  "timestamp": "2023-10-27T10:00:00Z",
  "status": "completed",
  "input": {"query": "preço do produto X"},
  "output": {"response": "O preço é R$ 50,00"},
  "trace_tree": [
    {
      "span_id": "span_1",
      "type": "agent_run",
      "name": "Agente Vendas",
      "children": [
        {
          "span_id": "span_2",
          "type": "tool_call",
          "name": "buscar_preco",
          "input": {"produto": "X"},
          "output": "50.00"
        }
      ]
    }
  ]
}
```
