"""Teste de integração com streaming agregado para UI."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from worker.runtime import GenericWorker, WorkerConfig
from worker.streaming import EventAggregator

# Load .env
load_dotenv()


async def main():
    """Testa worker com streaming agregado."""
    # Load config
    config_path = Path("scripts/worker_test/config/worker.json")
    if not config_path.exists():
        print(f"❌ Config não encontrada: {config_path}")
        return

    print(f"📄 Carregando config: {config_path}")
    config = WorkerConfig.from_json(config_path)

    print(f"✅ Config carregada: {config.workspace.name}")
    print(f"   - Agents: {len(config.agents)}")
    print(f"   - Orchestration: {config.orchestration.type}")

    # Create worker
    print("\n🔧 Inicializando worker...")
    worker = GenericWorker(config)
    await worker.initialize()
    print("✅ Worker inicializado\n")

    # Test com agregador (normal verbosity)
    print("=" * 60)
    print("Teste 1: Verbosity NORMAL (apenas eventos de alto nível)")
    print("=" * 60)
    
    query = "What's the weather in Paris?"
    aggregator = EventAggregator(verbosity="normal")
    
    async for message in aggregator.process_stream(worker.run_stream(query)):
        icon = {"executor_start": "🔄", "executor_complete": "✅", "workflow_output": "📦"}.get(message.event_type, "•")
        executor = f"[{message.executor_id}]" if message.executor_id else ""
        
        if message.is_complete:
            print(f"{icon} {executor} {message.event_type}")
            if message.event_type == "workflow_output":
                print(f"\n{message.content}\n")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído - veja como o output está agregado e limpo!")
    print("=" * 60)
    
    # Exemplo de como usar com diferentes verbosity levels
    print("\n💡 Verbosity levels disponíveis:")
    print("   - minimal: Apenas workflow_output final")
    print("   - normal: executor_start, executor_complete, workflow_output")
    print("   - debug: Todos os eventos incluindo chunks (similar ao anterior)")


if __name__ == "__main__":
    asyncio.run(main())
