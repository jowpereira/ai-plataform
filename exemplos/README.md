# Exemplos de Workflows

Este diretório contém configurações de exemplo para todos os tipos de workflows suportados pelo worker.

## Como Executar

Use o script `run.py` na raiz do projeto com o comando `uv run`:

```bash
uv run python run.py --config exemplos/<arquivo>.json --input "<seu input>"
```

## Lista de Exemplos

| Arquivo | Tipo | Descrição |
| :--- | :--- | :--- |
| `sequential.json` | **Sequencial** | Fluxo linear: Pesquisador -> Redator. |
| `parallel.json` | **Paralelo** | Executa tarefas simultâneas (Clima e Custos) e agrega os resultados. |
| `router.json` | **Roteador** | Decide qual caminho seguir com base no input (Clima ou Geral). |
| `group_chat.json` | **Group Chat** | Discussão colaborativa entre múltiplos agentes com um gerente. |
| `handoff.json` | **Handoff** | Transferência explícita de responsabilidade entre agentes (Triagem -> Especialistas). |
| `sequential_human.json` | **Sequencial (Human-in-the-loop)** | Inclui uma etapa de validação humana no meio do fluxo sequencial. |

## Estrutura dos Arquivos

Todos os arquivos seguem o schema de configuração definido em `src/worker/config.py`.
As ferramentas utilizadas estão definidas em `ferramentas/basicas.py`.
