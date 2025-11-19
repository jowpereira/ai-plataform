"""Teste de integração do módulo worker com config existente."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from worker.runtime import GenericWorker, WorkerConfig

# Load .env
load_dotenv()


async def main():
    """Testa worker com configuração existente."""
    # Load config existente
    config_path = Path("scripts/worker_test/config/worker.json")
    if not config_path.exists():
        print(f"❌ Config não encontrada: {config_path}")
        return

    print(f"📄 Carregando config: {config_path}")
    config = WorkerConfig.from_json(config_path)

    print(f"✅ Config carregada: {config.workspace.name}")
    print(f"   - Agents: {len(config.agents)}")
    print(f"   - Tools: {len(config.resources.tools)}")
    print(f"   - Orchestration: {config.orchestration.type}")

    # Create worker
    print("\n🔧 Inicializando worker...")
    worker = GenericWorker(config)
    await worker.initialize()

    print(f"✅ Worker inicializado")
    print(f"   - Workflow factory criada: {worker.workflow_factory is not None}")

    # Test run
    print("\n🚀 Executando workflow...")
    query = "What's the weather in Paris?"

    try:
        async for event in worker.run_stream(query):
            print(f"   � {type(event).__name__}: {event}")

        print("\n✅ Workflow executado com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro na execução: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
