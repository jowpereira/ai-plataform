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

## Agentes Disponíveis

| Arquivo | Role | Descrição | Ferramentas |
|---------|------|-----------|-------------|
| `agente_pesquisador.json` | Pesquisador | Especialista em pesquisa climática | `consultar_clima` |
| `agente_escritor.json` | Escritor | Cria roteiros e textos | - |
| `agente_analista_fraude.json` | Analista de Fraudes | Detecta padrões fraudulentos | - |
| `agente_suporte_tecnico.json` | Suporte Técnico N1 | Triagem e resolução técnica | `verificar_status_sistema` |
| `agente_extrator_dados.json` | Extrator de Dados | Estrutura dados de documentos | - |
| `agente_auditor.json` | Auditor de Qualidade | Valida conformidade | - |
| `agente_resumidor.json` | Resumidor Executivo | Cria resumos acionáveis | - |

## Uso

Os agentes definidos aqui podem ser referenciados em workflows.
