# Debug script para verificar resposta do agente
import asyncio
import sys
from src.worker.config import ConfigLoader
from src.worker.runner import AgentRunner
from dotenv import load_dotenv

load_dotenv()

async def test():
    # Usar argumento de linha de comando ou default
    query = sys.argv[1] if len(sys.argv) > 1 else "quais são as políticas de férias?"
    
    config = ConfigLoader('exemplos/agentes/agente_rh.json').load_agent()
    runner = AgentRunner(config)
    await runner.setup()
    
    resp = await runner._agent.run(query)
    
    print("=== Resposta ===")
    print(f"Messages: {len(resp.messages)}")
    
    # Iterar todas as mensagens
    for i, m in enumerate(resp.messages):
        role = getattr(m, 'role', None)
        print(f"\nMsg {i}: role={role}")
        contents = getattr(m, 'contents', [])
        print(f"  contents count: {len(contents)}")
        for j, c in enumerate(contents):
            ctype = type(c).__name__
            print(f"    [{j}] type={ctype}")
            if ctype == 'TextContent':
                # Imprimir todos os atributos
                for attr in dir(c):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(c, attr)
                            if not callable(val):
                                print(f"        {attr}: {val[:100] if isinstance(val, str) else val}")
                        except:
                            pass
    
    # Verificar se o ContextProvider tem matches
    if hasattr(runner._agent, 'context_providers'):
        print("\n=== RAG Context ===")
        for provider in runner._agent.context_providers:
            if hasattr(provider, 'last_matches'):
                matches = provider.last_matches
                print(f"  Matches: {len(matches)}")
                for match in matches:
                    print(f"    [{match.index}] {match.source}: {match.content[:80]}...")

asyncio.run(test())
