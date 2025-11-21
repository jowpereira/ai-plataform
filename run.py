from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    os.system("chcp 65001 > nul")

# Adiciona a raiz do projeto ao sys.path para permitir imports de src
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.worker.config import ConfigLoader
from src.worker.engine import WorkflowEngine

app = typer.Typer(add_completion=False, help="Executor genérico para workers do Microsoft Agent Framework.")


def load_all_examples_for_ui():
    """Carrega todos os exemplos da pasta 'exemplos' para o MAIA."""
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


@app.command()
def run(
    config_path: str = typer.Option(
        "exemplos/sequential.json",
        "--config",
        "-c",
        help="Caminho para o arquivo de configuração do worker (Modo CLI)",
    ),
    input_text: str = typer.Option(
        "Londres",
        "--input",
        "-i",
        help="Input inicial para o workflow (Modo CLI)",
    ),
    dev_ui: bool = typer.Option(
        False,
        "--ui",
        "--dev",
        help="Inicia o servidor MAIA com todos os exemplos (Ignora --config e --input)",
    ),
):
    """
    Executa o worker genérico.
    
    Modo CLI (padrão): Executa um workflow específico com input via terminal.
    Modo UI (--ui): Inicia o servidor MAIA para visualização e debug.
    """
    # Carregar variáveis de ambiente
    load_dotenv()

    if dev_ui:
        # --- MODO UI ---
        try:
            # Usando versão local do MAIA (src.maia_ui)
            from src.maia_ui import serve
            print("📦 Usando versão local do MAIA (src.maia_ui)")
        except ImportError as e:
            print(f"❌ Erro ao importar 'src.maia_ui': {e}")
            print("Verifique se a pasta 'src/maia_ui' existe e contém o arquivo '__init__.py'.")
            raise typer.Exit(code=1)

        os.environ["DEVUI_MODE"] = "true"
        print("🚀 Iniciando MAIA com exemplos locais...")
        
        entities = load_all_examples_for_ui()
        
        if not entities:
            print("Nenhuma entidade carregada. Verifique os arquivos em 'exemplos/'.")
            raise typer.Exit(code=1)
        
        print(f"Iniciando servidor com {len(entities)} entidades...")
        for e in entities:
            name = getattr(e, "name", "Unknown")
            print(f" - Entity: {name} (Type: {type(e).__name__})")
            
        serve(entities=entities)
        return

    # --- MODO CLI ---
    # Resolver caminho absoluto
    abs_config_path = os.path.abspath(config_path)
    
    print(f"Carregando configuração de: {abs_config_path}")
    
    try:
        loader = ConfigLoader(abs_config_path)
        config = loader.load()
        print(f"✅ Configuração '{config.name}' carregada com sucesso.")
    except Exception as e:
        print(f"❌ Falha ao carregar configuração: {e}")
        raise typer.Exit(code=1)

    async def _run_async():
        print("⚙️ Inicializando Motor de Workflow...")
        try:
            engine = WorkflowEngine(config)
            
            print(f"🚀 Iniciando execução do workflow com input: '{input_text}'")
            result = await engine.run(initial_input=input_text)
            
            print("\n✅ Execução do Workflow Concluída!")
            print("=" * 30)
            print(f"Resultado: {result}")
            print("=" * 30)
            
        except Exception as e:
            print(f"\n❌ Erro de Execução: {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(code=1)

    asyncio.run(_run_async())


if __name__ == "__main__":
    app()
