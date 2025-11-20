# Exemplos de Workflows

Este diretório contém configurações de exemplo para todos os tipos de workflows suportados pelo worker.

## Como Executar

Use o script `run.py` na raiz do projeto com o comando `uv run`:

```bash
uv run python run.py --config exemplos/<arquivo>.json --input "<seu input>"
```

## Lista de Exemplos

| Arquivo | Tipo | Problema de Negócio | Descrição Técnica | Ferramentas (Mock) |
| :--- | :--- | :--- | :--- | :--- |
| `sequential.json` | **Sequencial** | **Geração de Conteúdo:** Produzir um texto final rico baseado em dados reais. | Fluxo linear: Pesquisador busca dados -> Redator compila. | `consultar_clima`, `resumir_diretrizes` |
| `parallel.json` | **Paralelo** | **Planejamento de Viagem:** Obter visão 360º (clima e custos) simultaneamente para agilizar decisão. | Executa tarefas simultâneas e agrega os resultados. | `consultar_clima`, `calcular_custos` |
| `router.json` | **Roteador** | **Triagem de Atendimento:** Direcionar o cliente para o bot correto para evitar frustração. | Decide caminho (Clima ou Geral) com base na intenção do input. | `consultar_clima` |
| `router_conditional.json` | **Roteador (Condicional)** | **Monitoramento de Infra:** Reagir automaticamente a falhas de sistema sem intervenção humana inicial. | Decide caminho baseado no retorno de uma ferramenta (Online/Offline). | `verificar_status_sistema` |
| `group_chat.json` | **Group Chat** | **Brainstorming:** Explorar tópicos complexos com múltiplas perspectivas. | Discussão colaborativa entre múltiplos agentes com um gerente. | - |
| `handoff.json` | **Handoff** | **Suporte Especializado:** Garantir que dúvidas de cobrança vão para o financeiro e bugs para o técnico. | Transferência explícita de responsabilidade (Triagem -> Especialistas). | - |
| `handoff_complex.json` | **Handoff (State Machine)** | **Gestão de Crise:** Escalar automaticamente tickets que falham na resolução técnica para a gerência. | Fluxo complexo com loops e escalada (Triagem -> Técnico -> QA -> Gerente). | `verificar_resolucao` |
| `sequential_human.json` | **Sequencial (Human-in-the-loop)** | **Compliance:** Garantir que nenhuma pesquisa saia sem aprovação humana. | Inclui uma etapa de validação humana no meio do fluxo. | `consultar_clima` |

## Estrutura dos Arquivos

Todos os arquivos seguem o schema de configuração definido em `src/worker/config.py`.
As ferramentas utilizadas estão definidas em `ferramentas_mock/basicas.py`.
