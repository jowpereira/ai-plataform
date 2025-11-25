# Workflows

Esta pasta contém as definições de workflows criados via UI (Workflow Studio).

## Tipos de Workflow Suportados

### 1. Sequential (Sequencial)
Executa agentes em ordem linear, um após o outro.

### 2. Parallel (Paralelo)
Executa múltiplos agentes simultaneamente (fan-out/fan-in).

### 3. Group Chat
Múltiplos agentes colaboram em chat coordenado por um Manager.

### 4. Handoff
Transições explícitas entre agentes baseadas em condições.

### 5. Router
Um agente roteador decide para qual agente delegar.

## Estrutura de um Workflow

```json
{
  "version": "1.0",
  "name": "meu_workflow",
  "resources": {
    "models": {
      "gpt-4o-mini": { "type": "azure-openai", "deployment": "gpt-4o-mini" }
    },
    "tools": [...]
  },
  "agents": [...],
  "workflow": {
    "type": "sequential",
    "steps": ["agent_1", "agent_2"]
  }
}
```

## Execução

```bash
# Via CLI
uv run python run.py exemplos/workflows/meu_workflow.json

# Via Debug UI
# Acesse a aba Debug no navegador
```
