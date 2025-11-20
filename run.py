from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao sys.path para permitir imports de src
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.worker.config import ConfigLoader
from src.worker.engine import WorkflowEngine

app = typer.Typer(add_completion=False, help="Executor genérico para workers do Microsoft Agent Framework.")


@app.command()
def run(
    config_path: str = typer.Option(
        "exemplos/sequential.json",
        "--config",
        "-c",
        help="Caminho para o arquivo de configuração do worker",
    ),
    input_text: str = typer.Option(
        "Londres",
        "--input",
        "-i",
        help="Input inicial para o workflow",
    ),
):
    """
    Executa o worker genérico com a configuração especificada.
    """
    # Carregar variáveis de ambiente
    load_dotenv()

    # Resolver caminho absoluto
    abs_config_path = os.path.abspath(config_path)
    
    print(f"🔄 Carregando configuração de: {abs_config_path}")
    
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
