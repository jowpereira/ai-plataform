# Agentes

Esta pasta contém as definições de agentes individuais criados via UI.

## Estrutura de um Agente

```json
{
  "id": "pesquisador",
  "role": "Pesquisador",
  "description": "Agente especializado em pesquisar informações",
  "model": "gpt-4o-mini",
  "instructions": "Você é um pesquisador especializado...",
  "tools": ["consultar_clima", "resumir_diretrizes"]
}
```

## Campos

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `id` | ✅ | Identificador único do agente |
| `role` | ✅ | Nome/função do agente |
| `description` | ❌ | Descrição para o orquestrador |
| `model` | ✅ | Modelo a ser usado (ex: gpt-4o-mini) |
| `instructions` | ✅ | System prompt do agente |
| `tools` | ❌ | Lista de IDs de ferramentas |

## Uso

Os agentes definidos aqui podem ser referenciados em workflows.
