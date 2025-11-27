# Debug script para verificar resposta do agente
import asyncio
from src.worker.config import ConfigLoader
from src.worker.runner import AgentRunner
from dotenv import load_dotenv

load_dotenv()

async def test():
    config = ConfigLoader('exemplos/agentes/agente_pesquisador.json').load_agent()
    runner = AgentRunner(config)
    await runner.setup()
    
    resp = await runner._agent.run('Curitiba')
    
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

asyncio.run(test())
