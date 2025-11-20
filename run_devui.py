import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao sys.path para permitir imports de src
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.worker.config import ConfigLoader
from src.worker.engine import WorkflowEngine
from agent_framework_devui import serve

def load_examples():
    load_dotenv()
    examples_dir = PROJECT_ROOT / "exemplos"
    entities = []

    if not examples_dir.exists():
        print(f"Diretório de exemplos não encontrado: {examples_dir}")
        return []

    for file_path in examples_dir.glob("*.json"):
        print(f"Carregando exemplo: {file_path.name}")
        try:
            loader = ConfigLoader(str(file_path))
            config = loader.load()
            
            engine = WorkflowEngine(config)
            engine.build()
            
            if engine._workflow:
                entities.append(engine._workflow)
                print(f"✅ Adicionado: {config.name} ({file_path.name})")
            else:
                print(f"⚠️ Falha ao construir workflow para {file_path.name}")
                
        except Exception as e:
            print(f"❌ Erro ao carregar {file_path.name}: {e}")

    return entities

if __name__ == "__main__":
    # Habilita modo DevUI para evitar bloqueios em inputs de console
    os.environ["DEVUI_MODE"] = "true"
    
    print("🚀 Iniciando DevUI com exemplos locais...")
    entities = load_examples()
    
    if not entities:
        print("Nenhuma entidade carregada. Verifique os arquivos em 'exemplos/'.")
    else:
        print(f"Iniciando servidor com {len(entities)} entidades...")
        for e in entities:
            name = getattr(e, "name", "Unknown")
            print(f" - Entity: {name} (Type: {type(e).__name__})")
            
        serve(entities=entities)
