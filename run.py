from __future__ import annotations

import asyncio
import logging
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

from src.worker.config import ConfigLoader, StandaloneAgentConfig, WorkerConfig
from src.worker.engine import WorkflowEngine
from src.worker.runner import AgentRunner

app = typer.Typer(add_completion=False, help="Executor genérico para workers do Microsoft Agent Framework.")


def load_all_examples_for_ui():
    """Carrega todos os exemplos da pasta 'exemplos' para o MAIA."""
    examples_dir = PROJECT_ROOT / "exemplos"
    entities = []

    if not examples_dir.exists():
        print(f"Diretório de exemplos não encontrado: {examples_dir}")
        return []

    # Carregar todos os arquivos JSON da pasta exemplos
    files_to_load = list(examples_dir.glob("*.json"))

    for file_path in files_to_load:
        print(f"Carregando exemplo: {file_path.name}")
        try:
            loader = ConfigLoader(str(file_path))
            config = loader.load()
            
            engine = WorkflowEngine(config)
            engine.build()
            
            if engine._workflow:
                entities.append(engine._workflow)
                
                # 1. Registrar instâncias do workflow (ex: step1, step2)
                # Isso permite debug de nós específicos
                workflow_agents = engine.get_agents()
                # entities.extend(workflow_agents)
                
                # 2. Registrar templates de agentes (ex: weather_agent)
                # Isso permite que o frontend recrie o workflow referenciando os templates
                template_count = 0
                if config.agents:
                    for agent_conf in config.agents:
                        try:
                            # Verificar se já não foi adicionado (evitar duplicatas se ID coincidir)
                            if not any(e.id == agent_conf.id for e in entities):
                                template_agent = engine.agent_factory.create_agent(agent_conf.id)
                                # Garantir ID original
                                template_agent.id = agent_conf.id
                                # Marcar como oculto para não poluir a UI (mas estar disponível para o engine)
                                template_agent._maia_hidden = True
                                entities.append(template_agent)
                                template_count += 1
                        except Exception as e:
                            print(f"⚠️ Aviso: Falha ao criar template '{agent_conf.id}': {e}")

                print(f"✅ Adicionado: {config.name} ({file_path.name}) + {len(workflow_agents)} nós (ocultos) + {template_count} templates (ocultos)")
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
        help="Caminho para o arquivo de configuração (workflow ou agente)",
    ),
    input_text: str = typer.Option(
        "Londres",
        "--input",
        "-i",
        help="Input inicial para o workflow ou agente",
    ),
    dev_ui: bool = typer.Option(
        False,
        "--ui",
        "--dev",
        help="Inicia o servidor MAIA com todos os exemplos (Ignora --config e --input)",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--no-stream",
        help="Usa streaming (ainvoke) ou execução direta (invoke). Streaming mostra respostas de cada agente.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Habilita logging detalhado de eventos do framework",
    ),
):
    """
    Executa o worker genérico.
    
    Modo CLI (padrão): Executa um workflow ou agente específico com input via terminal.
    Modo UI (--ui): Inicia o servidor MAIA para visualização e debug.
    
    Detecção automática:
    - Arquivos com 'workflow' e 'resources' → executados como workflow
    - Arquivos com 'model' e 'instructions' → executados como agente standalone
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurar nível de logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        # Habilitar debug do worker
        logging.getLogger("worker").setLevel(logging.DEBUG)
        print("🔍 Modo DEBUG habilitado")

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
        
        examples_dir = PROJECT_ROOT / "exemplos"
        if not examples_dir.exists():
             print(f"Diretório de exemplos não encontrado: {examples_dir}")
             raise typer.Exit(code=1)

        print(f"Iniciando servidor monitorando: {examples_dir}")
            
        serve(entities_dir=str(examples_dir))
        return

    # --- MODO CLI ---
    # Resolver caminho absoluto
    abs_config_path = os.path.abspath(config_path)
    
    try:
        loader = ConfigLoader(abs_config_path)
        config_type = loader.detect_config_type()
        
        print(f"📄 Tipo detectado: {config_type}")
        
    except Exception as e:
        print(f"❌ Falha ao carregar configuração: {e}")
        raise typer.Exit(code=1)

    async def _run_workflow_async(config: WorkerConfig):
        """Executa workflow via WorkflowEngine."""
        # Configurar reporter visual
        try:
            from src.worker.events import get_event_bus
            from src.worker.reporters.console import ConsoleReporter
            
            bus = get_event_bus()
            reporter = ConsoleReporter()
            bus.subscribe_all(reporter.handle_event)
        except ImportError as e:
            print(f"⚠️ Falha ao carregar reporter visual: {e}")

        try:
            engine = WorkflowEngine(config)
            if stream:
                result = await engine.ainvoke(initial_input=input_text)
            else:
                result = await engine.invoke(initial_input=input_text)
            
        except Exception as e:
            print(f"\n❌ Erro de Execução: {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(code=1)

    async def _run_agent_async(config: StandaloneAgentConfig):
        """Executa agente standalone via AgentRunner."""
        # Configurar reporter visual
        try:
            from src.worker.events import get_event_bus
            from src.worker.reporters.console import ConsoleReporter
            
            bus = get_event_bus()
            reporter = ConsoleReporter()
            bus.subscribe_all(reporter.handle_event)
        except ImportError as e:
            print(f"⚠️ Falha ao carregar reporter visual: {e}")

        try:
            runner = AgentRunner(config)
            result = await runner.run(input_text)
            # Resultado já é exibido pelo ConsoleReporter via AGENT_RUN_COMPLETE
            await runner.teardown()
            
        except Exception as e:
            print(f"\n❌ Erro de Execução: {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(code=1)

    # Executar baseado no tipo detectado
    if config_type == "agent":
        config = loader.load_agent()
        print(f"🤖 Executando agente: {config.id} ({config.role})")
        asyncio.run(_run_agent_async(config))
    else:
        config = loader.load()
        print(f"⚙️ Executando workflow: {config.name}")
        asyncio.run(_run_workflow_async(config))


if __name__ == "__main__":
    app()
