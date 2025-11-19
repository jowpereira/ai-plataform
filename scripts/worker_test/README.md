# Worker de teste com Microsoft Agent Framework

Este laboratório monta um worker 100% configurável via JSON para validar agentes e workflows do Microsoft Agent Framework.

## Componentes

- `config/worker.json`: descreve ferramentas, agentes e o grafo de execução.
- `tools.py`: funções Python que viram ferramentas MCP/Function Calling automaticamente.
- `run_worker.py`: CLI em Typer que carrega as configurações, instancia os agentes e executa o workflow.

## Como executar

1. Garanta que o ambiente uv esteja sincronizado:

   ```powershell
   uv sync --prerelease=allow
   ```

2. Crie/atualize a `.env` com `OPENAI_API_KEY` e `OPENAI_MODEL` (já incluído neste repo).

3. Rode apenas a validação da configuração:

   ```powershell
   uv run python scripts/worker_test/run_worker.py --plan-only
   ```

4. Execute o workflow completo (consome créditos do modelo configurado):

   ```powershell
   uv run python scripts/worker_test/run_worker.py --message "Preciso de um plano de contingência para queda de data center" --stream
   ```

Use `--config` para apontar para outros JSONs e `--stream` para acompanhar os outputs em tempo real.
