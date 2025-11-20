# AI Platform Worker

Este projeto implementa um worker genérico baseado no Microsoft Agent Framework, configurável via arquivos JSON/YAML.

## Funcionalidades

- **Orquestração Flexível**: Suporta fluxos Sequenciais, Paralelos (Concurrent), Router, Group Chat e Handoff.
- **Configuração Declarativa**: Defina agentes, modelos e passos do workflow em um arquivo JSON.
- **Integração com Ferramentas**: Carregamento dinâmico de ferramentas Python.
- **Suporte a Modelos**: OpenAI e Azure OpenAI.

## Estrutura de Configuração

O arquivo de configuração deve seguir o schema definido em `src/worker/config.py`.

### Tipos de Workflow

1. **sequential**: Executa agentes em ordem linear.
2. **parallel**: Executa agentes em paralelo (fan-out/fan-in).
3. **router**: Roteia a execução com base na saída de um agente classificador.
4. **group_chat**: Gerencia uma conversa entre múltiplos agentes com um coordenador (Manager).
5. **handoff**: Permite que agentes transfiram a execução para especialistas específicos.

### Exemplo de Configuração (Group Chat)

```json
{
  "version": "1.0",
  "name": "Exemplo Chat em Grupo",
  "resources": {
    "models": {
      "gpt-4o-mini": { "type": "openai", "deployment": "gpt-4o-mini" }
    }
  },
  "agents": [
    {
      "id": "researcher",
      "role": "Pesquisador",
      "description": "Pesquisa informações detalhadas.",
      "model": "gpt-4o-mini",
      "instructions": "Pesquise sobre o tema solicitado.",
      "tools": []
    },
    {
      "id": "writer",
      "role": "Escritor",
      "description": "Escreve resumos.",
      "model": "gpt-4o-mini",
      "instructions": "Escreva um resumo com base na pesquisa.",
      "tools": []
    }
  ],
  "workflow": {
    "type": "group_chat",
    "steps": [
      { "id": "step1", "type": "agent", "agent": "researcher", "input_template": "{{ input }}" },
      { "id": "step2", "type": "agent", "agent": "writer", "input_template": "Resuma" }
    ]
  }
}
```

### Exemplo de Configuração (Handoff)

```json
{
  "workflow": {
    "type": "handoff",
    "start_step": "triage",
    "steps": [
      {
        "id": "triage",
        "type": "agent",
        "agent": "triage_agent",
        "transitions": ["billing", "tech"]
      },
      { "id": "billing", "type": "agent", "agent": "billing_agent" },
      { "id": "tech", "type": "agent", "agent": "tech_agent" }
    ]
  }
}
```

## Como Executar

Use o script `run_worker.py` via `uv`:

```bash
uv run python scripts/worker_test/run_worker.py --config scripts/worker_test/config/group_chat.json --input "Seu input aqui"
```

## Ferramentas

As ferramentas devem ser definidas em módulos Python (ex: `scripts/worker_test/tools.py`) e referenciadas na configuração:

```json
"tools": [
  {
    "id": "get_weather",
    "path": "scripts.worker_test.tools:get_weather"
  }
]
```
